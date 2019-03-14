#!/usr/bin/env python3
# coding: utf8
from datetime import datetime
from typing import TypeVar

from gphotos.BaseMedia import BaseMedia

# this allows self reference to this class in its factory methods
D = TypeVar('D', bound='DatabaseMedia')


# noinspection PyUnresolvedReferences
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

    def __init__(self,
                 _id: str = None,
                 _uid: str = None,
                 _url: str = None,
                 _relative_folder: str = None,
                 _filename: str = None,
                 _orig_name: str = None,
                 _duplicate_number: int = None,
                 _size: int = None,
                 _mime_type: str = None,
                 _description: str = None,
                 _date: datetime = None,
                 _create_date: datetime = None,
                 _downloaded: bool = False,
                 _location: str = None):
        super(DatabaseMedia, self).__init__()
        # add all of the arguments as attributes on this object
        self.__dict__.update(locals())

    # this is used to replace meta data that has been extracted from the
    # file system and overrides that provided by Google API
    # noinspection PyAttributeOutsideInit
    def update_extra_meta(self, uid, create_date, size):
        self._uid = uid
        self._create_date = create_date
        self._size = size

    @property
    def location(self) -> str:
        """
        image GPS information
        """
        return self._location

    # ----- BaseMedia base class override Properties below -----
    @property
    def size(self) -> int:
        return self._size

    @property
    def mime_type(self) -> str:
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
        return self.validate_encoding(self._description)

    @property
    def orig_name(self) -> str:
        """
        Original filename before duplicate name handling
        """
        return self.validate_encoding(self._orig_name)

    @property
    def filename(self) -> str:
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
