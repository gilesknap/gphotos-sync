#!/usr/bin/python
# coding: utf8
import os.path
from GoogleMedia import GoogleMedia, MediaType, MediaFolder


class DatabaseMedia(GoogleMedia):
    MEDIA_TYPE = MediaType.DATABASE
    MEDIA_FOLDER = MediaFolder[MEDIA_TYPE]

    def __init__(self, root_folder, data_tuple):
        super(DatabaseMedia, self).__init__(None, root_folder)

        if data_tuple:
            (
                self._id, self._url, local_folder,
                self._filename, self.orig_name, self._duplicate_number,
                self._date, self._checksum, self._description, self._size,
                self._create_date, _, self._media_type,
                self._sym_link
            ) = data_tuple
            self.duplicate_number = int(self.duplicate_number)
            self.media_folder = MediaFolder[self._media_type]
            media_root = os.path.join(root_folder, self.media_folder)
            self._relative_folder = os.path.relpath(local_folder,
                                                    media_root)
        else:
            # this indicates record not found
            self._id = None

    @classmethod
    def get_media_by_filename(cls, local_full_path, root_folder, db):
        data_tuple = db.get_file_by_path(local_full_path)
        return DatabaseMedia(root_folder, data_tuple)

    @classmethod
    def get_media_by_search(cls, root_folder, db, drive_id='%', media_type='%',
                            start_date=None, end_date=None):
        for record in db.get_files_by_search(
                drive_id, media_type, start_date, end_date):
            new_media = DatabaseMedia(root_folder, record)
            yield new_media

    # ----- override Properties below -----
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
    def date(self):
        return self._date

    @property
    def mime_type(self):
        raise NotImplementedError

    @property
    def url(self):
        return self._url