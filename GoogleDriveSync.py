#!/usr/bin/python
# coding: utf8
import os.path
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import ApiRequestError

from GoogleDriveMedia import GoogleDriveMedia
from DatabaseMedia import DatabaseMedia
from GoogleMedia import MediaType
from LocalData import LocalData
import Utils


class NoGooglePhotosFolderError(Exception):
    pass


# todo create local albums from my original uploads via title encoding

# NOTE: keep in mind that no 'Creations' of gphotos are referenced unless
#  they appear in an album.
# one workaround is to create an album and use google photos to drop all
# creations in it. This would need redoing every so often but may be the only
# solution since it seems picasa API cannot see these otherwise
# UPDATE - the global 'Auto Backup' album contains all files including creations
#   however the API fails at the 10000 file mark. Thus it would be possible
#   tp backup these by creating a folder and then use Auto Backup to continue
#   to save new creations (would require that they could be marked as 'do not
#   delete' once sync of deletions is implemented)

class GoogleDriveSync(object):
    GOOGLE_PHOTO_FOLDER_QUERY = (
        u'title = "Google Photos" and "root" in parents and trashed=false')
    FOLDER_QUERY = u'title = "%s" and "%s" in parents and trashed=false and ' \
                   u'mimeType="application/vnd.google-apps.folder"'
    PHOTO_QUERY = u"mimeType contains 'image/' and trashed=false"
    VIDEO_QUERY = u"(mimeType contains 'image/' or mimeType contains " \
                  u"'video/') and trashed=false"
    AFTER_QUERY = u" and modifiedDate >= '{}T00:00:00'"
    BEFORE_QUERY = u" and modifiedDate <= '{}T00:00:00'"
    FILENAME_QUERY = u'title contains "{}" and trashed=false'
    PAGE_SIZE = 500

    def __init__(self, root_folder, db,
                 client_secret_file="client_secret.json",
                 credentials_json="credentials.json"):
        """
        :param (str) root_folder:
        :param (LocalData) db:
        :param (str) client_secret_file:
        :param (str) credentials_json:
        """
        self._db = db
        self._root_folder = root_folder

        self._g_auth = GoogleAuth()
        self._g_auth.settings["client_config_file"] = client_secret_file
        self._g_auth.settings["save_credentials_file"] = credentials_json
        self._g_auth.settings["save_credentials"] = True
        self._g_auth.settings["save_credentials_backend"] = "file"
        self._g_auth.settings["get_refresh_token"] = True
        self._g_auth.CommandLineAuth()
        self._googleDrive = GoogleDrive(self._g_auth)
        self._latest_download = Utils.minimum_date()
        # public members to be set after init
        self.folderPaths = {}
        self.startDate = None
        self.endDate = None
        self.driveFileName = None
        self.quiet = False
        self.allDrive = False
        self.includeVideo = False

    @property
    def credentials(self):
        return self._g_auth.credentials

    @property
    def latest_download(self):
        return self._latest_download

    def scan_folder_hierarchy(self):
        print('\nIndexing Drive Folders ...')
        # get the root id
        root_id = None
        query_params = {'q': self.GOOGLE_PHOTO_FOLDER_QUERY}
        results = Utils.retry(5, self._googleDrive.ListFile, query_params)
        for page_results in results:
            for drive_file in page_results:
                if self.allDrive:
                    root_id = drive_file['parents'][0]['id']
                else:
                    root_id = drive_file['id']

        # now get all folders
        q = 'trashed=false and mimeType="application/vnd.google-apps.folder"'
        query_params = {
            "q": q,
            "maxResults": GoogleDriveSync.PAGE_SIZE,
            "orderBy": 'modifiedDate'
        }

        results = Utils.retry(5, self._googleDrive.ListFile, query_params)
        for page_results in results:
            for drive_file in page_results:
                if len(drive_file['parents']) > 0:
                    parent_id = drive_file['parents'][0]['id']
                else:
                    parent_id = None
                self._db.put_drive_folder(drive_file['id'], parent_id,
                                          drive_file['title'])
        print('Resolving paths ...')
        self.folderPaths[root_id] = ''
        self.recurse_paths('', root_id)
        print('Drive Folders scanned.\n')

    def recurse_paths(self, path, folder_id):
        self.folderPaths[folder_id] = path
        for (fid, name) in self._db.update_drive_folder_path(path, folder_id):
            next_path = os.path.join(path, name)
            self.recurse_paths(next_path, fid)

    # todo this will currently do nothing unless using --flush-db
    # need to look at drive changes api if we want to support deletes and
    # incremental backup.
    def check_for_removed(self):
        # note for partial scans using date filters this is still OK because
        # for a file to exist it must have been indexed in a previous scan
        print('\nFinding deleted media ...')
        top_dir = os.path.join(self._root_folder, GoogleDriveMedia.MEDIA_FOLDER)
        for (dir_name, _, file_names) in os.walk(top_dir):
            for file_name in file_names:
                file_id = self._db.get_file_by_path(dir_name, file_name)
                if not file_id:
                    name = os.path.join(dir_name, file_name)
                    # os.remove(name)
                    print(u"{} deleted".format(name))

    def index_drive_media(self):
        print('\nIndexing Drive Files ...')

        if self.includeVideo:
            q = self.VIDEO_QUERY
        else:
            q = self.PHOTO_QUERY

        if self.driveFileName:
            q = self.FILENAME_QUERY.format(self.driveFileName)
        if self.startDate:
            q += self.AFTER_QUERY.format(self.startDate)
        else:
            # setup for incremental backup
            if not self.driveFileName:
                (self._latest_download, _) = self._db.get_scan_dates()
                if not self._latest_download:
                    self._latest_download = Utils.minimum_date()
                if self._latest_download:
                    s = Utils.date_to_string(self._latest_download, True)
                    q += self.AFTER_QUERY.format(s)
        if self.endDate:
            q += self.BEFORE_QUERY.format(self.endDate)

        query_params = {
            "q": q,
            "maxResults": GoogleDriveSync.PAGE_SIZE,
            "orderBy": 'modifiedDate'
        }
        if not self.allDrive:
            query_params['spaces'] = 'photos'

        results = self._googleDrive.ListFile(query_params)
        n = 0
        try:
            for page_results in Utils.retry_i(5, results):
                for drive_file in page_results:
                    if not drive_file:
                        continue
                    media = GoogleDriveMedia(self.folderPaths,
                                             self._root_folder, drive_file)
                    if not media.is_indexed(self._db):
                        n += 1
                        if not self.quiet:
                            print(u"Added {} {}".format(n,
                                                        media.local_full_path))
                            media.save_to_db(self._db)
                        if media.modified_date > self._latest_download:
                            self._latest_download = media.modified_date
        finally:
            # store latest date for incremental backup only if scanning all
            if not (self.driveFileName or self.startDate):
                self._db.set_scan_dates(drive_last_date=self._latest_download)

    # todo set file dates as per downloaded media
    def download_drive_media(self):
        print('\nDownloading Drive Files ...')
        # noinspection PyTypeChecker
        for media in DatabaseMedia.get_media_by_search(
                self._root_folder, self._db, media_type=MediaType.DRIVE,
                start_date=self.startDate, end_date=self.endDate):
            if os.path.exists(media.local_full_path):
                continue

            if not os.path.isdir(media.local_folder):
                os.makedirs(media.local_folder)
            temp_filename = os.path.join(self._root_folder, '.temp-photo')

            print (u'downloading {} ...'.format(media.local_full_path))
            f = self._googleDrive.CreateFile({'id': media.id})
            try:
                Utils.retry(10, f.GetContentFile, temp_filename)

                os.rename(temp_filename, media.local_full_path)
            except ApiRequestError:
                print(u'DOWNLOAD FAILURE for {}'.format(media.local_full_path))
