#!/usr/bin/env python3
# coding: utf8
from pathlib import Path
import platform
from os.path import normcase  # (cannot see how to do this in pathlib)
import sqlite3 as lite
from sqlite3.dbapi2 import Connection, Row, Cursor
from datetime import datetime
from typing import Iterator, Type

# todo this module could be tidied quite a bit
#  too much application logic at this level in some cases
#  also the generic functions seem a bit ugly and could do with rework
import gphotos.Queries as Queries
from gphotos import Utils
from gphotos.GoogleAlbumsRow import GoogleAlbumsRow
from gphotos.LocalFilesRow import LocalFilesRow
from gphotos.GooglePhotosRow import GooglePhotosRow
from gphotos.DbRow import DbRow
from gphotos.DatabaseMedia import DatabaseMedia

import logging

log = logging.getLogger(__name__)


class LocalData:
    DB_FILE_NAME: str = 'gphotos.sqlite'
    BLOCK_SIZE: int = 10000
    VERSION: float = 5.6

    def __init__(self, root_folder: Path, flush_index: bool = False):
        """ Initialize a connection to the DB and create some cursors.
        If requested or if the DB schema version is old, recreate the DB
        from scratch.
        """
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            self.case_insensitive = True
        else:
            self.case_insensitive = False

        clean_db = False
        self.db_file: Path = root_folder / LocalData.DB_FILE_NAME
        if not self.db_file.exists():
            clean_db = True
        elif flush_index:
            clean_db = True
            self.db_file.rename(self.db_file.parent /
                                (self.db_file.name + '.previous'))

        self.con: Connection = lite.connect(str(self.db_file),
                                            check_same_thread=False)
        self.con.row_factory = lite.Row
        self.cur: Cursor = self.con.cursor()
        # second cursor for iterator functions so they can interleave with
        # others
        self.cur2: Cursor = self.con.cursor()
        if clean_db:
            self.clean_db()
        self.check_schema_version()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Always clean up and close the connection when this object is
        destroyed. """
        if self.con:
            self.store()
            self.con.close()

    def store(self):
        log.info("Saving Database ...")
        self.con.commit()
        log.info("Database Saved.")

    def check_schema_version(self):
        query = "SELECT  Version FROM  Globals WHERE Id IS 1"
        self.cur.execute(query)
        version = float(self.cur.fetchone()[0])
        if version > self.VERSION:
            raise ValueError('Database version is newer than gphotos-sync')
        elif version < self.VERSION:
            log.warning('Database schema out of date. Flushing index ...\n'
                        'A backup of the previous DB has been created')
            self.con.commit()
            self.con.close()
            self.db_file.rename(self.db_file.parent /
                                (self.db_file.name + '.previous'))
            self.con = lite.connect(str(self.db_file))
            self.con.row_factory = lite.Row
            self.cur = self.con.cursor()
            self.clean_db()

    def clean_db(self):
        """ Execute the DB creation script, erasing old data and bringing
        the schema up to date if necessary """
        sql_file = Path(__file__).absolute().parent
        sql_file = sql_file / "sql" / "gphotos_create.sql"

        with sql_file.open('r') as f:
            qry = f.read()
            self.cur.executescript(qry)
        self.store()
        self.cur.execute('INSERT INTO Globals(Id, Version, Albums, Files) '
                         'VALUES(1, ?, 0, 0);',
                         (self.VERSION,))
        self.store()

    # functions to set global values ##########################################
    def set_scan_date(self, last_date: datetime):
        d = Utils.date_to_string(last_date)
        self.cur.execute('UPDATE Globals SET LastIndex=? '
                         'WHERE Id IS 1', (d,))

    def get_scan_date(self) -> datetime:
        query = "SELECT LastIndex " \
                "FROM  Globals WHERE Id IS 1"
        self.cur.execute(query)
        res = self.cur.fetchone()

        d = res['LastIndex']
        if d:
            last_date = Utils.string_to_date(d)
        else:
            last_date = None

        return last_date

    # functions for managing the (any) Media Tables ###########################
    # noinspection SqlResolve
    def put_row(self, row: DbRow, update=False, album=False):
        try:
            if update:
                if album:
                    # noinspection PyUnresolvedReferences
                    query = "UPDATE {0} Set {1} WHERE RemoteId = '{2}'".format(
                        row.table, row.update, row.RemoteId)
                else:
                    # noinspection PyUnresolvedReferences
                    query = "UPDATE {0} Set {1} WHERE RemoteId = '{2}'".format(
                        row.table, row.update, row.RemoteId)
            else:
                # EXISTS - allows for no action when trying to re-insert
                # noinspection PyUnresolvedReferences
                query = \
                    "INSERT INTO {0} ({1}) SELECT {2} " \
                    "WHERE NOT EXISTS (SELECT * FROM SyncFiles " \
                    "WHERE RemoteId = '{3}')".format(
                        row.table, row.columns, row.params, row.RemoteId)
            self.cur.execute(query, row.dict)
            row_id = self.cur.lastrowid
        except lite.IntegrityError:
            log.error('SQL constraint issue with {}'.format(row.dict))
            raise
        return row_id

    # noinspection SqlResolve
    def get_rows_by_search(
            self,
            row_type: Type[DbRow] = None,
            uid: str = '',
            remote_id: str = '%',
            file_name: str = '%',
            path: str = '%',
            start_date: datetime = None,
            end_date: datetime = None,
            skip_downloaded: bool = False) -> Iterator[DatabaseMedia]:
        """
        Search for a selection of files in a media table.

        Parameters:
            row_type: One of the DbRow derived classes - defines which table
              this request is for
            uid: the exif unique identifier search entry (can be ISNULL)
            remote_id: Google Photos unique ID
            file_name:
            path:
            start_date: start day for search
            end_date: end day for search
            skip_downloaded: Dont return entries already downloaded
        Return:
            An iterator over query results
        """
        params = (remote_id, file_name, path)
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
        if uid:
            extra_clauses += 'AND Uid ' + uid

        query = "SELECT {0} FROM {1} WHERE RemoteId LIKE ? " \
                "AND FileName LIKE ? and Path LIKE ? {2};". \
            format(row_type.columns, row_type.table, extra_clauses)

        try:
            self.cur2.execute(query, params)
            while True:
                records = self.cur2.fetchmany(LocalData.BLOCK_SIZE)
                if not records:
                    break
                for record in records:
                    yield row_type(record).to_media()
        except Exception:
            log.error('query: %s\nparams: %s', query, params)
            raise

    # noinspection SqlResolve
    def get_file_by_path(
            self,
            row_type: Type[DbRow],
            folder: Path,
            name: str) -> DatabaseMedia:
        """
        Search for a media item by filename, this applies to any of the
        BaseMedia/DbRow derived class pairs
        """
        query = "SELECT {0} FROM {1} WHERE Path = ?" \
                " AND FileName = ?;".format(row_type.columns, row_type.table)
        self.cur.execute(query, (str(folder), name))
        record = self.cur.fetchone()
        return row_type(record).to_media()

    # functions for managing the SyncFiles Table ##############################

    # todo this could be generic and support Albums and LocalFiles too
    def file_duplicate_no(self, name: str,
                          path: str, remote_id: str) -> (int, DatabaseMedia):
        """
        determine if there is already an entry for file. If not determine
        if other entries share the same path/filename and determine a duplicate
        number for providing a unique local filename suffix

        Returns:
            duplicate no. (zero if there are no duplicates),
            Single row from the SyncRow table
        """
        query = "SELECT {0} FROM SyncFiles WHERE RemoteId = ?; ". \
            format(GooglePhotosRow.columns)
        self.cur.execute(query, (remote_id,))
        result = self.cur.fetchone()

        if result:
            # return the existing file entry's duplicate no.
            return result['DuplicateNo'], GooglePhotosRow(result).to_media()

        if self.case_insensitive:
            self.cur.execute(
                "SELECT MAX(DuplicateNo) FROM SyncFiles "
                "WHERE Path = ? AND lower(OrigFileName) = ?;",
                (path, name.lower()))
        else:
            self.cur.execute(
                "SELECT MAX(DuplicateNo) FROM SyncFiles "
                "WHERE Path = ? AND OrigFileName = ?;",
                (path, name))

        results = self.cur.fetchone()
        if results[0] is not None:
            # assign the next available duplicate no.
            dup = results[0] + 1
            return dup, None
        else:
            # the file is new and has no duplicates
            return 0, None

    def put_location(self, sync_file_id: str, location: str):
        self.cur.execute(
            "UPDATE SyncFiles SET Location=? "
            "WHERE RemoteId IS ?;", (location, sync_file_id))

    def put_downloaded(self, sync_file_id: str, downloaded: bool = True):
        self.cur.execute(
            "UPDATE SyncFiles SET Downloaded=? "
            "WHERE RemoteId IS ?;", (downloaded, sync_file_id))

    def downloaded_count(self, downloaded: bool = True) -> int:
        self.cur.execute(
            "Select Count(Downloaded) from main.SyncFiles WHERE Downloaded=? ",
            (downloaded,))
        result = self.cur.fetchone()[0]
        return result

    # functions for managing Albums ###########################################
    def get_album(self, album_id: str) -> DatabaseMedia:
        query = "SELECT {0} FROM Albums WHERE RemoteId = ?;".format(
            GoogleAlbumsRow.columns)
        self.cur.execute(query, (album_id,))
        res = self.cur.fetchone()
        return GoogleAlbumsRow(res).to_media()

    def put_album_downloaded(self, album_id: str, downloaded: bool = True):
        self.cur.execute(
            "UPDATE Albums SET Downloaded=? "
            "WHERE RemoteId IS ?;", (downloaded, album_id))

    def get_album_files(self, album_id: str = '%', download_again: bool = False
                        ) -> (str, str, str, str, str):
        """ Join the Albums, SyncFiles and AlbumFiles tables to get a list
        of the files in an album or all albums.
        Parameters
            album_id: the Google Photos unique id for an album or None for all
            albums
        Returns:
            A tuple containing:
                Path, Filename, AlbumName, Album end date
        """

        extra_clauses = '' if download_again else 'AND Albums.Downloaded==0'

        query = """
        SELECT SyncFiles.Path, SyncFiles.Filename, Albums.AlbumName,
        Albums.EndDate, Albums.RemoteId, SyncFiles.CreateDate FROM AlbumFiles
        INNER JOIN SyncFiles ON AlbumFiles.DriveRec=SyncFiles.RemoteId
        INNER JOIN Albums ON AlbumFiles.AlbumRec=Albums.RemoteId
        WHERE Albums.RemoteId LIKE ? 
        {}
        ORDER BY Albums.RemoteId, SyncFiles.CreateDate;""".format(extra_clauses)

        self.cur.execute(query, (album_id,))
        results = self.cur.fetchall()
        # fetchall does not need to use cur2
        for result in results:
            yield tuple(result)

    def put_album_file(self, album_rec: str, file_rec: str):
        """ Record in the DB a relationship between an album and a media item
        """
        self.cur.execute(
            "INSERT OR REPLACE INTO AlbumFiles(AlbumRec, DriveRec) "
            "VALUES(?,"
            "?) ;",
            (album_rec, file_rec))

    def remove_all_album_files(self):
        # noinspection SqlWithoutWhere
        self.cur.execute("DELETE FROM AlbumFiles")

    # ---- LocalFiles Queries -------------------------------------------

    def get_missing_paths(self):
        self.cur2.execute(Queries.missing_files)
        while True:
            records = self.cur2.fetchmany(LocalData.BLOCK_SIZE)
            if not records:
                break
            for record in records:
                r = LocalFilesRow(record).to_media()
                pth = Path(r.relative_path.parent / r.filename)
                yield pth

    def get_duplicates(self):
        self.cur2.execute(Queries.duplicate_files)
        while True:
            records = self.cur2.fetchmany(LocalData.BLOCK_SIZE)
            if not records:
                break
            for record in records:
                r = LocalFilesRow(record).to_media()
                pth = r.relative_path.parent / r.filename
                yield r.id, pth

    def get_extra_paths(self):
        self.cur2.execute(Queries.pre_extra_files)
        self.cur2.execute(Queries.extra_files)
        while True:
            records = self.cur2.fetchmany(LocalData.BLOCK_SIZE)
            if not records:
                break
            for record in records:
                r = GooglePhotosRow(record).to_media()
                pth = r.relative_path.parent / r.filename
                yield pth

    def local_exists(self, file_name: str, path: str):
        self.cur.execute(
            "SELECT COUNT() FROM main.LocalFiles WHERE FileName = ?"
            "AND PATH = ?;", (file_name, path))
        result = int(self.cur.fetchone()[0])
        return result

    def local_erase(self):
        # noinspection SqlWithoutWhere
        self.cur.execute("DELETE FROM main.LocalFiles")

    def find_local_matches(self):
        # noinspection SqlWithoutWhere
        for i, q in enumerate(Queries.match):
            log.info('Executing local match query {}'.format(i))
            self.cur.execute(q)
