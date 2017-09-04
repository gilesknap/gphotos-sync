#!/usr/bin/python
# coding: utf8
import os.path
import sqlite3 as lite
import shutil

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
    VERSION = "1.4"

    class DuplicateDriveIdException(Exception):
        pass

    def __init__(self, root_folder, flush_index=False):
        self.file_name = os.path.join(root_folder, LocalData.DB_FILE_NAME)
        if not os.path.exists(root_folder):
            os.mkdir(root_folder, 0o700)
        if not os.path.exists(self.file_name) or flush_index:
            self.setup_new_db()
        self.con = lite.connect(self.file_name)
        self.con.row_factory = lite.Row
        self.cur = self.con.cursor()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.con:
            self.store()
            self.con.close()

    def setup_new_db(self):
        # todo should just run gphotos_empty.sqlite
        print("creating new database")
        src_folder = os.path.dirname(os.path.abspath(__file__))
        from_file = os.path.join(src_folder, LocalData.EMPTY_FILE_NAME)
        shutil.copy(from_file, self.file_name)

    @classmethod
    def record_to_tuple(cls, rec):
        if rec:
            data_tuple = (
                rec['RemoteId'], rec['Url'], rec['Path'], rec['FileName'],
                rec['OrigFileName'], rec['DuplicateNo'], rec['ModifyDate'],
                rec['Checksum'], rec['Description'], rec['FileSize'],
                rec['CreateDate'], rec['SyncDate'], rec['MediaType'],
                rec['SymLink']
            )
        else:
            data_tuple = None
        return data_tuple

    def get_files_by_search(self, drive_id='%', media_type='%',
                            start_date=None, end_date=None):
        params = (drive_id, int(media_type))
        date_clauses = ''
        if start_date:
            date_clauses += 'AND ModifyDate >= ?'
            params += (start_date,)
        if end_date:
            date_clauses += 'AND ModifyDate <= ?'
            params += (end_date,)

        query = "SELECT * FROM SyncFiles WHERE RemoteId LIKE ? AND " \
                " MediaType LIKE ? {0};".format(date_clauses)

        self.cur.execute(query, params)
        while True:
            records = self.cur.fetchmany(LocalData.BLOCK_SIZE)
            if not records:
                break
            for record in records:
                yield (self.record_to_tuple(record))

    def get_file_by_path(self, local_full_path):
        path = os.path.dirname(local_full_path)
        name = os.path.basename(local_full_path)
        self.cur.execute(
            "SELECT * FROM SyncFiles WHERE Path = ? AND FileName = ?;",
            (path, name))
        result = self.record_to_tuple(self.cur.fetchone())
        return result

    def get_file_by_id(self, remote_id):
        self.cur.execute(
            "SELECT * FROM SyncFiles WHERE RemoteId = ?;", (remote_id,))
        result = self.record_to_tuple(self.cur.fetchone())
        return result

    def put_file(self, data_tuple):
        # note this will overwrite existing entries with new data which fine
        # but we hide the possibility of > 1 reference to a single file from
        # > 1 Drive folders - again OK since it does represent the same file
        # However we will only see the last reference in our local sync of
        # the drive folders (this does not affect Google Photos sub-folders)
        self.cur.execute(
            "INSERT INTO SyncFiles "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ;",
            (None,) + data_tuple)
        return self.cur.lastrowid

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

    def get_album(self, table_id):
        self.cur.execute(
            "SELECT * FROM Albums WHERE Id = ?",
            (table_id,))
        results = self.cur.fetchone()
        for result in results:
            yield (result['AlbumId'], result['AlbumName'],
                   result['StartDate'], result['EndDate'])

    def put_album(self, album_id, album_name, start_date, end_end=0):
        self.cur.execute(
            "INSERT OR REPLACE INTO Albums(AlbumId, AlbumName, StartDate, "
            "EndDate) VALUES(?,?,?,?) ;",
            (album_id, unicode(album_name, 'utf8'), start_date, end_end))
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

    def get_drive_folder_path(self, folder_id):
        self.cur.execute(
            "SELECT Path FROM DriveFolders "
            "WHERE FolderId is ?", (folder_id,))
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
