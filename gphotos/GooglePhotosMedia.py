#!/usr/bin/env python3
# coding: utf8

from . import Utils
from .BaseMedia import BaseMedia


class GooglePhotosMedia(BaseMedia):
    def __init__(self, media_json):
        self.__media_json = media_json
        self.__path = None
        super(GooglePhotosMedia, self).__init__()
        if self.is_video():
            self.__media_meta = None
            # self.__media_meta = media_json.get('mediaMetadata').get('video')
        else:
            self.__media_meta = media_json.get('mediaMetadata').get('photo')

    # ----- override Properties below -----
    @property
    def size(self):
        return 0

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

    @property
    def camera_owner(self):
        return "none"

    @property
    def camera_model(self):
        camera_model = None
        try:
            camera_model = self.__media_meta['cameraModel']
        except (KeyError, AttributeError):
            pass
        return camera_model
