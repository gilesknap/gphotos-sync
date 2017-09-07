#!/usr/bin/python
# coding: utf8
import os.path
from GoogleMedia import GoogleMedia, MediaType, MediaFolder


class DatabaseMedia(GoogleMedia):
    """A Class for instantiating a GoogleMedia object from the database

    The standard GoogleMedia attributes are presented here and are read in
    from the database using one of the two factory class methods.

    Attributes:
        Public attributes documented on their getters
    """
    MEDIA_TYPE = MediaType.DATABASE
    MEDIA_FOLDER = MediaFolder[MEDIA_TYPE]

    def __init__(self, root_folder, data_tuple):
        """
        This constructor is kept in sync with changes to the SyncFiles table
        and is the only function in this project with knowledge of how to
        interpret a select * on the table.

        :param (str) root_folder: the root of the sync folder in which
        the database file is created and below which the synced files are
        stored
        :param (tuple) data_tuple: a tuple containing a value for each
        column in the SyncFiles table.
        """
        super(DatabaseMedia, self).__init__(None, root_folder)

        if data_tuple:
            (
                self._id, self._url, local_folder,
                self._filename, self._orig_name, self._duplicate_number,
                self._date, self._checksum, self._description, self._size,
                self._create_date, _, self._media_type,
                self._sym_link
            ) = data_tuple
            self.duplicate_number = int(self.duplicate_number)
            self._media_folder = MediaFolder[self._media_type]
            media_root = os.path.join(root_folder, self._media_folder)
            self._relative_folder = os.path.relpath(local_folder,
                                                    media_root)
        else:
            # this indicates record not found
            self._id = None

    @classmethod
    def get_media_by_filename(cls, folder, name, root_folder, db):
        """
        A factory method for finding a single row in the SyncFile table by
        full path to filename and instantiate a DataBaseMedia object to
        represent it
        :param (str) folder : the root relative path to the file to find
        :param (str) name: the name of the file to find
        :param (str) root_folder: the root folder (todo to be removed)
        :param (LocalData) db: the database wrapper object
        :return:
        """
        data_tuple = db.get_file_by_path(folder, name)
        return DatabaseMedia(root_folder, data_tuple)

    @classmethod
    def get_media_by_search(cls, root_folder, db, drive_id='%', media_type='%',
                            start_date=None, end_date=None):
        """
        A factory method to find any number of rows in SyncFile and yield an
        iterator of DataBaseMedia objects representing the results
        :param root_folder:
        :param db:
        :param drive_id:
        :param media_type:
        :param start_date:
        :param end_date:
        """
        for record in db.get_files_by_search(
                drive_id, media_type, start_date, end_date):
            new_media = DatabaseMedia(root_folder, record)
            yield new_media

    # ----- GoogleMedia base class override Properties below -----
    @property
    def size(self):
        """
        The size of the file
        :return (int):
        """
        return self._size

    @property
    def checksum(self):
        """
        The md5 checksum of the file
        :return (string):
        """
        return self._checksum

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
        return self._description

    @property
    def orig_name(self):
        """
        Original filename before duplicate name handling (todo refactor so
        this is not required)
        :return (str):
        """
        return self._orig_name

    @property
    def filename(self):
        """
        filename including a suffix to make it unique if duplicates exist
        :return (str):
        """
        return self._filename

    @property
    def create_date(self):
        """
        Creation date
        :return (datetime):
        """
        return self._create_date

    @property
    def date(self):
        """
        Modify Date
        :return (datetime):
        """
        return self._date

    @property
    def mime_type(self):
        """
        Mimetype not required at present
        :return None:
        """
        raise NotImplementedError

    @property
    def url(self):
        """
        Remote url to retrieve this file from the server
        :return (string):
        """
        return self._url
