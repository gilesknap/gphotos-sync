#!/usr/bin/env python2
# coding: utf8
import os.path

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import ApiRequestError
from pydrive.settings import InvalidConfigError

import Utils
from GoogleDriveMedia import GoogleDriveMedia
from GoogleMedia import MediaType
from LocalData import LocalData
from gphotos.DatabaseMedia import DatabaseMedia
import logging

class NoGooglePhotosFolderError(Exception):
    pass


log = logging.getLogger('gphotos.drive')


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
    PAGE_SIZE = 100

    def __init__(self, root_folder, db,
                 client_secret_file="client_secret.json",
                 credentials_json="credentials.json",
                 no_browser=False):
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
        self._g_auth.settings["oauth_scope"] = [
            'https://www.googleapis.com/auth/drive.photos.readonly',
            'https://picasaweb.google.com/data/',
            'https://www.googleapis.com/auth/drive']
        try:
            if no_browser:
                self._g_auth.CommandLineAuth()
            else:
                self._g_auth.LocalWebserverAuth()
        except InvalidConfigError:
            log.error(u"No client secrets file found.\nPlease see "
                      u"https://github.com/gilesknap/gphotos-sync#install"
                      u"-and-configure")
            exit(1)

        self._googleDrive = GoogleDrive(self._g_auth)
        self._latest_download = Utils.minimum_date()
        # public members to be set after init
        self.folderPaths = {}
        self.startDate = None
        self.endDate = None
        self.driveFileName = None
        self.allDrive = False
        self.includeVideo = False

    @property
    def credentials(self):
        return self._g_auth.credentials

    @property
    def latest_download(self):
        return self._latest_download

    def scan_folder_hierarchy(self):
        log.info(u'Indexing Drive Folders ...')
        # get the root id
        # is this really the only way?- Find all items with root as parent
        # then ask the first of these for its parent id !!??
        root_id = None
        query_params = {'q': '"root" in parents'}
        results = Utils.retry(5, self._googleDrive.ListFile, query_params)
        for page_results in results:
            for drive_file in page_results:
                root_id = drive_file['parents'][0]['id']
                log.debug('root_id = %s', root_id)
                break
            break

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
        log.info(u'Resolving paths ...')
        self.recurse_paths('', root_id)
        if len(self.folderPaths) == 1:
            raise ValueError(
                "No folders found. Please enable Google Photos in Google "
                "drive (see https://support.google.com/photos/answer/6156103"
                "). Or use one of the options --all-drive --skip-drive.")
        log.info(u'Drive Folders scanned.')

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
        log.info(u'Finding deleted media ...')
        top_dir = os.path.join(self._root_folder, GoogleDriveMedia.MEDIA_FOLDER)
        for (dir_name, _, file_names) in os.walk(top_dir):
            for file_name in file_names:
                file_row = self._db.get_file_by_path(dir_name, file_name)
                if not file_row:
                    name = os.path.join(dir_name, file_name)
                    os.remove(name)
                    log.warning("%s deleted", name)

    def write_media(self, media, update=True):
        media.save_to_db(self._db, update)
        if media.modify_date > self._latest_download:
            self._latest_download = media.modify_date

    PHOTO_QUERY = u"mimeType contains 'image/' and trashed=false"
    VIDEO_QUERY = u"(mimeType contains 'image/' or mimeType contains " \
                  u"'video/') and trashed=false"
    AFTER_QUERY = u" and modifiedDate >= '{}T00:00:00'"
    BEFORE_QUERY = u" and modifiedDate <= '{}T00:00:00'"
    FILENAME_QUERY = u'title contains "{}" and trashed=false'

    # these are the queries I'd like to use but they are for drive api v3
    AFTER_QUERY2 = u" and (modifiedTime >= '{0}T00:00:00' or " \
                   u"createdTime >= '{0}T00:00:00') "
    BEFORE_QUERY2 = u" and (modifiedTime <= '{0}T00:00:00' or " \
                    u"createdTime <= '{0}T00:00:00') "

    def index_drive_media(self):
        log.info(u'Indexing Drive Files ...')

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
                else:
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
                    media = GoogleDriveMedia(self.folderPaths,
                                             self._root_folder, drive_file)
                    row = media.is_indexed(self._db)
                    if not row:
                        n += 1
                        log.info(u"Added %d %s", n, media.local_full_path)
                        self.write_media(media, False)
                        if n % 1000 == 0:
                            self._db.store()
                    elif media.modify_date > row.ModifyDate:
                        log.info(u"Updated %d %s", n, media.local_full_path)
                        self.write_media(media, True)
        finally:
            # store latest date for incremental backup only if scanning all
            if not (self.driveFileName or self.startDate):
                self._db.set_scan_dates(drive_last_date=self._latest_download)

    def download_drive_media(self):
        log.info(u'Downloading Drive Files ...')
        # noinspection PyTypeChecker
        for media in DatabaseMedia.get_media_by_search(
                self._root_folder, self._db, media_type=MediaType.DRIVE,
                start_date=self.startDate, end_date=self.endDate):
            if os.path.exists(media.local_full_path):
                if Utils.to_timestamp(media.modify_date) > \
                        os.path.getctime(media.local_full_path):
                    log.warning(u'{} was modified'.format(
                        media.local_full_path))
                else:
                    continue

            if not os.path.isdir(media.local_folder):
                os.makedirs(media.local_folder)
            temp_filename = os.path.join(self._root_folder, '.temp-photo')

            log.info(u'downloading {} ...'.format(media.local_full_path))
            f = self._googleDrive.CreateFile({'id': media.id})
            try:
                Utils.retry(10, f.GetContentFile, temp_filename)
                if os.path.exists(media.local_full_path):
                    os.remove(media.local_full_path)
                os.rename(temp_filename, media.local_full_path)
                # set the access date to create date since there is nowhere
                # else to put it on linux (and is useful for debugging)
                os.utime(media.local_full_path,
                         (Utils.to_timestamp(media.modify_date),
                          Utils.to_timestamp(media.create_date)))
            except ApiRequestError:
                log.error(u'DOWNLOAD FAILURE for {}'.format(
                    media.local_full_path))
