#!/usr/bin/env python3
# coding: utf8
from datetime import datetime
from pathlib import Path
from typing import Optional, TypeVar

from gphotos_sync import Utils
from gphotos_sync.BaseMedia import BaseMedia
from gphotos_sync.Checks import get_check

# this allows self reference to this class in its factory methods
D = TypeVar("D", bound="DatabaseMedia")


# noinspection PyUnresolvedReferences
# pylint: disable=no-member
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
        _mime_type: string representation of file type
        _date: modification date
        _create_date: creation date
        _description:
        _downloaded: true if previously downloaded to disk
    """

    def __init__(
        self,
        _id: str = "",
        _uid: str = "",
        _url: str = "",
        _relative_folder: Path = Path(),
        _filename: str = "",
        _orig_name: str = "",
        _duplicate_number: int = 0,
        _size: int = 0,
        _mime_type: str = "",
        _description: str = "",
        _date: datetime = Utils.MINIMUM_DATE,
        _create_date: datetime = Utils.MINIMUM_DATE,
        _downloaded: bool = False,
        _location: str = "",
    ):
        super(DatabaseMedia, self).__init__()
        self._id = _id
        self._uid = _uid
        self._url = _url
        self._relative_folder = _relative_folder
        self._filename = _filename
        self._orig_name = _orig_name
        self._duplicate_number = _duplicate_number
        self._size = _size
        self._mime_type = _mime_type
        self._description = _description
        self._date = _date
        self._create_date = _create_date
        self._downloaded = _downloaded
        self._location = _location

    # this is used to replace meta data that has been extracted from the
    # file system and overrides that provided by Google API
    # noinspection PyAttributeOutsideInit
    def update_extra_meta(self, uid, create_date, size):
        self._uid = uid
        self._create_date = create_date
        self._size = size

    @property
    def location(self) -> Optional[str]:
        """
        image GPS information
        """
        return self._location

    # ----- BaseMedia base class override Properties below -----
    @property
    def size(self) -> int:
        return self._size

    @property
    def mime_type(self) -> Optional[str]:
        return self._mime_type

    @property
    def id(self) -> str:
        return self._id

    @property
    def uid(self) -> str:
        return self._uid

    @property
    def description(self) -> str:
        """
        The description of the file
        """
        return get_check().valid_file_name(self._description)

    @property
    def orig_name(self) -> str:
        """
        Original filename before duplicate name handling
        """
        return get_check().valid_file_name(self._orig_name)

    @property
    def filename(self) -> str:
        """
        filename including a suffix to make it unique if duplicates exist
        """
        return get_check().valid_file_name(self._filename)

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
