#!/usr/bin/env python3
# coding: utf8
from typing import TypeVar
from datetime import datetime
from gphotos.DbRow import DbRow
from gphotos.BaseMedia import BaseMedia
from gphotos.DatabaseMedia import DatabaseMedia
from gphotos.GooglePhotosMedia import GooglePhotosMedia
import logging

log = logging.getLogger(__name__)

# this allows self reference to this class in its factory methods
G = TypeVar('G', bound='GooglePhotosRow')


@DbRow.db_row
class GooglePhotosRow(DbRow):
    """
    generates a class with attributes for each of the columns in the
    SyncFiles table
    """
    table = 'SyncFiles'
    cols_def = {'Id': int, 'RemoteId': str, 'Url': str, 'Path': str,
                'FileName': str, 'OrigFileName': str, 'DuplicateNo': int,
                'FileSize': int, 'MimeType': str, 'Description': str,
                'ModifyDate': datetime, 'CreateDate': datetime,
                'SyncDate': datetime, 'Downloaded': int}
    no_update = ['Id']

    def to_media(self) -> DatabaseMedia:
        db_media = DatabaseMedia(
            _id=self.RemoteId,
            _url=self.Url,
            _relative_folder=self.Path,
            _filename=self.FileName,
            _orig_name=self.OrigFileName,
            _duplicate_number=self.DuplicateNo,
            _size=self.FileSize,
            _mime_type=self.MimeType,
            _description=self.Description,
            _date=self.ModifyDate,
            _create_date=self.CreateDate,
            _downloaded=self.Downloaded)
        return db_media

    @classmethod
    def from_media(cls, media: GooglePhotosMedia) -> G:
        now_time = datetime.now().strftime(BaseMedia.TIME_FORMAT)
        new_row = cls.make(RemoteId=media.id, Url=media.url,
                           Path=media.relative_folder,
                           FileName=media.filename,
                           OrigFileName=media.orig_name,
                           DuplicateNo=media.duplicate_number,
                           FileSize=media.size,
                           MimeType=media.mime_type,
                           Description=media.description,
                           ModifyDate=media.modify_date,
                           CreateDate=media.create_date,
                           SyncDate=now_time,
                           Downloaded=0)
        return new_row
