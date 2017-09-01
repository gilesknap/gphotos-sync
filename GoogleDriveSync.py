#!/usr/bin/python
# coding: utf8
import io
import os.path

from googleapiclient import http
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from GoogleDriveMedia import GoogleDriveMedia
from DatabaseMedia import DatabaseMedia
from LocalData import LocalData
import Utils


class NoGooglePhotosFolderError(Exception):
    pass


# todo the following todos to go into documentation before removing from here
#
# todo separate indexing and downloading into two separate parts
# instead of scanning through folders do:
# index all folders so we get a pathname for each folder id
#  (make this last modified dependent so that it is quick after first pass)
# get all images (with date filtering as required) and determine their path
#   from the above index
# this should make incremental passes as fast as possible
#
# todo also
# start downloading unmatched album files using the picassa download
# the final scheme will have 3 root level folders
#  drive
#  photos
#  albums
# drive is a download of all drive files (or images/videos only if required)
#   with original folder hierarchy
# photos is download of picasa items not found in drive broken down by year
#   folders (so one level folder depth only)
# albums is a set of folders named as per picasa album names containing symlinks
#   to files is the above two areas, again with year folders
# goal is to have no files in photos if possible (everything in drive)
#
# suggest the layout of folders in all 3 is actually controlled by a regex
# config item
#
# todo final breakdown will be the following phases each date gated
# NOTE: flush the DB between each step
# * index all drive folders
# * index drive files
# * index photos albums (with contents)
# * download drive files
# * download photos only files (not found in drive)
# * create local google albums as folders with links to above
# * create local albums from my original uploads via title or filename encoding

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
# todo - check if a search for -PANO, MOVIE.* etc works from picasa API


class GoogleDriveSync(object):
    GOOGLE_PHOTO_FOLDER_QUERY = (
        'title = "Google Photos" and "root" in parents and trashed=false')
    MEDIA_QUERY = '"%s" in parents and trashed=false '
    FOLDER_QUERY = ('title = "%s" and "%s" in parents and trashed=false'
                    ' and mimeType="application/vnd.google-apps.folder"')
    AFTER_QUERY = " and modifiedDate >= '%sT00:00:00'"
    BEFORE_QUERY = " and modifiedDate <= '%sT00:00:00'"
    PAGE_SIZE = 2000
    # TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    ROOT_FOLDER = "drive"

    def __init__(self, args, db=None, client_secret_file="client_secret.json",
                 credentials_json="credentials.json"):

        self.db = db
        self.args = args
        self.root_folder = args.root_folder
        self.start_folder = args.start_folder

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

    @property
    def credentials(self):
        return self.g_auth.credentials

    def get_photos_folder_id(self):
        return "root"

    def add_date_filter(self, query_params):
        if self.args.start_date:
            query_params[
                'q'] += GoogleDriveSync.AFTER_QUERY % self.args.start_date
        elif self.args.end_date:
            query_params[
                'q'] += GoogleDriveSync.BEFORE_QUERY % self.args.end_date

    def get_remote_folder(self, parent_id, folder_name):
        this_folder_id = None
        parts = folder_name.split('/', 1)
        query_params = {
            "q": GoogleDriveSync.FOLDER_QUERY % (parts[0], parent_id)
        }

        for results in self.googleDrive.ListFile(query_params):
            this_folder_id = results[0]["id"]
        if len(parts) > 1:
            this_folder_id = self.get_remote_folder(this_folder_id, parts[1])
        return this_folder_id

    def get_remote_medias(self, folder_id, path):
        query_params = {
            "q": GoogleDriveSync.MEDIA_QUERY % folder_id,
            "maxResults": GoogleDriveSync.PAGE_SIZE,
            # "orderBy": 'createdDate desc, title'
            "orderBy": 'title'
        }
        self.add_date_filter(query_params)

        results = Utils.retry(5, self.googleDrive.ListFile, query_params)

        for page_results in results:
            for drive_file in page_results:
                mime = drive_file["mimeType"]
                if not self.args.include_video:
                    if mime.startswith("video/"):
                        continue
                media = GoogleDriveMedia(path, self.root_folder,
                                         drive_file=drive_file)
                yield media

    def is_indexed(self, media):
        # todo switch to using the DB to determine next duplicate number to use
        is_indexed = False
        db_record = DatabaseMedia.get_media_by_filename(
            media.local_full_path, self.root_folder, self.db)
        if db_record.id:
            if db_record.id == media.id:
                is_indexed = True
            else:
                media.duplicate_number += 1
                is_indexed = self.is_indexed(media)
        return is_indexed

    def has_local_version(self, media):
        # todo switch to using the DB to determine next duplicate number to use
        # todo (and can probably combine with is_indexed)
        exists = False
        # recursively check if any existing duplicates have same id
        if os.path.isfile(media.local_full_path):
            db_record = DatabaseMedia.get_media_by_filename(
                media.local_full_path, self.root_folder, self.db)
            if db_record.id:
                if db_record.id == media.id:
                    exists = True
                else:
                    media.duplicate_number += 1
                    exists = self.has_local_version(media)
            return exists
        return exists

    def download_media(self, media, path, progress_handler=None):
        temp_filename = os.path.join(self.root_folder, '.temp-photo')

        if not self.args.index_only:
            if not os.path.isdir(media.local_folder):
                os.makedirs(media.local_folder)
            # retry for occasional transient quota errors - http 503
            for retry in range(10):
                try:
                    with io.open(temp_filename, 'bw') as target_file:
                        request = self.g_auth.service.files().get_media(
                            fileId=media.id)
                        download_request = http.MediaIoBaseDownload(target_file,
                                                                    request)

                        done = False
                        while not done:
                            download_status, done = \
                                download_request.next_chunk()
                            if progress_handler is not None:
                                progress_handler.update_progress(
                                    download_status)
                except Exception as e:
                    print("\nRETRYING due to", e)
                    continue

                os.rename(temp_filename, media.local_full_path)
                break
        else:
            print("Added %s" % media.local_full_path)

        try:
            media.save_to_db(self.db)
        except LocalData.DuplicateDriveIdException:
            print media.local_full_path, "is duplicate"
            # this error may just mean we already indexed on a previous pass
            #  but could also mean that there are >1 refs t this file on drive
            # in future I will separate index and download anyway and this will
            # be handled differently
            # print("WARNING, %s is a link to another file" %
            #       media.local_full_path)
            # todo create a symlink in the file system for this
            # todo put symlink field in the DB too and add this to GoogleMedia

    def scan_folder_hierarchy(self):
        print('Scanning Drive Folders ...')
        # get the root id
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
        print('resolving paths ...')
        self.recurse_paths('', root_id)
        print('Drive Folders scanned.\n')

    def recurse_paths(self, path, folder_id):
        for (fid, name) in self.db.update_drive_folder_path(path, folder_id):
            next_path = os.path.join(path, name)
            self.recurse_paths(next_path, fid)
