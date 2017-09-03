#!/usr/bin/python
# coding: utf8
import io
import os.path

from googleapiclient import http
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from GoogleDriveMedia import GoogleDriveMedia
from DatabaseMedia import DatabaseMedia
from GoogleMedia import MediaType
from ProgressHandler import ProgressHandler
import Utils


class NoGooglePhotosFolderError(Exception):
    pass


# todo create local albums from my original uploads via title encoding

# todo keep in mind that no 'Creations' of gphotos are referenced unless
#  they appear in an album.
# one workaround is to create an album and use google photos to drop all
# creations in it. This would need redoing every so often but may be the only
# solution since it seems picassa API cannot see these otherwise
# UDATE - the global 'Auto Backup' album contains all files including creations
#   however the API fails at the 10000 file mark. Thus it would be possible
#   tp backup these by creating a folder and then use Auto Backup to continue
#   to save new creations (would require that they could be marked as 'do not
#   delete' once sync of deletions is implemented)

class GoogleDriveSync(object):
    GOOGLE_PHOTO_FOLDER_QUERY = (
        'title = "Google Photos" and "root" in parents and trashed=false')
    FOLDER_QUERY = ('title = "%s" and "%s" in parents and trashed=false'
                    ' and mimeType="application/vnd.google-apps.folder"')
    MEDIA_QUERY = "(mimeType contains 'image/' or mimeType contains 'video/')"
    AFTER_QUERY = " and modifiedDate >= '{}T00:00:00'"
    BEFORE_QUERY = " and modifiedDate <= '{}T00:00:00'"
    PAGE_SIZE = 500
    ROOT_FOLDER = "drive"

    def __init__(self, args, db=None, client_secret_file="client_secret.json",
                 credentials_json="credentials.json"):
        self.db = db
        self.args = args
        self.root_folder = args.root_folder

        if args.new_token:
            os.remove(credentials_json)
        self.g_auth = GoogleAuth()
        self.g_auth.settings["client_config_file"] = client_secret_file
        self.g_auth.settings["save_credentials_file"] = credentials_json
        self.g_auth.settings["save_credentials"] = True
        self.g_auth.settings["save_credentials_backend"] = "file"
        self.g_auth.settings["get_refresh_token"] = True
        self.g_auth.CommandLineAuth()
        self.googleDrive = GoogleDrive(self.g_auth)
        self.matchingRemotesCount = 0
        self.folder_paths = {}

    @property
    def credentials(self):
        return self.g_auth.credentials

    def scan_folder_hierarchy(self):
        print('\nIndexing Drive Folders ...')
        # get the root id
        root_id = None
        query_params = {'q': self.GOOGLE_PHOTO_FOLDER_QUERY}
        results = Utils.retry(5, self.googleDrive.ListFile, query_params)
        for page_results in results:
            for drive_file in page_results:
                root_id = drive_file['parents'][0]['id']

        # now get all folders
        q = 'trashed=false and mimeType="application/vnd.google-apps.folder"'
        query_params = {
            "q": q,
            "maxResults": GoogleDriveSync.PAGE_SIZE,
            "orderBy": 'modifiedDate'
        }

        results = Utils.retry(5, self.googleDrive.ListFile, query_params)
        for page_results in results:
            for drive_file in page_results:
                if len(drive_file['parents']) > 0:
                    parent_id = drive_file['parents'][0]['id']
                else:
                    parent_id = None
                self.db.put_drive_folder(drive_file['id'], parent_id,
                                         drive_file['title'])
        print('Resolving paths ...')
        self.folder_paths[root_id] = ''
        self.recurse_paths('', root_id)
        print('Drive Folders scanned.\n')

    def recurse_paths(self, path, folder_id):
        self.folder_paths[folder_id] = path
        for (fid, name) in self.db.update_drive_folder_path(path, folder_id):
            next_path = os.path.join(path, name)
            self.recurse_paths(next_path, fid)

    def index_drive_media(self):
        print('\nIndexing Drive Files ...')
        q = "(mimeType contains 'image/' or mimeType contains 'video/')"
        if self.args.start_date:
            q += self.AFTER_QUERY.format(self.args.start_date)
        if self.args.end_date:
            q += self.BEFORE_QUERY.format(self.args.end_date)

        query_params = {
            "q": q,
            "maxResults": GoogleDriveSync.PAGE_SIZE,
            "orderBy": 'modifiedDate'
        }

        results = self.googleDrive.ListFile(query_params)
        n = 0
        for page_results in Utils.retry_i(5, results):
            for drive_file in page_results:
                media = GoogleDriveMedia(self.folder_paths,
                                         self.args.root_folder, drive_file)
                if not media.is_indexed(self.db):
                    n += 1
                    print(u"Added {} {}".format(n, media.local_full_path))
                    media.save_to_db(self.db)

    def download_drive_media(self):
        print('\nDownloading Drive Files ...')
        for media in DatabaseMedia.get_media_by_search(
                self.args.root_folder, self.db, media_type=MediaType.DRIVE,
                start_date=self.args.start_date, end_date=self.args.end_date):
            if os.path.exists(media.local_full_path):
                continue

            if not os.path.isdir(media.local_folder):
                os.makedirs(media.local_folder)
            temp_filename = os.path.join(self.root_folder, '.temp-photo')

            if self.args.quiet:
                progress_handler = None
            else:
                progress_handler = ProgressHandler(media)

            with io.open(temp_filename, 'bw') as target_file:
                request = self.g_auth.service.files().get_media(
                    fileId=media.id)
                download_request = http.MediaIoBaseDownload(target_file,
                                                            request)

                done = False
                while not done:
                    download_status, done = \
                        Utils.retry(10, download_request.next_chunk)
                    if progress_handler is not None:
                        progress_handler.update_progress(
                            download_status)

                os.rename(temp_filename, media.local_full_path)
