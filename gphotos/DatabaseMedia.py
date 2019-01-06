#!/usr/bin/env python2
# coding: utf8
import os.path
from datetime import datetime

from .GoogleMedia import GoogleMedia, MediaType
from .LocalData import LocalData


class DatabaseMedia(GoogleMedia):
    """A Class for instantiating a GoogleMedia object from the database

    The standard GoogleMedia attributes are presented here and are read in
    from the database using one of the two factory class methods.

    Attributes:
        _id (str): remote identifier from picasa or drive
        _filename (str):
        _orig_name (str):
        _duplicate_number (int):
        _date (datetime):
        _checksum (str):
        _description (str):
        _size (int):
        _create_date (datetime):
        _media_type (int):
        _sym_link (int):

    """
    MEDIA_TYPE = MediaType.DATABASE

    # noinspection PyUnresolvedReferences
    def __init__(self, row):
        """
        This constructor is kept in sync with changes to the SyncFiles table

        :param (str) root_folder: the root of the sync folder in which
        the database file is created and below which the synced files are
        stored
        :param (LocalData.SyncRow) row: a tuple containing a value for each
        column in the SyncFiles table.
        """
        super(DatabaseMedia, self).__init__()

        if row:
            self._id = row.RemoteId
            self._url = row.Url
            self._relative_folder = row.Path
            self._filename = row.FileName
            self._orig_name = row.OrigFileName
            self._duplicate_number = row.DuplicateNo
            self._media_type = row.MediaType
            self._size = row.FileSize
            self._mimeType = row.MimeType
            self._description = row.Description
            self._date = row.ModifyDate
            self._create_date = row.CreateDate
            self._sym_link = row.SymLink = None

            self.duplicate_number = int(self.duplicate_number)
        else:
            # this indicates record not found
            self._id = None

    @classmethod
    def get_media_by_filename(cls, folder, name, db):
        """
        A factory method for finding a single row in the SyncFile table by
        full path to filename and instantiate a DataBaseMedia object to
        represent it
        :param (str) folder : the root relative path to the file to find
        :param (str) name: the name of the file to find
        :param (LocalData) db: the database wrapper object
        :return:
        """
        data_tuple = db.get_file_by_path(folder, name)
        return DatabaseMedia(data_tuple)

    @classmethod
    def get_media_by_search(cls, db, remote_id='%', media_type='%',
                            start_date=None, end_date=None, skip_linked=False):
        """
        A factory method to find any number of rows in SyncFile and yield an
        iterator of DataBaseMedia objects representing the results
        :param (LocalData) db: the database wrapper object
        :param (str) remote_id: optional id of row to find
        :param (int) media_type: optional type of rows to find
        :param (datetime) start_date: optional date filter
        :param (datetime) end_date: optional date filter
        :param (bool) skip_linked: skip files with non-null SymLink
        :returns (GoogleMedia): yields GoogleMedia object filled from database
        """
        for record in db.get_files_by_search(
                remote_id, media_type, start_date, end_date, skip_linked):
            new_media = DatabaseMedia(record)
            yield new_media

    # ----- GoogleMedia base class override Properties below -----
    @property
    def size(self):
        """
        The size of the file
        :return int:
        """
        return self._size

    @property
    def mime_type(self):
        return self._mimeType

    @property
    def id(self):
        """
        The remote id of the server copy of the file
        :return (str):
        """
        return self._id

    @property
    def description(self):
        """
        The description of the file
        :return (str):
        """
        return self.validate_encoding(self._description)

    @property
    def orig_name(self):
        """
        Original filename before duplicate name handling (todo refactor so
        this is not required)
        :return (str):
        """
        return self.validate_encoding(self._orig_name)

    @property
    def filename(self):
        """
        filename including a suffix to make it unique if duplicates exist
        :return (str):
        """
        return self.validate_encoding(self._filename)

    @property
    def create_date(self):
        """
        Creation date
        :return (datetime):
        """
        return self._create_date

    @property
    def modify_date(self):
        """
        Modify Date
        :return (datetime):
        """
        return self._date

    @property
    def url(self):
        """
        Remote url to retrieve this file from the server
        :return (string):
        """
        return self._url
