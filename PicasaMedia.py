#!/usr/bin/python
# coding: utf8
import mimetypes

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
        return Utils.safe_str_time(self.date, '%Y/%m')

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
        return Utils.string_to_date(self.__photo_xml.published.text)

    @property
    def date(self):
        try:
            return Utils.timestamp_to_date(self.__photo_xml.exif.time.text, 0)
        except AttributeError:
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
            # todo this is probably not a complete list
            suffix = self.orig_name.lower().split('.')[-1]
            if suffix == 'm4v' \
                    or suffix == '3gp' or suffix == 'avi':
                return 'video/dummy'
            else:
                return 'unknown'
