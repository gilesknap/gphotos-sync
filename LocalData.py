#!/usr/bin/python
# coding: utf8
import os.path
import sqlite3 as lite
from datetime import datetime
import Utils


# NOTES on DB Schema changes
# if adding or removing columns from SyncFiles Table Update:
# (1) GoogleMedia.save_to_db
# (2) LocalData.record_to_tuple
# (3) LocalData.put_file
# (4) DatabaseMedia constructor
# ( add or remove column related properties from GoogleMedia (and subclasses) )


# todo currently store full path in SyncFiles.Path
# would be better as relative path and store root once in this module (runtime)
# this could be refreshed at start for a portable file system folder
# also this would remove the need to pass any paths to the GoogleMedia
# constructors (which is messy)
class LocalData:
    DB_FILE_NAME = 'gphotos.sqlite'
    BLOCK_SIZE = 10000
    EMPTY_FILE_NAME = 'etc/gphotos_empty.sqlite'
    VERSION = "2.0"

    class DuplicateDriveIdException(Exception):
        pass

    def __init__(self, root_folder, flush_index=False):
        self.file_name = os.path.join(root_folder, LocalData.DB_FILE_NAME)
        if not os.path.exists(root_folder):
            os.makedirs(root_folder, 0o700)
        if not os.path.exists(self.file_name) or flush_index:
            clean_db = True
        else:
            clean_db = False
        self.con = lite.connect(self.file_name)
        self.con.row_factory = lite.Row
        self.cur = self.con.cursor()
        if clean_db:
            self.clean_db()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.con:
            self.store()
            self.con.close()

    def clean_db(self):
        sql_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "etc", "gphotos_create.sql")
        qry = open(sql_file, 'r').read()
        self.cur.executescript(qry)

    def set_scan_dates(self, picasa_last_date=None, drive_last_date=None):
        if drive_last_date:
            d = Utils.date_to_string(drive_last_date)
            self.cur.execute('UPDATE Globals SET LastIndexDrive=? '
                             'WHERE Id IS 1', (d,))
        if picasa_last_date:
            d = Utils.date_to_string(picasa_last_date)
            self.cur.execute('UPDATE Globals SET LastIndexPicasa=? '
                             'WHERE Id IS 1', (d,))

    # noinspection PyTypeChecker
    def get_scan_dates(self):
        query = "SELECT LastIndexDrive, LastIndexPicasa " \
                "FROM  Globals WHERE Id IS 1"
        self.cur.execute(query)
        res = self.cur.fetchone()

        drive_last_date = picasa_last_date = None
        d = res['LastIndexDrive']
        p = res['LastIndexPicasa']
        if d:
            drive_last_date = Utils.string_to_date(d)
        if p:
            picasa_last_date = Utils.string_to_date(p)

        return drive_last_date, picasa_last_date

    class SyncRow:
        """
        generates an object with attributes for each of the columns in the
        SyncFiles table
        """
        _sync_rows = [
            'RemoteId', 'Url', 'Path', 'FileName', 'OrigFileName',
            'DuplicateNo', 'MediaType', 'FileSize', 'Checksum', 'Description',
            'ModifyDate', 'CreateDate', 'SyncDate', 'SymLink']
        _sync_types = [
            str, str, str, str, str,
            int, int, int, str, str,
            datetime, datetime, datetime, int]
        sync_query = ','.join(_sync_rows)
        sync_params = ':' + ',:'.join(_sync_rows)

        def __init__(self, result_row=None):
            col_no = 0
            for column in self._sync_rows:
                if not result_row:
                    value = None
                elif self._sync_types[col_no] == datetime:
                    value = Utils.string_to_date(result_row[column])
                else:
                    value = result_row[column]
                setattr(self, column, value)
                col_no += 1

        @property
        def dict(self):
            return self.__dict__

    @classmethod
    def record_to_object(cls, rec):
        """
        :param ([]) rec:
        :return (SyncRow):
        """
        if rec:
            result = cls.SyncRow(rec)
        else:
            result = None
        return result

    def get_files_by_search(self, drive_id='%', media_type=None,
                            start_date=None, end_date=None):
        """
        :param (str) drive_id:
        :param (int) media_type:
        :param (datetime) start_date:
        :param (datetime) end_date:
        :return (SyncRow):
        """
        if not media_type:
            media_type = '%'
        params = (drive_id, media_type)
        date_clauses = ''
        if start_date:
            date_clauses += 'AND ModifyDate >= ?'
            params += (start_date,)
        if end_date:
            date_clauses += 'AND ModifyDate <= ?'
            params += (end_date,)

        query = "SELECT {0} FROM SyncFiles WHERE RemoteId LIKE ? AND " \
                " MediaType LIKE ? {1};".format(self.SyncRow.sync_query,
                                                date_clauses)

        self.cur.execute(query, params)
        while True:
            records = self.cur.fetchmany(LocalData.BLOCK_SIZE)
            if not records:
                break
            for record in records:
                yield self.SyncRow(record)

    def get_file_by_path(self, folder, name):
        """
        :param (str) folder:
        :param (str) name:
        :return (SyncRow):
        """
        query = "SELECT {0} FROM SyncFiles WHERE Path = ?" \
                " AND FileName = ?;".format(self.SyncRow.sync_query)
        self.cur.execute(query, (folder, name))
        record = self.cur.fetchone()
        if record:
            return self.SyncRow(record)
        else:
            return None

    def get_file_by_id(self, remote_id):
        query = "SELECT {0} FROM SyncFiles WHERE RemoteId = ?;".format(
            self.SyncRow.sync_query)
        self.cur.execute(query, (remote_id,))
        record = self.cur.fetchone()
        if record:
            return self.SyncRow(record)
        else:
            return None

    def put_file(self, row):
        query = "INSERT INTO SyncFiles ({0}) VALUES ({1})".format(
            self.SyncRow.sync_query, self.SyncRow.sync_params)
        self.cur.execute(query, row.dict)
        return self.cur.lastrowid

    # noinspection PyTypeChecker
    def find_file_ids_dates(self, filename='%', exif_date='%', size='%',
                            use_create=False):
        if use_create:
            self.cur.execute(
                "SELECT Id, CreateDate FROM SyncFiles WHERE FileName LIKE ? "
                "AND CreateDate LIKE ? AND FileSize LIKE ?;",
                (filename, exif_date, size))
        else:
            self.cur.execute(
                "SELECT Id, CreateDate FROM SyncFiles WHERE FileName LIKE ? "
                "AND "
                "ModifyDate LIKE ? AND FileSize LIKE ?;",
                (filename, exif_date, size))
        res = self.cur.fetchall()

        if len(res) == 0:
            return None
        else:
            keys_dates = [(key['Id'], key['CreateDate']) for key in res]
            return keys_dates

    def put_album(self, album_id, album_name, start_date, end_end=0):
        self.cur.execute(
            "INSERT OR REPLACE INTO Albums(AlbumId, AlbumName, StartDate, "
            "EndDate) VALUES(?,?,?,?) ;",
            (album_id, album_name, start_date, end_end))
        return self.cur.lastrowid

    def get_album_files(self, album_id='%'):
        self.cur.execute(
            "SELECT SyncFiles.Path, SyncFiles.Filename, Albums.AlbumName, "
            "Albums.EndDate FROM AlbumFiles "
            "INNER JOIN SyncFiles ON AlbumFiles.DriveRec=SyncFiles.Id "
            "INNER JOIN Albums ON AlbumFiles.AlbumRec=Albums.AlbumId "
            "WHERE Albums.AlbumId LIKE ?;",
            (album_id,))
        results = self.cur.fetchall()
        for result in results:
            yield tuple(result)

    def put_album_file(self, album_rec, file_rec):
        self.cur.execute(
            "INSERT OR REPLACE INTO AlbumFiles(AlbumRec, DriveRec) VALUES(?,"
            "?) ;",
            (album_rec, file_rec))

    # noinspection PyTypeChecker
    def get_drive_folder_path(self, folder_id):
        self.cur.execute(
            "SELECT Path FROM DriveFolders "
            "WHERE FolderId IS ?", (folder_id,))
        result = self.cur.fetchone()
        if result:
            return result['Path']
        else:
            return None

    def put_drive_folder(self, drive_id, parent_id, date):
        self.cur.execute(
            "INSERT OR REPLACE INTO "
            "DriveFolders(FolderId, ParentId, FolderName)"
            " VALUES(?,?,?) ;", (drive_id, parent_id, date))

    # noinspection PyTypeChecker
    def update_drive_folder_path(self, path, parent_id):
        self.cur.execute(
            "UPDATE DriveFolders SET Path = ? WHERE ParentId = ?;",
            (path, parent_id))
        self.cur.fetchall()

        self.cur.execute(
            "SELECT FolderId, FolderName FROM DriveFolders WHERE ParentId = ?;",
            (parent_id,))

        results = self.cur.fetchall()
        for result in results:
            yield (result['FolderId'], result['FolderName'])

    def store(self):
        print("\nSaving Database ...")
        self.con.commit()
        print("Database Saved.\n")

    # todo - keeping origFileName and FileName is bobbins
    # we only need original filename and duplicate number to determine
    # what the local filename is so that is how it should be
    # this refactor should be combined with making paths stored in db relative
    def file_duplicate_no(self, file_id, path, name):
        self.cur.execute(
            "SELECT DuplicateNo FROM SyncFiles WHERE RemoteId = ?;", (file_id,))
        results = self.cur.fetchone()

        if results:
            # return the existing file entry's duplicate no.
            return results[0]

        self.cur.execute(
            "SELECT MAX(DuplicateNo) FROM SyncFiles "
            "WHERE Path = ? AND OrigFileName = ?;", (path, name))
        results = self.cur.fetchone()
        if results[0] is not None:
            # assign the next available duplicate no.
            dup = results[0] + 1
            return dup
        else:
            # the file is new and has no duplicates
            return 0
