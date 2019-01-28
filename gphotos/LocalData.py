#!/usr/bin/env python3
# coding: utf8
import os.path
import sqlite3 as lite
from datetime import datetime

from gphotos import Utils
from gphotos.DbRow import DbRow
import logging

log = logging.getLogger(__name__)


class LocalData:
    DB_FILE_NAME = 'gphotos.sqlite'
    BLOCK_SIZE = 10000
    EMPTY_FILE_NAME = 'etc/gphotos_empty.sqlite'
    # this must match 'INSERT INTO Globals' in gphotos_create.sql
    VERSION = 4.1

    class DuplicateDriveIdException(Exception):
        pass

    def __init__(self, root_folder, flush_index=False):
        self.file_name = os.path.join(root_folder, LocalData.DB_FILE_NAME)
        if not os.path.exists(self.file_name) or flush_index:
            clean_db = True
        else:
            clean_db = False
        self.con = lite.connect(self.file_name, check_same_thread=False)
        self.con.row_factory = lite.Row
        self.cur = self.con.cursor()
        # second cursor for iterator functions so they can interleave with
        # others
        self.cur2 = self.con.cursor()
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
    @DbRow.db_row
    class SyncRow(DbRow):
        """
        generates an object with attributes for each of the columns in the
        SyncFiles table
        """
        cols_def = {'Id': int, 'RemoteId': str, 'Url': str, 'Path': str,
                    'FileName': str, 'OrigFileName': str, 'DuplicateNo': int,
                    'FileSize': int, 'MimeType': str, 'Description': str,
                    'ModifyDate': datetime, 'CreateDate': datetime,
                    'SyncDate': datetime, 'Downloaded': int}
        no_update = ['Id']

    # noinspection PyClassHasNoInit
    @DbRow.db_row
    class AlbumsRow(DbRow):
        """
        generates an object with attributes for each of the columns in the
        SyncFiles table
        """
        cols_def = {'AlbumId': str, 'AlbumName': str, 'Size': int,
                    'StartDate': datetime,
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
        with open(sql_file, 'r') as f:
            qry = f.read()
            self.cur.executescript(qry)

    def set_scan_date(self, last_date):
        d = Utils.date_to_string(last_date)
        self.cur.execute('UPDATE Globals SET LastIndex=? '
                         'WHERE Id IS 1', (d,))

    def get_scan_date(self):
        query = "SELECT LastIndex " \
                "FROM  Globals WHERE Id IS 1"
        self.cur.execute(query)
        res = self.cur.fetchone()

        # noinspection PyTypeChecker
        d = res['LastIndex']
        if d:
            last_date = Utils.string_to_date(d)
        else:
            last_date = None

        return last_date

    def get_files_by_search(self, remote_id='%',
                            start_date=None, end_date=None,
                            skip_downloaded=False):
        """
        :param (str) remote_id:
        :param (datetime) start_date:
        :param (datetime) end_date:
        :param (bool) skip_downloaded: Dont return entries already downloaded
        :return (self.SyncRow):
        """
        params = (remote_id,)
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
        if skip_downloaded:
            extra_clauses += 'AND Downloaded IS 0'

        query = "SELECT {0} FROM SyncFiles WHERE RemoteId LIKE ? {1};". \
            format(self.SyncRow.columns, extra_clauses)

        self.cur2.execute(query, params)
        while True:
            records = self.cur2.fetchmany(LocalData.BLOCK_SIZE)
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

    def put_file(self, row, update=False):
        try:
            if update:
                query = "UPDATE SyncFiles Set {0} " \
                        "WHERE RemoteId = '{1}'".format(self.SyncRow.update,
                                                        row.RemoteId)
            else:
                query = "INSERT INTO SyncFiles ({0}) VALUES ({1})".format(
                    self.SyncRow.columns, self.SyncRow.params)
            self.cur.execute(query, row.dict)
            row_id = self.cur.lastrowid
        except lite.IntegrityError:
            log.error('SQL constraint issue with {}'.format(row.dict))
            raise
        return row_id

    def file_duplicate_no(self, name, path, remote_id):
        """
        determine if there is already an entry for file. If not determine
        if other entries share the same path/filename and determine a duplicate
        number for providing a unique local filename suffix

        :param (str) name:
        :param (str) path:
        :param (str) remote_id:
        :return (int, SyncRow): the next available duplicate number or 0 if
        file is unique
        """
        query = "SELECT {0} FROM SyncFiles WHERE RemoteId = ?; ". \
            format(self.SyncRow.columns)
        self.cur.execute(query, (remote_id,))
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
            "INNER JOIN SyncFiles ON AlbumFiles.DriveRec=SyncFiles.RemoteId "
            "INNER JOIN Albums ON AlbumFiles.AlbumRec=Albums.AlbumId "
            "WHERE Albums.AlbumId LIKE ?;",
            (album_id,))
        results = self.cur.fetchall()
        # fetchall does not need to use cur2
        for result in results:
            yield tuple(result)

    def put_album_file(self, album_rec, file_rec):
        self.cur.execute(
            "INSERT OR REPLACE INTO AlbumFiles(AlbumRec, DriveRec) "
            "VALUES(?,"
            "?) ;",
            (album_rec, file_rec))

    def remove_all_album_files(self):
        # noinspection SqlWithoutWhere
        self.cur.execute("DELETE FROM AlbumFiles")

    def put_downloaded(self, sync_file_id, downloaded=True):
        self.cur.execute(
            "UPDATE SyncFiles SET Downloaded=? "
            "WHERE RemoteId IS ?;", (downloaded, sync_file_id))

    def downloaded_count(self, downloaded=True):
        self.cur.execute(
            "Select Count(Downloaded) from main.SyncFiles WHERE Downloaded=? ",
            (downloaded,))
        result = self.cur.fetchone()[0]
        return result

    def store(self):
        log.info("Saving Database ...")
        self.con.commit()
        log.info("Database Saved.")
