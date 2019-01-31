#!/usr/bin/env python3
# coding: utf8
from datetime import datetime

from gphotos.BaseMedia import BaseMedia
from gphotos.LocalData import LocalData
from typing import TypeVar, Iterator

# this allows self reference to this class in its factory methods
D = TypeVar('D', bound='DatabaseMedia')


class DatabaseMedia(BaseMedia):
    """A Class for instantiating a DatabaseMedia object from the database

    The standard BaseMedia attributes are presented here and are read in
    from the database using one of the two class factory methods.

    Attributes:
        _id: remote identifier from Google Photos
        _url: the 'product URL' which takes you to the Web view for this file
        _relative_folder: root relative path to file
        _filename: local filename
        _orig_name: as above minus any duplicate number suffix
        _duplicate_number: which instance if > 1 file has same orig_name
        _size: files size on disk
        _mimeType: string representation of file type
        _date: modification date
        _create_date: creation date
        _description:
        _downloaded: true if previously downloaded to disk
    """
    def __init__(self, row: LocalData.SyncRow):
        """
        This constructor is kept in sync with changes to the SyncFiles table

        Args:
            row: object with an attribute for each column in the SyncFiles
            table.
        """
        super(DatabaseMedia, self).__init__()

        if row:
            self._id: str = row.RemoteId
            self._url: str = row.Url
            self._relative_folder: str = row.Path
            self._filename: str = row.FileName
            self._orig_name: str = row.OrigFileName
            self._duplicate_number: int = int(row.DuplicateNo)
            self._size: int = int(row.FileSize)
            self._mimeType: str = row.MimeType
            self._description: str = row.Description
            self._date: datetime = row.ModifyDate
            self._create_date: datetime = row.CreateDate
            self._downloaded: bool = row.Downloaded
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

        Returns:
            DatabaseMedia object representing a single row
        """
        data_tuple = db.get_file_by_path(folder, name)
        return DatabaseMedia(data_tuple)

    @classmethod
    def get_media_by_search(cls, db: LocalData,
                            remote_id: str = '%',
                            start_date: datetime = None,
                            end_date: datetime = None,
                            skip_downloaded: bool = False) -> Iterator[D]:
        """
        A factory method to find any number of rows in SyncFile and yield an
        iterator of DataBaseMedia objects representing the results

        Args:
            db: the database wrapper object
            remote_id: optional id of row to find
            start_date: optional date filter
            end_date: optional date filter
            skip_downloaded: skip files with downloaded=1

        Returns:
            yields DatabaseMedia objects filled with rows from database
        """
        for record in db.get_files_by_search(
                remote_id, start_date, end_date, skip_downloaded):
            new_media = DatabaseMedia(record)
            yield new_media

    # ----- BaseMedia base class override Properties below -----
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
