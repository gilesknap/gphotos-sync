#!/usr/bin/env python3
# coding: utf8
import os.path
import re
from time import gmtime, strftime
from datetime import datetime
from gphotos.LocalData import LocalData


class BaseMedia(object):
    """Base class for media model classes.
    These provide a standard interface for media items that have been loaded
    from disk / loaded from DB / retrieved from the Google Photos Library
    """
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, **k_args):
        self._relative_folder = None
        self._duplicate_number = 0

    # regex for illegal characters in file names and database queries
    fix_linux = re.compile(r'[/]|[\x00-\x1f]|\x7f|\x00')
    fix_windows = re.compile(r'[<>:"/\\|?*]|[\x00-\x1f]|\x7f|\x00')
    fix_windows_ending = re.compile('([ .]+$)')

    def validate_encoding(self, s: str) -> str:
        """
        makes sure a string is valid for creating file names and converts to
        unicode assuming utf8 encoding if necessary

        :param (str) s: input string (or unicode string)
        :return: (unicode): sanitized string
        """
        if os.name == 'nt':
            s = self.fix_windows.sub('_', s)
            s = self.fix_windows_ending.split(s)[0]
        else:
            s = self.fix_linux.sub('_', s)
        return s

    def save_to_db(self, db: LocalData, update: bool = False) -> int:
        now_time = strftime(BaseMedia.TIME_FORMAT, gmtime())
        new_row = LocalData.SyncRow.make(RemoteId=self.id, Url=self.url,
                                         Path=self.relative_folder,
                                         FileName=self.filename,
                                         OrigFileName=self.orig_name,
                                         DuplicateNo=self.duplicate_number,
                                         FileSize=self.size,
                                         MimeType=self.mime_type,
                                         Description=self.description,
                                         ModifyDate=self.modify_date,
                                         CreateDate=self.create_date,
                                         SyncDate=now_time,
                                         Downloaded=0)
        return db.put_file(new_row, update)

    def set_path_by_date(self, root: str):
        y = "{:04d}".format(self.create_date.year)
        m = "{:02d}".format(self.create_date.month)
        self._relative_folder = os.path.join(root, y, m)

    def is_video(self) -> bool:
        return self.mime_type.startswith('video')

    @property
    def duplicate_number(self) -> int:
        return self._duplicate_number

    @duplicate_number.setter
    def duplicate_number(self, value: int):
        self._duplicate_number = value

    def is_indexed(self, db: LocalData) -> LocalData.SyncRow:
        # checking for index has the side effect of setting duplicate number as
        # it is when we discover if other entries share path and filename
        (num, row) = db.file_duplicate_no(self.filename, self.relative_folder,
                                          self.id)
        self._duplicate_number = num
        return row

    # Relative path to the media file from the root of the sync folder
    # e.g. 'Google Photos/2017/09'.
    @property
    def relative_path(self) -> str:
        return os.path.join(self._relative_folder, self.filename)

    # as above but without the filename appended
    @property
    def relative_folder(self) -> str:
        return self._relative_folder

    @property
    def filename(self) -> str:
        if self.duplicate_number > 0:
            base, ext = os.path.splitext(os.path.basename(self.orig_name))
            filename = "%(base)s (%(duplicate)d)%(ext)s" % {
                'base': base,
                'ext': ext,
                'duplicate': self.duplicate_number + 1
            }
        else:
            filename = self.orig_name
        return self.validate_encoding(filename)

    # ----- Properties for override below -----
    @property
    def size(self) -> int:
        raise NotImplementedError

    @property
    def id(self) -> str:
        raise NotImplementedError

    @property
    def description(self) -> str:
        raise NotImplementedError

    @property
    def orig_name(self) -> str:
        raise NotImplementedError

    @property
    def create_date(self) -> datetime:
        raise NotImplementedError

    @property
    def modify_date(self) -> datetime:
        raise NotImplementedError

    @property
    def mime_type(self) -> str:
        raise NotImplementedError

    @property
    def url(self) -> str:
        raise NotImplementedError
