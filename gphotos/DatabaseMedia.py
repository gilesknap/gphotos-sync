#!/usr/bin/env python3
# coding: utf8
from datetime import datetime

from gphotos.BaseMedia import BaseMedia, MediaType
from gphotos.LocalData import LocalData
from typing import TypeVar

D = TypeVar('D', bound='DatabaseMedia')


class DatabaseMedia(BaseMedia):
    """A Class for instantiating a GoogleMedia object from the database

    The standard GoogleMedia attributes are presented here and are read in
    from the database using one of the two factory class methods.

    Attributes:
        _id: remote identifier from Google Photos
        _filename:
        _orig_name:
        _duplicate_number:
        _date:
        _description:
        _size:
        _create_date:
        _media_type:
        _sym_link:
    """
    MEDIA_TYPE = MediaType.DATABASE

    def __init__(self, row: LocalData.SyncRow):
        """
        This constructor is kept in sync with changes to the SyncFiles table

        Args:
            row: a tuple containing a value for each column in the SyncFiles
            table.
        """
        super(DatabaseMedia, self).__init__()

        if row:
            self._id = row.RemoteId
            self._url = row.Url
            self._relative_folder = row.Path
            self._filename = row.FileName
            self._orig_name = row.OrigFileName
            self._duplicate_number = row.DuplicateNo
            self._media_type = row.MediaType
            self._size = row.FileSize
            self._mimeType = row.MimeType
            self._description = row.Description
            self._date = row.ModifyDate
            self._create_date = row.CreateDate
            self._sym_link = row.SymLink = None
            self._downloaded = row.Downloaded = None

            self.duplicate_number = int(self.duplicate_number)
        else:
            # this indicates record not found
            self._id = None

    @classmethod
    def get_media_by_filename(cls, folder: str, name: str, db: LocalData) -> D:
        """
        A factory method for finding a single row in the SyncFile table by
        full path to filename and instantiate a DataBaseMedia object to
        represent it

        Args:
            folder : the root relative path to the file to find
            name: the name of the file to find
            db: the database wrapper object
        """
        data_tuple = db.get_file_by_path(folder, name)
        return DatabaseMedia(data_tuple)

    @classmethod
    def get_media_by_search(cls, db: LocalData, remote_id: str = '%',
                            media_type: MediaType = '%',
                            start_date: datetime = None,
                            end_date: datetime = None,
                            skip_linked: bool = False,
                            skip_downloaded: bool = False):
        """
        A factory method to find any number of rows in SyncFile and yield an
        iterator of DataBaseMedia objects representing the results

        Args:
            db: the database wrapper object
            remote_id: optional id of row to find
            media_type: optional type of rows to find
            start_date: optional date filter
            end_date: optional date filter
            skip_linked: skip files with non-null SymLink
            skip_downloaded: skip files with downloaded=1

        Returns:
            yields GoogleMedia object filled from database
        """
        for record in db.get_files_by_search(
                remote_id, media_type, start_date, end_date, skip_linked,
                skip_downloaded):
            new_media = DatabaseMedia(record)
            yield new_media

    # ----- GoogleMedia base class override Properties below -----
    @property
    def size(self) -> int:
        return self._size

    @property
    def mime_type(self) -> str:
        return self._mimeType

    @property
    def id(self) -> str:
        return self._id

    @property
    def description(self) -> str:
        """
        The description of the file
        """
        return self.validate_encoding(self._description)

    @property
    def orig_name(self) -> str:
        """
        Original filename before duplicate name handling
        """
        return self.validate_encoding(self._orig_name)

    @property
    def filename(self)->str:
        """
        filename including a suffix to make it unique if duplicates exist
        """
        return self.validate_encoding(self._filename)

    @property
    def create_date(self) -> datetime:
        """
        Creation date
        """
        return self._create_date

    @property
    def modify_date(self) -> datetime:
        """
        Modify Date
        """
        return self._date

    @property
    def url(self) -> str:
        """
        Remote url to retrieve this file from the server
        """
        return self._url
