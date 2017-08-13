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

    def get_photos_folder_id(self):
        query_results = self.googleDrive.ListFile(
            {"q": GooglePhotosSync.GOOGLE_PHOTO_FOLDER_QUERY}).GetList()
        try:
            return query_results[0]["id"]
        except:
            raise NoGooglePhotosFolderError()

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
                if not self.args.include_video:
                    if drive_file["mimeType"].startswith("video/"):
                        continue
                media = GooglePhotosMedia(drive_file, path)
                yield media

    def get_remote_media_by_name(self, filename):
        google_photos_folder_id = self.get_photos_folder_id()
        query_params = {
            "q": 'title = "%s" and "%s" in parents and trashed=false' %
                 (filename, google_photos_folder_id)
        }
        found_media = self.googleDrive.ListFile(query_params).GetList()
        # todo this function will fail since it cant find jpg in the root
        # typically, when fixing this make sure we get path set in media obj
        return GooglePhotosMedia(found_media[0]) if found_media else None

    def get_local_medias(self):
        for directory, _, files in os.walk(self.start_folder):
            for filename in files:
                media_path = os.path.join(directory, filename)
                mime_type, _ = mimetypes.guess_type(media_path)
                if mime_type and mime_type.startswith('image/'):
                    yield LocalMedia(media_path)

    def is_indexed(self, path, media):
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
        local_filename = os.path.join(path, media.filename)
        local_full_path = os.path.join(self.root_folder, local_filename)
        # recursively check if any existing duplicates have same id
        if os.path.isfile(local_full_path):
            media_record = self.db.get_file(local_filename)
            # todo this is broken since path and name now in separate columns
            # fix by returning a GooglePhotosMedia from get_file
            if media_record and media_record['LocalFileName'] == local_filename:
                return True
            else:
                media.duplicate_number += 1
                return self.has_local_version(path, media)
        return False

    def download_media(self, media, path, progress_handler=None):
        if path != '' and not os.path.isdir(path):
            os.makedirs(path)

        target_filename = os.path.join(path, media.filename)
        local_full_path = os.path.join(self.root_folder, target_filename)
        temp_filename = os.path.join(self.root_folder, path, '.temp-photo')

        if not self.args.index_only:
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

        # todo use root relative path for portability
        # assert ('2013-01-04 14.33.44.jpg' != media.filename)
        self.db.put_file(media)
        return target_filename

    def upload_media(self, local_media, progress_handler=None):

        remote_media = self.get_remote_media_by_name(local_media.filename)

        media_body = MediaFileUpload(local_media.path, resumable=True)

        if remote_media:
            upload_request = self.g_auth.service.files().update(
                fileId=remote_media.id,
                body=remote_media.drive_file,
                newRevision=True,
                media_body=media_body)
        else:
            body = {
                'title': local_media.filename,
                'mimetype': local_media.mimetype
            }
            upload_request = self.g_auth.service.files().insert(
                body=body,
                media_body=media_body)

        done = False
        while not done:
            upload_status, done = upload_request.next_chunk()
            if progress_handler is not None:
                progress_handler.update_progress(upload_status)
