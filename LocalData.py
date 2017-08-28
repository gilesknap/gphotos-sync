#!/usr/bin/python
# coding: utf8
import os.path
import sqlite3 as lite
import shutil


class LocalData:
    DB_FILE_NAME = 'gphotos.sql'
    EMPTY_FILE_NAME = 'etc/gphotos_empty.sqlite'
    VERSION = "1.4"

    class DuplicateDriveIdException(Exception):
        pass

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

    def get_file(self, local_full_path):
        path = os.path.dirname(local_full_path)
        name = os.path.basename(local_full_path)
        self.cur.execute(
            "SELECT * FROM DriveFiles WHERE Path = ? AND FileName = ?;",
            (path, name))
        res = self.cur.fetchone()
        if res:
            data_tuple = (
                res['DriveId'], res['OrigFileName'], res['Path'],
                res['FileName'], res['DuplicateNo'], res['ExifDate'],
                res['Checksum'], res['Description'], res['FileSize'],
                res['CreateDate'], res['SyncDate'], res['PicassaOnly']
            )
            return data_tuple
        else:
            return None

    def put_file(self, data_tuple):
        try:
            self.cur.execute(
                "INSERT INTO DriveFiles VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ;",
                (None,) + data_tuple)
        except lite.IntegrityError as e:
            if e.message == 'UNIQUE constraint failed: DriveFiles.DriveId':
                raise LocalData.DuplicateDriveIdException
            else:
                raise

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

    def get_album(self, table_id):
        self.cur.execute(
            "SELECT * FROM Albums WHERE Id = ?",
            (table_id,))
        res = self.cur.fetchone()
        return res

    def put_album(self, album_id, album_name, start_date, end_end=0):
        self.cur.execute(
            "INSERT OR REPLACE INTO Albums(AlbumId, AlbumName, StartDate, "
            "EndDate) VALUES(?,?,?,?) ;",
            (album_id, album_name, start_date, end_end))
        return self.cur.lastrowid

    def get_album_files(self, album_id):
        self.cur.execute(
            "SELECT * FROM AlbumFiles WHERE Id = ?",
            (album_id,))
        res = self.cur.fetchall()
        return res

    def put_album_file(self, album_rec, file_rec):
        self.cur.execute(
            "INSERT OR REPLACE INTO AlbumFiles(AlbumRec, DriveRec) VALUES(?,"
            "?) ;",
            (album_rec, file_rec))
