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
        db_media = DatabaseMedia()
        db_media._id: str = self.RemoteId
        db_media._url: str = self.Url
        db_media._relative_folder: str = self.Path
        db_media._filename: str = self.FileName
        db_media._orig_name: str = self.OrigFileName
        db_media._duplicate_number: int = int(self.DuplicateNo)
        db_media._size: int = int(self.FileSize)
        db_media._mimeType: str = self.MimeType
        db_media._description: str = self.Description
        db_media._date: datetime = self.ModifyDate
        db_media._create_date: datetime = self.CreateDate
        db_media._downloaded: bool = self.Downloaded
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
