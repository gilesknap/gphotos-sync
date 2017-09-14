#!/usr/bin/python
# coding: utf8
import os.path
from enum import Enum
from time import gmtime, strftime
from LocalData import LocalData
import re


# an enum for identifying the type of subclass during polymorphic use
# only used for identifying the root folder the media should occupy locally
class MediaType(Enum):
    DRIVE = 0
    PICASA = 1
    ALBUM = 2
    DATABASE = 3
    NONE = 4


# folder names for each of rhe types of media specified above
MediaFolder = [
    u'drive',
    u'picasa',
    u'albums',
    u'',
    u'']


# base class for media model classes
class GoogleMedia(object):
    MEDIA_TYPE = MediaType.NONE
    # todo below is nice and concise and works but the type checker fails
    # noinspection PyTypeChecker
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
        self.symlink = False  # Todo need to implement use of this

    # regex for illegal characters in file names and database queries
    fix_linux = re.compile(r'[/]|[\x00-\x1f]|\x7f|\x00')
    fix_windows = re.compile(r'[<>:"/\\|?*]|[\x00-\x1f]|\x7f|\x00')

    def validate_encoding(self, string):
        """
        makes sure a string is valid for creating file names and converts to
        unicode assuming utf8 encoding if necessary

        :param (str) string: input string (or unicode string)
        :return: (unicode): sanitized string
        """
        if string is None:  # a string of '' is valid
            return None
        elif isinstance(string, unicode):
            s = string
        else:
            s = unicode(string, 'utf8')

        if os.name == 'nt':
            s = self.fix_windows.sub('_', s)
        else:
            s = self.fix_linux.sub('_', s)
        return s

    def save_to_db(self, db):
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
                                         ModifyDate=self.date,
                                         CreateDate=self.create_date,
                                         SyncDate=now_time, SymLink=None)
        return db.put_file(new_row)

    def is_indexed(self, db):
        # todo (this is brittle so fix it)
        # checking for index has the side effect of setting duplicate no
        # probably should do this immediately after subclass init
        num = db.file_duplicate_no(
            self.id, self.local_folder, self.orig_name)
        self.duplicate_number = num
        result = db.get_file_by_id(remote_id=self.id)
        return result is not None

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
        raise NotImplementedError

    @property
    def checksum(self):
        raise NotImplementedError

    @property
    def id(self):
        raise NotImplementedError

    @property
    def description(self):
        raise NotImplementedError

    @property
    def orig_name(self):
        raise NotImplementedError

    @property
    def create_date(self):
        raise NotImplementedError

    @property
    def date(self):
        raise NotImplementedError

    @property
    def mime_type(self):
        raise NotImplementedError

    @property
    def url(self):
        raise NotImplementedError
