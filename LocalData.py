#!/usr/bin/python
# coding: utf8
import os.path
import sqlite3 as lite
from time import gmtime, strftime
from GooglePhotosSync import GooglePhotosSync
import shutil


class LocalData:
    DB_FILE_NAME = 'gphotos.sql'
    EMPTY_FILE_NAME = 'gphotos_empty.sql'
    VERSION = "1.4"

    def __init__(self, root_folder):
        self.file_name = os.path.join(root_folder, LocalData.DB_FILE_NAME)
        if not os.path.exists(root_folder):
            os.mkdir(root_folder, 0o700)
        if not os.path.exists(self.file_name):
            self.setup_new_db()
        self.con = lite.connect(self.file_name)
        self.con.row_factory = lite.Row
        self.cur = self.con.cursor()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.con:
            self.con.commit()
            self.con.close()

    def setup_new_db(self):
        print("creating new database")
        src_folder = os.path.dirname(os.path.abspath(__file__))
        from_file = os.path.join(src_folder, LocalData.EMPTY_FILE_NAME)
        shutil.copy(from_file, self.file_name)

    # todo datatypes - should return and take GooglePhotoMedia / LocalMedia ??
    # todo e.g put_file already done
    def get_file(self, local_name):
        path = os.path.dirname(local_name)
        name = os.path.basename(local_name)
        self.cur.execute(
            "SELECT * FROM DriveFiles WHERE Path = ? AND FileName = ?;",
            (path, name))
        res = self.cur.fetchone()
        return res

    def find_drive_file(self, orig_name='%', exif_date='%', size='%',
                        use_create=False):
        if use_create:
            self.cur.execute(
                "SELECT Id FROM DriveFiles WHERE OrigFileName LIKE ? AND "
                "CreateDate LIKE ? AND FileSize LIKE ?;",
                (orig_name, exif_date, size))
        else:
            self.cur.execute(
                "SELECT Id FROM DriveFiles WHERE OrigFileName LIKE ? AND "
                "ExifDate LIKE ? AND FileSize LIKE ?;",
                (orig_name, exif_date, size))
        res = self.cur.fetchall()

        if len(res) == 0:
            return None
        else:
            return res

    def put_file(self, media):
        now_time = strftime(GooglePhotosSync.TIME_FORMAT, gmtime())
        self.cur.execute(
            "INSERT INTO DriveFiles VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ;",
            (None, media.id, media.orig_name, media.path, media.filename,
             media.duplicate_number, media.date, media.checksum,
             media.description, media.size, media.create_date,
             now_time, media.picassa_only))

    def get_album(self, table_id):
        self.cur.execute(
            "SELECT * FROM Albums WHERE Id = ?",
            (table_id,))
        res = self.cur.fetchone()
        return res

    def put_album(self, album_id, album_name):
        self.cur.execute(
            "INSERT INTO Albums(AlbumNo, DriveFile) VALUES(?,?) ;",
            (album_id, album_name))

    def get_album_files(self, album_id):
        self.cur.execute(
            "SELECT * FROM AlbumFiles WHERE Id = ?",
            (album_id,))
        res = self.cur.fetchall()
        return res

    def put_album_file(self, album_rec, file_rec):
        self.cur.execute(
            "INSERT INTO AlbumsFiles(AlbumRec, DriveFileRec) VALUES(?,?) ;",
            (album_rec, file_rec))
