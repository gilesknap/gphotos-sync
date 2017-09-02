#!/usr/bin/python
# coding: utf8
import os.path
from enum import Enum
from datetime import datetime
from time import gmtime, strftime


class MediaType(Enum):
    DRIVE = 0
    PICASA = 1
    ALBUM_LINK = 2
    DATABASE = 4
    NONE = 4


MediaFolder = [
    'drive',
    'picasa',
    'albums',
    '',
    '']


# base class for media model classes
class GoogleMedia(object):
    MEDIA_TYPE = MediaType.NONE
    MEDIA_FOLDER = MediaFolder[MEDIA_TYPE]
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    # todo remove relative path removed and determine it in derived classes
    # note that PicasaMedia and DataBaseMedia already do this
    def __init__(self, relative_folder, root_folder, **k_args):
        self.media_type = self.__class__.MEDIA_TYPE
        self.media_folder = self.__class__.MEDIA_FOLDER
        self._relative_folder = relative_folder
        self._root_folder = root_folder
        self._duplicate_number = 0
        self.symlink = False  # Todo need to implement use of this

    def save_to_db(self, db):
        now_time = strftime(GoogleMedia.TIME_FORMAT, gmtime())
        if isinstance(self.description, unicode):
            description = self.description
        else:
            description = unicode(self.description, 'utf8')
        data_tuple = (
            self.id, self.url, self.local_folder,
            self.filename, self.duplicate_number,
            self.checksum, description, self.size,
            self.date, self.create_date, now_time, self.media_type,
            self.symlink
        )
        return db.put_file(data_tuple)

    def is_indexed(self, db):
        # checking for index has the side effect of setting duplicate no
        # probably should do this immediately after subclass init
        num = db.file_duplicate_no(self. id, self.local_full_path)
        self.duplicate_number = num
        result = db. find_drive_file_ids(filename=self.orig_name)

    # todo this is named wrong and sort out picsaSYnc / base date classmethods
    @classmethod
    def format_date(cls, date):
        return datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

    # Path to the local folder in which this media item is stored this
    # will include the media type folder which is one of 'drive' 'picasa' or
    # 'albums'
    @property
    def local_folder(self):
        return os.path.join(self._root_folder, self.media_folder,
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
            return "%(base)s (%(duplicate)d)%(ext)s" % {
                'base': base,
                'ext': ext,
                'duplicate': self.duplicate_number
            }
        else:
            return self.orig_name

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
