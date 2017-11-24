#!/usr/bin/python
# coding: utf8
import mimetypes
import os

import Utils
from GoogleMedia import GoogleMedia, MediaType, MediaFolder


class PicasaMedia(GoogleMedia):
    MEDIA_TYPE = MediaType.PICASA
    MEDIA_FOLDER = MediaFolder[MEDIA_TYPE]

    def __init__(self, relative_folder, root_folder, photo_xml=None):
        super(PicasaMedia, self).__init__(relative_folder, root_folder)
        self.__photo_xml = photo_xml
        self._relative_folder = self.define_path()

    def define_path(self):
        year = Utils.safe_str_time(self.create_date, '%Y')
        month = Utils.safe_str_time(self.create_date, '%m')
        return os.path.join(year, month)

    # ----- override Properties below -----
    @property
    def url(self):
        if self.__photo_xml.media.content:
            high_res_content = self.__photo_xml.media.content[-1]
            if high_res_content.type.startswith('video'):
                if high_res_content.url:
                    return high_res_content.url
        return self.__photo_xml.content.src

    @property
    def size(self):
        return int(self.__photo_xml.size.text)

    @property
    def checksum(self):
        # NOTE: picasa API returns empty checksum
        return self.__photo_xml.checksum.text

    @property
    def id(self):
        return self.__photo_xml.gphoto_id.text

    @property
    def description(self):
        # NOTE: picasa API returns empty description field, use title
        return self.validate_encoding(
            self.__photo_xml.title.text)

    @property
    def orig_name(self):
        return self.validate_encoding(self.__photo_xml.title.text)

    @property
    def create_date(self):
        try:
            return Utils.timestamp_to_date(self.__photo_xml.exif.time.text, 0)
        except AttributeError:
            return Utils.timestamp_to_date(self.__photo_xml.timestamp.text)

    @property
    def modify_date(self):
            if self.mime_type.startswith('video'):
                # for some reason the updated field is weird in picasa API
                # use created here instead - this means edits to videos in
                # picasa won't get backed up
                return Utils.timestamp_to_date(self.__photo_xml.timestamp.text)
            else:
                return Utils.string_to_date(self.__photo_xml.updated.text)

    @property
    def mime_type(self):
        try:
            return self.__photo_xml.metadata[u'mimeType'].text
        except AttributeError:
            mime_type, _ = mimetypes.guess_type(self.orig_name)
            if mime_type:
                return mime_type
            # a bit of a hack here - picasa does not reveal the mime_type
            # and guess_type does not work on all video extensions
            suffix = self.orig_name.lower().split('.')[-1]
            if suffix == 'm4v' \
                    or suffix == '3gp' or suffix == 'avi':
                return 'video/dummy'
            else:
                return 'unknown'
