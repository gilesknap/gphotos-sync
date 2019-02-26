#!/usr/bin/env python3
# coding: utf8
from typing import TypeVar
from datetime import datetime
from gphotos import Utils
from gphotos.DbRow import DbRow
from gphotos.DatabaseMedia import DatabaseMedia
from gphotos.GoogleAlbumMedia import GoogleAlbumMedia
import logging

log = logging.getLogger(__name__)

# this allows self reference to this class in its factory methods
G = TypeVar('G', bound='GoogleAlbumsRow')


@DbRow.db_row
class GoogleAlbumsRow(DbRow):
    """
    generates a class with attributes for each of the columns in the
    SyncFiles table
    """
    table = "Albums"
    cols_def = {'RemoteId': str, 'AlbumName': str, 'Size': int,
                'StartDate': datetime,
                'EndDate': datetime, 'SyncDate': datetime,
                'Downloaded': bool}

    def to_media(self) -> DatabaseMedia:
        db_media = DatabaseMedia(
            _id=self.RemoteId,
            _filename=self.AlbumName,
            _size=self.Size,
            _create_date=self.EndDate)
        return db_media

    @classmethod
    def from_media(cls, album: GoogleAlbumMedia) -> G:
        pass

    @classmethod
    def from_parm(cls, album_id, filename, size, start, end) -> G:
        new_row = cls.make(
            RemoteId=album_id,
            AlbumName=filename,
            Size=size,
            StartDate=start,
            EndDate=end,
            SyncDate=Utils.date_to_string(
                datetime.now()),
            Downloaded=0)
        return new_row
