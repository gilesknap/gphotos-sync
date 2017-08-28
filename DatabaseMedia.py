#!/usr/bin/python
# coding: utf8
import os.path
from datetime import datetime
from time import gmtime, strftime
from GoogleMedia import GoogleMedia, MediaType


class DatabaseMedia(GoogleMedia):
    MEDIA_FOLDER = ""
    MEDIA_TYPE = MediaType.DATABASE

    def __init__(self, root_path, local_full_path, db, **k_args):
        super(DatabaseMedia, self).__init__(None, root_path)

        media_root = os.path.join(root_path, self.media_folder)
        local_folder = os.path.dirname(local_full_path)
        self.__relative_path = os.path.relpath(local_folder,
                                               media_root)

        data_tuple = db.get_file(local_full_path)
        if data_tuple:
            (
                self._id, self._orig_name, local_folder,
                self._filename, self._duplicate_number, self._date,
                self._checksum, self._description, self._size,
                self._create_date, _, self._media_type
            ) = data_tuple

            # todo this is clumsy and repeats the derived class info
            # probably just need to add a global Enum for the media folders
            if self._media_type == MediaType.PICASA:
                self.media_folder = 'picasa'
            elif self._media_type == MediaType.DRIVE:
                self.media_folder = 'drive'
            elif self._media_type == MediaType.ALBUM_LINK:
                self.media_folder = 'albums'
        else:
            # use this to indicate record not found
            self._id = None

    @property
    def duplicate_number(self):
        return self.__duplicate_number

    @property
    def date(self):
        return self._date

    @property
    def size(self):
        return self._size

    @property
    def checksum(self):
        return self._checksum

    @property
    def id(self):
        return self._id

    @property
    def description(self):
        return self._description

    @property
    def orig_name(self):
        return self._orig_name

    @property
    def filename(self):
        return self._filename

    @property
    def create_date(self):
        return self._create_date

    @property
    def mime_type(self):
        raise NotImplementedError
