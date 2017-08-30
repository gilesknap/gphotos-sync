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
        # some times are ucase T and non zero millisecs - normalize
        date = datetime.strptime(self.__photo_xml.published.text.upper()[:-4],
                                 "%Y-%m-%dT%H:%M:%S.")
        return date

    @property
    def date(self):
        # some times are ucase T and non zero millisecs - normalize
        date = datetime.fromtimestamp(
            int(self.__photo_xml.timestamp.text) / 1000)
        return date

    @property
    def mime_type(self):
        return self.__photo_xml.metadata[u'mimeType']
