#!/usr/bin/env python3
# coding: utf8
from datetime import datetime
from typing import TypeVar, Iterator

from gphotos.BaseMedia import BaseMedia

# this allows self reference to this class in its factory methods
D = TypeVar('D', bound='DatabaseMedia')


class DatabaseMedia(BaseMedia):
    """A Class for reading and writing BaseMedia objects to and from
    database tables

    The standard BaseMedia attributes are represented here. This dumb class
    is used for representing any MediaBase derived class that has been read out
    of the Database.

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
    def __init__(self):
        super(DatabaseMedia, self).__init__()
        self._id: str = None
        self._url: str = None
        self._relative_folder: str = None
        self._filename: str = None
        self._orig_name: str = None
        self._duplicate_number: int = None
        self._size: int = None
        self._mimeType: str = None
        self._description: str = None
        self._date: datetime = None
        self._create_date: datetime = None
        self._downloaded: bool = None

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
