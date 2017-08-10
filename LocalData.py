#!/usr/bin/python
# coding: utf8
import os.path
import sqlite3 as lite
import re
from datetime import datetime


class LocalData:
    DB_FILE_NAME = 'gphotos.sql'

    def __init__(self, root_folder):
        self.file_name = os.path.join(root_folder, LocalData.DB_FILE_NAME)
        if not os.path.exists(root_folder):
            os.mkdir(root_folder, 0o700)
        self.con = lite.connect(self.file_name)

        if not self.db_exists():
            self.create_new_db()

    def create_new_db(self):
        self.cur.executescript("""
            CREATE TABLE Globals(Id INTEGER PRIMARY KEY, Albums INT,
              Files INT, LastScanDate TEXT);
            INSERT INTO Globals VALUES(1,0,0, 'Never');
            CREATE TABLE DriveFiles(Id INTEGER PRIMARY KEY, DriveId TEXT, 
              OrigFileName TEXT, DriveFileName TEXT, LocalFileName, TEXT);
            CREATE TABLE Albums(Id INTEGER PRIMARY KEY, AlbumId TEXT,
              AlbumName Text);
            CREATE TABLE AlbumFiles(Id INTEGER PRIMARY KEY, Title TEXT,
              AlbumNo INT)
            """)

    def db_exists(self):
        self.cur = self.con.cursor()
        self.cur.execute("SELECT name from sqlite_master WHERE type='table'"
                         "AND name = 'Globals'")
        data = self.cur.fetchone()
        return data is not None

