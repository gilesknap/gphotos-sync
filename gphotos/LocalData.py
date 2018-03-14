#!/usr/bin/env python2
# coding: utf8
import os.path
import sqlite3 as lite
from datetime import datetime

import Utils
import logging

log = logging.getLogger('gphotos.data')


# noinspection PyClassHasNoInit
class DbRow:
    """
    base class for classes representing a row in the database to allow easy
    generation of queries and an easy interface for callers e.g.
        q = "INSERT INTO SyncFiles ({0}) VALUES ({1})".format(
            self.SyncRow.query, self.SyncRow.params)
        self.cur.execute(query, row.dict)
    Attributes:
        (dict) cols_def: keys are names of columns and items are their type
        (str) query: a string to insert after a SELECT or INSERT INTO {db}
        (str) params: a string to insert after VALUES in a sql INSERT or UPDATE
        The remaining attributes are on a per subclass basis and are
        generated from row_def by the db_row decorator
    """
    cols_def = None
    no_update = []
    columns = None
    params = None
    dict = None
    empty = False

    # allows us to do boolean checks on the row object and return True i
    def __nonzero__(self):
        return not self.empty

    # factory method for delivering a DbRow object based on named arguments
    @classmethod
    def make(cls, **k_args):
        new_row = cls()
        for key, value in k_args.items():
            if not hasattr(new_row, key):
                raise ValueError("{0} does not have column {1}".format(
                    cls, key))
            setattr(new_row, key, value)
        new_row.empty = False
        return new_row


def db_row(row_class):
    """
    class decorator function to create RowClass classes that represent a row
    in the database

    :param (DbRow) row_class: the class to decorate
    :return (DbRow): the decorated class
    """
    row_class.columns = ','.join(row_class.cols_def.keys())
    row_class.params = ':' + ',:'.join(row_class.cols_def.keys())
    row_class.update = ','.join('{0}=:{0}'.format(col) for
                                col in row_class.cols_def.keys() if
                                col not in row_class.no_update)

    def init(self, result_row=None):
        for col, col_type in self.cols_def.items():
            if not result_row:
                value = None
            elif col_type == datetime:
                value = Utils.string_to_date(result_row[col])
            else:
                value = result_row[col]
            setattr(self, col, value)
            if not result_row:
                self.empty = True

    @property
    def to_dict(self):
        return self.__dict__

    row_class.__init__ = init
    row_class.dict = to_dict
    return row_class


# todo currently store full path in SyncFiles.Path
# would be better as relative path and store root once in this module (runtime)
# this could be refreshed at start for a portable file system folder
# also this would remove the need to pass any paths to the GoogleMedia
# constructors (which is messy)
class LocalData:
    DB_FILE_NAME = 'gphotos.sqlite'
    BLOCK_SIZE = 10000
    EMPTY_FILE_NAME = 'etc/gphotos_empty.sqlite'
    VERSION = 2.3

    class DuplicateDriveIdException(Exception):
        pass

    def __init__(self, root_folder, flush_index=False):
        self.file_name = os.path.join(root_folder, LocalData.DB_FILE_NAME)
        if not os.path.exists(self.file_name) or flush_index:
            clean_db = True
        else:
            clean_db = False
        self.con = lite.connect(self.file_name)
        self.con.row_factory = lite.Row
        self.cur = self.con.cursor()
        if clean_db:
            self.clean_db()
        self.check_schema_version()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.con:
            self.store()
            self.con.close()

    # noinspection PyClassHasNoInit
    @db_row
    class SyncRow(DbRow):
        """
        generates an object with attributes for each of the columns in the
        SyncFiles table
        """
        cols_def = {'Id': int, 'RemoteId': str, 'Url': str, 'Path': str,
                    'FileName': str, 'OrigFileName': str, 'DuplicateNo': int,
                    'MediaType': int, 'FileSize': int, 'Checksum': str,
                    'Description': str, 'ModifyDate': datetime,
                    'CreateDate': datetime, 'SyncDate': datetime,
                    'SymLink': int}
        no_update = ['Id']

    # noinspection PyClassHasNoInit
    @db_row
    class AlbumsRow(DbRow):
        """
        generates an object with attributes for each of the columns in the
        SyncFiles table
        """
        cols_def = {'AlbumId': str, 'AlbumName': str, 'StartDate': datetime,
                    'EndDate': datetime, 'SyncDate': datetime}

    def check_schema_version(self):
        query = "SELECT  Version FROM  Globals WHERE Id IS 1"
        self.cur.execute(query)
        version = float(self.cur.fetchone()[0])
        if version > self.VERSION:
            raise ValueError('Database version is newer than gphotos-sync')
        elif version < self.VERSION:
            log.warning('Database schema out of date. Flushing index ...')
            self.con.commit()
            self.con.close()
            os.rename(self.file_name, self.file_name + '.previous')
            self.con = lite.connect(self.file_name)
            self.con.row_factory = lite.Row
            self.cur = self.con.cursor()
            self.clean_db()

    def clean_db(self):
        sql_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "sql", "gphotos_create.sql")
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

    def get_scan_dates(self):
        query = "SELECT LastIndexDrive, LastIndexPicasa " \
                "FROM  Globals WHERE Id IS 1"
        self.cur.execute(query)
        res = self.cur.fetchone()

        drive_last_date = picasa_last_date = None
        # noinspection PyTypeChecker
        d = res['LastIndexDrive']
        # noinspection PyTypeChecker
        p = res['LastIndexPicasa']
        if d:
            drive_last_date = Utils.string_to_date(d)
        if p:
            picasa_last_date = Utils.string_to_date(p)

        return drive_last_date, picasa_last_date

    def get_files_by_search(self, drive_id='%', media_type='%',
                            start_date=None, end_date=None, skip_linked=False):
        """
        :param (str) drive_id:
        :param (int) media_type:
        :param (datetime) start_date:
        :param (datetime) end_date:
        :param (bool) skip_linked: Don't return entries with non-null SymLink
        :return (self.SyncRow):
        """
        params = (drive_id, media_type)
        extra_clauses = ''
        if start_date:
            # look for create date too since an photo recently uploaded will
            # keep its original modified date (since that is in the exif)
            # this clause is specifically to assist in incremental download
            extra_clauses += 'AND (ModifyDate >= ? OR CreateDate >= ?)'
            params += (start_date, start_date)
        if end_date:
            extra_clauses += 'AND ModifyDate <= ?'
            params += (end_date,)
        if skip_linked:
            extra_clauses += 'AND SymLink IS NULL'

        query = "SELECT {0} FROM SyncFiles WHERE RemoteId LIKE ? AND  " \
                "MediaType LIKE ? {1};". \
            format(self.SyncRow.columns, extra_clauses)

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
        :return (self.SyncRow):
        """
        query = "SELECT {0} FROM SyncFiles WHERE Path = ?" \
                " AND FileName = ?;".format(self.SyncRow.columns)
        self.cur.execute(query, (folder, name))
        record = self.cur.fetchone()
        return self.SyncRow(record)

    def get_file_by_id(self, remote_id):
        query = "SELECT {0} FROM SyncFiles WHERE RemoteId = ?;".format(
            self.SyncRow.columns)
        self.cur.execute(query, (remote_id,))
        record = self.cur.fetchone()
        return self.SyncRow(record)

    def put_file(self, row, update=False):
        if update:
            query = "UPDATE SyncFiles Set {0} WHERE RemoteId = '{1}'".format(
                self.SyncRow.update, row.RemoteId)
        else:
            query = "INSERT INTO SyncFiles ({0}) VALUES ({1})".format(
                self.SyncRow.columns, self.SyncRow.params)
        self.cur.execute(query, row.dict)
        row_id = self.cur.lastrowid
        return row_id

    def file_duplicate_no(self, create_date, name, size, path, media_type,
                          remote_id):
        """
        determine if there is already an entry for file. If not determine
        if other entries share the same path/filename and determine a duplicate
        number for providing a unique local filename suffix

        :param (datetime) create_date:
        :param (str) name:
        :param (int) size:
        :param (str) path:
        :param (MediaType) media_type:
        :param (str) remote_id:
        :return (int, SyncRow): the next available duplicate number or 0 if
        file is unique
        """
        query = "SELECT {0} FROM SyncFiles WHERE (CreateDate= ? AND " \
                "FileSize = ? AND FileName = ? AND MediaType = ?) " \
                "OR RemoteId = ?;". \
            format(self.SyncRow.columns)
        self.cur.execute(query,
                         (create_date, size, name, media_type, remote_id))
        result = self.cur.fetchone()

        if result:
            # return the existing file entry's duplicate no.
            # noinspection PyTypeChecker
            return result['DuplicateNo'], self.SyncRow(result)

        self.cur.execute(
            "SELECT MAX(DuplicateNo) FROM SyncFiles "
            "WHERE Path = ? AND OrigFileName = ?;", (path, name))
        results = self.cur.fetchone()
        if results[0] is not None:
            # assign the next available duplicate no.
            dup = results[0] + 1
            return dup, None
        else:
            # the file is new and has no duplicates
            return 0, None

    def find_file_ids_dates(self, filename='%', exif_date='%', size='%',
                            media_type='%', use_create=False):
        if use_create:
            query = "SELECT {0} FROM SyncFiles WHERE FileName LIKE ? AND " \
                    "CreateDate LIKE ? AND FileSize LIKE ? " \
                    "AND MediaType LIKE ?;" \
                .format(self.SyncRow.columns)
            self.cur.execute(query, (filename, exif_date, size, media_type))
        else:
            query = "SELECT {0} FROM SyncFiles WHERE FileName LIKE ? AND " \
                    "ModifyDate LIKE ? AND FileSize LIKE ? " \
                    "AND MediaType LIKE ?;" \
                .format(self.SyncRow.columns)
            self.cur.execute(query, (filename, exif_date, size, media_type))
        res = self.cur.fetchall()
        results = []
        for row in res:
            results.append(self.SyncRow(row))
        return results

    def get_album(self, album_id):
        query = "SELECT {0} FROM Albums WHERE AlbumId = ?;".format(
            self.AlbumsRow.columns)
        self.cur.execute(query, (album_id,))
        res = self.cur.fetchone()
        return self.AlbumsRow(res)

    def put_album(self, row):
        query = "INSERT OR REPLACE INTO Albums ({0}) VALUES ({1}) ;".format(
            row.columns, row.params)
        self.cur.execute(query, row.dict)
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
            "INSERT OR REPLACE INTO AlbumFiles(AlbumRec, DriveRec) "
            "VALUES(?,"
            "?) ;",
            (album_rec, file_rec))

    def remove_all_album_files(self):
        self.cur.execute("DELETE FROM AlbumFiles")

    def get_drive_folder_path(self, folder_id):
        self.cur.execute(
            "SELECT Path FROM DriveFolders "
            "WHERE FolderId IS ?", (folder_id,))
        result = self.cur.fetchone()
        if result:
            # noinspection PyTypeChecker
            return result['Path']
        else:
            return None

    def put_drive_folder(self, drive_id, parent_id, folder_name):
        self.cur.execute(
            "INSERT OR REPLACE INTO "
            "DriveFolders(FolderId, ParentId, FolderName)"
            " VALUES(?,?,?) ;", (drive_id, parent_id, folder_name))

    def put_symlink(self, sync_file_id, link_id):
        self.cur.execute(
            "UPDATE SyncFiles SET SymLink=? "
            "WHERE Id IS ?;", (link_id, sync_file_id))

    def update_drive_folder_path(self, path, parent_id):
        self.cur.execute(
            "UPDATE DriveFolders SET Path = ? WHERE ParentId = ?;",
            (path, parent_id))
        self.cur.fetchall()

        self.cur.execute(
            "SELECT FolderId, FolderName FROM DriveFolders WHERE ParentId "
            "= ?;",
            (parent_id,))

        results = self.cur.fetchall()
        for result in results:
            # noinspection PyTypeChecker
            yield (result['FolderId'], result['FolderName'])

    def store(self):
        log.info("Saving Database ...")
        self.con.commit()
        log.info("Database Saved.")
