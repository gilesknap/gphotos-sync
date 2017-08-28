#!/usr/bin/python
# coding: utf8
import io
import mimetypes
import os.path

from googleapiclient import http
from googleapiclient.http import MediaFileUpload
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from GooglePhotosMedia import GooglePhotosMedia
from LocalMedia import LocalMedia


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
# * create local google albums as folder with links to above
# * create local albums from my original uploads via title or filename encoding

# todo keep in mind that no 'Creations' of gphotos are referenced unless
#  they appear in an album.
# one workaround is to create an album and use google photos to drop all
# creations in it. This would need redoing every so often but may be the only
# solution since it seems picassa API cannot see these otherwise
# todo - check if a search for -PANO, MOVIE.* etc works from picasa API


class GooglePhotosSync(object):
    GOOGLE_PHOTO_FOLDER_QUERY = (
        'title = "Google Photos" and "root" in parents and trashed=false')
    MEDIA_QUERY = '"%s" in parents and trashed=false '
    FOLDER_QUERY = ('title = "%s" and "%s" in parents and trashed=false'
                    ' and mimeType="application/vnd.google-apps.folder"')
    AFTER_QUERY = " and modifiedDate >= '%sT00:00:00'"
    BEFORE_QUERY = " and modifiedDate <= '%sT00:00:00'"
    PAGE_SIZE = 100
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
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

    # todo currently I am scanning from the root to include items that where
    # originally not uploaded to photos - look into using 'spaces' instead.
    def get_photos_folder_id(self):
        return "root"
        # query_results = self.googleDrive.ListFile(
        #     {"q": GooglePhotosSync.GOOGLE_PHOTO_FOLDER_QUERY}).GetList()
        # try:
        #     return query_results[0]["id"]
        # except:
        #     raise NoGooglePhotosFolderError()

    def add_date_filter(self, query_params):
        if self.args.start_date:
            query_params[
                'q'] += GooglePhotosSync.AFTER_QUERY % self.args.start_date
        elif self.args.end_date:
            query_params[
                'q'] += GooglePhotosSync.BEFORE_QUERY % self.args.end_date

    def get_remote_folder(self, parent_id, folder_name):
        this_folder_id = None
        parts = folder_name.split('/', 1)
        query_params = {
            "q": GooglePhotosSync.FOLDER_QUERY % (parts[0], parent_id)
        }

        for results in self.googleDrive.ListFile(query_params):
            this_folder_id = results[0]["id"]
        if len(parts) > 1:
            this_folder_id = self.get_remote_folder(this_folder_id, parts[1])
        return this_folder_id

    def get_remote_medias(self, folder_id, path):
        query_params = {
            "q": GooglePhotosSync.MEDIA_QUERY % folder_id,
            "maxResults": GooglePhotosSync.PAGE_SIZE,
            # "orderBy": 'createdDate desc, title'
            "orderBy": 'title'
        }
        self.add_date_filter(query_params)

        for page_results in self.googleDrive.ListFile(query_params):
            for drive_file in page_results:
                mime = drive_file["mimeType"]
                if not self.args.include_video:
                    if mime.startswith("video/"):
                        continue
                media = GooglePhotosMedia(drive_file, path)
                yield media

    def is_indexed(self, path, media):
        # todo switch to using the DB to determine next duplicate number to use
        is_indexed = False
        local_filename = os.path.join(path, media.filename)
        file_record = self.db.get_file(local_filename)
        if file_record:
            if file_record['DriveId'] == media.id:
                is_indexed = True
            else:
                media.duplicate_number += 1
                is_indexed = self.is_indexed(path, media)
        return is_indexed

    def has_local_version(self, path, media):
        # todo switch to using the DB to determine next duplicate number to use
        # todo (and can probably combine with is_indexed)
        exists = False
        local_filename = os.path.join(path, media.filename)
        local_full_path = os.path.join(self.root_folder,
                                       GooglePhotosSync.ROOT_FOLDER,
                                       local_filename)
        # recursively check if any existing duplicates have same id
        if os.path.isfile(local_full_path):
            file_record = self.db.get_file(local_filename)
            if file_record:
                if file_record['DriveId'] == media.id:
                    exists = True
                else:
                    media.duplicate_number += 1
                    exists = self.has_local_version(path, media)
            return exists
        return exists

    def download_media(self, media, path, progress_handler=None):
        local_folder = os.path.join(self.root_folder,
                                    GooglePhotosSync.ROOT_FOLDER, path)
        local_full_path = os.path.join(local_folder, media.filename)
        temp_filename = os.path.join(self.root_folder, '.temp-photo')

        if not self.args.index_only:
            if path != '' and not os.path.isdir(local_folder):
                os.makedirs(local_folder)
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

                os.rename(temp_filename, local_full_path)
                break
        else:
            print("Added %s" % local_full_path)

        self.db.put_file(media)


