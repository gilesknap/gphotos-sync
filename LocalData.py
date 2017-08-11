#!/usr/bin/python
# coding: utf8
import os.path
import sqlite3 as lite
import re
from datetime import datetime
from enum import Enum


class FileStatus(Enum):
    New = 1
    Updated = 2
    Unchanged = 3


class LocalData:
    DB_FILE_NAME = 'gphotos.sql'
    VERSION = 1.1

    def __init__(self, root_folder):
        self.file_name = os.path.join(root_folder, LocalData.DB_FILE_NAME)
        if not os.path.exists(root_folder):
            os.mkdir(root_folder, 0o700)
        self.con = lite.connect(self.file_name)
        self.con.row_factory = lite.Row
        self.cur = self.con.cursor()

        if self.db_is_new():
            print('initialising new database')
            self.setup_new_db()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.con:
            self.con.commit()
            self.con.close()

    def setup_new_db(self):
        self.cur.executescript("""
            CREATE TABLE Globals(Version INT, Albums INT,
              Files INT, LastScanDate TEXT);
            CREATE TABLE DriveFiles(Id INTEGER PRIMARY KEY, DriveId TEXT, 
              OrigFileName TEXT, DriveFileName TEXT, LocalFileName TEXT);
            CREATE TABLE Albums(Id INTEGER PRIMARY KEY, AlbumId TEXT,
              AlbumName TEXT);
            CREATE TABLE AlbumFiles(Id INTEGER PRIMARY KEY, Title TEXT,
              AlbumNo INT) """)
        self.cur.execute("INSERT INTO Globals VALUES(?,0,0, 'Never');",
                         (LocalData.VERSION,))
        self.con.commit()

    def db_is_new(self):
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table'"
                         "AND name = 'Globals'")
        data = self.cur.fetchone()
        return data is None

    def get_file(self, local_name):
        self.cur.execute(
            "SELECT id, DriveId, OrigFileName, DriveFileName,LocalFileName "
            "FROM DriveFiles WHERE LocalFileName = ?",
            (local_name,))
        res = self.cur.fetchone()
        return res

    def put_file(self, drive_id, orig_filename, drive_filename, local_filename):
        self.cur.execute(
            "INSERT INTO DriveFiles(DriveId, OrigFileName, DriveFileName, " \
            "LocalFileName) VALUES(?,?,?,?) ;",
            (drive_id, orig_filename, drive_filename,
             local_filename))
