#!/usr/bin/env python3
# coding: utf8
from .BaseMedia import BaseMedia


class GoogleAlbumMedia(BaseMedia):
    def __init__(self, media_json):
        self.__media_json = media_json
        super(GoogleAlbumMedia, self).__init__()

    # ----- override Properties below -----
    @property
    def size(self):
        try:
            return int(self.__media_json["mediaItemsCount"])
        except KeyError:
            return 0

    @property
    def id(self):
        return self.__media_json["id"]

    @property
    def description(self):
        return self.orig_name

    @property
    def orig_name(self) -> str:
        try:
            return self.__media_json["title"]
        except KeyError:
            return "none"

    @property
    def create_date(self):
        return None

    @property
    def modify_date(self):
        return None

    @property
    def mime_type(self):
        return "none"

    @property
    def url(self):
        return self.__media_json['productUrl']
