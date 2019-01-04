#!/usr/bin/env python2
# coding: utf8
import re

from . import Utils
from .GoogleMedia import GoogleMedia, MediaType, MediaFolder
from enum import IntEnum


class FileType(IntEnum):
    Other = 0
    Video = 1
    Image = 2


class GooglePhotosMedia(GoogleMedia):
    MEDIA_TYPE = MediaType.PHOTOS
    MEDIA_FOLDER = MediaFolder[MEDIA_TYPE]
    EXTERNAL_LINKS = 'External-Links'

    # todo passing folder_paths (and root_folder) here seems messy, refactor?
    def __init__(self, path, media_json):
        self.__media_json = media_json
        self.__path = path
        self.__type = FileType.Other
        if self.mime_type.startswith('video'):
            self.__type = FileType.Video
            self.__media_meta = media_json.get('mediaMetadata').get('video')
        elif self.mime_type.startswith('image'):
            self.__type = FileType.Image
            self.__media_meta = media_json.get('mediaMetadata').get('photo')
        super(GooglePhotosMedia, self).__init__(path, '/tmp')

    # ----- override Properties below -----
    @property
    def size(self):
        return 0

    @property
    def checksum(self):
        return "none"

    @property
    def id(self):
        return self.__media_json["id"]

    @property
    def description(self):
        try:
            return self.validate_encoding(
                self.__media_json["description"])
        except KeyError:
            return ''

    @property
    def orig_name(self):
        try:
            name = self.__media_json["filename"]
        except KeyError:
            name = ''
        return self.validate_encoding(name)

    @property
    def create_date(self):
        try:
            create_date = self.__media_json["mediaMetadata"].get("creationTime")
            photo_date = Utils.string_to_date(create_date)
        except (KeyError, ValueError):
            photo_date = Utils.minimum_date()

        return photo_date

    @property
    def modify_date(self):
        date = Utils.minimum_date()
        return date

    @property
    def mime_type(self):
        return self.__media_json['mimeType']

    @property
    def url(self):
        return self.__media_json['productUrl']

    # ----- Derived class custom properties below -----
    @property
    def parent_id(self):
        return 0

    @property
    def camera_owner(self):
        return "none"

    @property
    def camera_model(self):
        try:
            camera_model = self.__media_meta['cameraModel']
        except KeyError:
            camera_model = None
        return camera_model
