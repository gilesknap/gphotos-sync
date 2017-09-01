#!/usr/bin/python
# coding: utf8
import os.path
from datetime import datetime
from GoogleMedia import GoogleMedia, MediaType, MediaFolder


class PicasaMedia(GoogleMedia):
    MEDIA_TYPE = MediaType.PICASA
    MEDIA_FOLDER = MediaFolder[MEDIA_TYPE]

    def __init__(self, relative_folder, root_folder, photo_xml=None):
        super(PicasaMedia, self).__init__(relative_folder, root_folder)
        self.__photo_xml = photo_xml
        self._relative_folder = self.define_path()

    @classmethod
    def time_from_timestamp(cls, time_secs, hour_offset=0):
        date = datetime.fromtimestamp(
            int(time_secs) / 1000 - 3600 * hour_offset)
        return date

    @classmethod
    def parse_date_string(cls, date_string):
        # some times are ucase T and non zero millisecs - normalize
        date = datetime.strptime(date_string.upper()[:-4],
                                 "%Y-%m-%dT%H:%M:%S.")
        return date

    def define_path(self):
        return self.date.strftime('%Y/%m')

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
        # NOTE: picasa API returns no description
        return self.__photo_xml.title.text

    @property
    def orig_name(self):
        return self.__photo_xml.title.text

    @property
    def create_date(self):
        return self.parse_date_string(self.__photo_xml.published.text)

    @property
    def date(self):
        try:
            return self.time_from_timestamp(self.__photo_xml.exif.time.text, 0)
        except AttributeError as e:
            return self.parse_date_string(self.__photo_xml.updated.text)

    @property
    def mime_type(self):
        return self.__photo_xml.metadata[u'mimeType']
