#!/usr/bin/env python2
# coding: utf8
import os.path
import re
from time import gmtime, strftime
from datetime import datetime
from enum import Enum

from .LocalData import LocalData

from enum import IntEnum


class FileType(IntEnum):
    Other = 0
    Video = 1
    Image = 2


# an enum for identifying the type of subclass during polymorphic use
# only used for identifying the root folder the media should occupy locally
class MediaType(IntEnum):
    PHOTOS = 0
    ALBUM = 1
    DATABASE = 2
    NONE = 3


# base class for media model classes
# noinspection PyCompatibility
class GoogleMedia(object):
    MEDIA_TYPE = MediaType.NONE
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, **k_args):
        self.media_type = self.__class__.MEDIA_TYPE
        self._relative_folder = None
        self._duplicate_number = 0
        self.symlink = False
        self.file_type = None

    # regex for illegal characters in file names and database queries
    fix_linux = re.compile(r'[/]|[\x00-\x1f]|\x7f|\x00')
    fix_windows = re.compile(r'[<>:"/\\|?*]|[\x00-\x1f]|\x7f|\x00')
    fix_windows_ending = re.compile('([ .]+$)')

    def validate_encoding(self, s):
        """
        makes sure a string is valid for creating file names and converts to
        unicode assuming utf8 encoding if necessary

        :param (str) string: input string (or unicode string)
        :return: (unicode): sanitized string
        """
        if os.name == 'nt':
            s = self.fix_windows.sub('_', s)
            s = self.fix_windows_ending.split(s)[0]
        else:
            s = self.fix_linux.sub('_', s)
        return s

    def save_to_db(self, db, update=False):
        now_time = strftime(GoogleMedia.TIME_FORMAT, gmtime())
        new_row = LocalData.SyncRow.make(RemoteId=self.id, Url=self.url,
                                         Path=self.relative_folder,
                                         FileName=self.filename,
                                         OrigFileName=self.orig_name,
                                         DuplicateNo=self.duplicate_number,
                                         MediaType=self.media_type,
                                         FileSize=self.size,
                                         Checksum=self.checksum,
                                         Description=self.description,
                                         ModifyDate=self.modify_date,
                                         CreateDate=self.create_date,
                                         SyncDate=now_time, SymLink=None)
        return db.put_file(new_row, update)

    def set_path_by_date(self):
        y = "{:04d}".format(self.create_date.year)
        m = "{:02d}".format(self.create_date.month)
        self._relative_folder = os.path.join(y, m)

    @property
    def duplicate_number(self):
        return self._duplicate_number

    @duplicate_number.setter
    def duplicate_number(self, value):
        self._duplicate_number = value

    def is_indexed(self, db):
        # checking for index has the side effect of setting duplicate number as
        # it is when we discover if other entries share path and filename
        (num, row) = db.file_duplicate_no(self.filename, self.relative_folder, self.id)
        self._duplicate_number = num
        return row

    # Relative path to the media file from the root of the sync folder
    # e.g. 'Google Photos/2017/09'.
    @property
    def relative_path(self):
        return os.path.join(self._relative_folder, self.filename)

    # as above but without the filename appended
    @property
    def relative_folder(self):
        return self._relative_folder

    @property
    def filename(self):
        if self.duplicate_number > 0:
            base, ext = os.path.splitext(os.path.basename(self.orig_name))
            filename = "%(base)s (%(duplicate)d)%(ext)s" % {
                'base': base,
                'ext': ext,
                'duplicate': self.duplicate_number
            }
        else:
            filename = self.orig_name
        return self.validate_encoding(filename)

    # ----- Properties for override below -----
    @property
    def size(self):
        """
        :rtype: int
        """
        raise NotImplementedError

    @property
    def checksum(self):
        """
        :rtype: str
        """
        raise NotImplementedError

    @property
    def id(self):
        """
        :rtype: int
        """
        raise NotImplementedError

    @property
    def description(self):
        """
        :rtype: str
        """
        raise NotImplementedError

    @property
    def orig_name(self):
        """
        :rtype: str
        """
        raise NotImplementedError

    @property
    def create_date(self):
        """
        :rtype: datetime
        """
        raise NotImplementedError

    @property
    def modify_date(self):
        """
        :rtype: datetime
        """
        raise NotImplementedError

    @property
    def mime_type(self):
        """
        :rtype: str
        """
        raise NotImplementedError

    @property
    def url(self):
        """
        :rtype: str
        """
        raise NotImplementedError
