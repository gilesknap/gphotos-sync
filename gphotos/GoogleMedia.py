#!/usr/bin/env python2
# coding: utf8
import os.path
import re
from time import gmtime, strftime
from datetime import datetime
from enum import Enum

from .LocalData import LocalData


class IntEnum(int, Enum):
    pass


# an enum for identifying the type of subclass during polymorphic use
# only used for identifying the root folder the media should occupy locally
class MediaType(IntEnum):
    PHOTOS = 0
    ALBUM = 1
    DATABASE = 2
    NONE = 3


# folder names for each of the types of media specified above
MediaFolder = [
    u'drive',
    u'picasa',
    u'albums',
    u'',
    u'']


# base class for media model classes
# noinspection PyCompatibility
class GoogleMedia(object):
    MEDIA_TYPE = MediaType.NONE
    MEDIA_FOLDER = MediaFolder[MEDIA_TYPE]
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    # todo remove relative path and determine it in derived classes
    # note that PicasaMedia and DataBaseMedia already do this
    def __init__(self, relative_folder, root_folder, **k_args):
        self.media_type = self.__class__.MEDIA_TYPE
        self._media_folder = self.__class__.MEDIA_FOLDER
        self._relative_folder = relative_folder
        self._root_folder = root_folder
        self._duplicate_number = 0
        self.symlink = False

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
                                         Path=self.local_folder,
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

    def is_indexed(self, db):
        # checking for index has the side effect of setting duplicate number as
        # it is when we discover if other entries share path and filename
        # IMPORTANT - it would seem logical to use remoteId to verify if the
        # item is already indexed BUT remote id varies in picasa API
        # for the same item in more than one album
        (num, row) = db.file_duplicate_no(self.create_date, self.filename,
                                          self.size, self.local_folder,
                                          self.media_type, self.id)
        self.duplicate_number = num
        return row

    # Path to the local folder in which this media item is stored this
    # will include the media type folder which is one of 'drive' 'picasa' or
    # 'albums'
    @property
    def local_folder(self):
        return os.path.join(self._root_folder, self._media_folder,
                            self._relative_folder)

    # Path to the local file in which this media item is stored
    @property
    def local_full_path(self):
        return os.path.join(self.local_folder, self.filename)

    # Relative path to the media file from the root of the media type folder
    # e.g. 'Google Photos/2017/09'. This also represents the path to the
    # folder on google drive in which this is stored (if there is one)
    @property
    def relative_path(self):
        return os.path.join(self._relative_folder, self.filename)

    # as above but with the filename appended
    @property
    def relative_folder(self):
        return self._relative_folder

    @property
    def duplicate_number(self):
        return self._duplicate_number

    @duplicate_number.setter
    def duplicate_number(self, value):
        self._duplicate_number = value

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
