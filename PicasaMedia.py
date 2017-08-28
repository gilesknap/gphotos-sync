#!/usr/bin/python
# coding: utf8
import os.path
import re
from datetime import datetime
from GoogleMedia import GoogleMedia, MediaType


class PicasaMedia(GoogleMedia):
    MEDIA_FOLDER = "picasa"
    MEDIA_TYPE = MediaType.PICASA

    def __init__(self, relative_path, root_path, photo_xml=None):
        super(PicasaMedia, self).__init__(relative_path, root_path)
        self.__photo_xml = photo_xml

    @property
    def date(self):
        date = datetime.fromtimestamp(
            int(self.__photo_xml.timestamp.text) / 1000)
        return self.format_date(date)

    @property
    def size(self):
        return int(self.__photo_xml.size.text)

    @property
    def checksum(self):
        # NOTE: picasa API returns empty checksums
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

    # todo duplicate suffix logic should be in base class
    @property
    def filename(self):
        base, ext = os.path.splitext(
            os.path.basename(self.orig_name))
        if self.duplicate_number > 0:
            return "%(base)s (%(duplicate)d)%(ext)s" % {
                'base': base,
                'ext': ext,
                'duplicate': self.duplicate_number
            }
        else:
            return self.__photo_xml["title"]

    @property
    def create_date(self):
        # some times are ucase T and non zero millisecs - normalize
        date = datetime.strptime(self.__photo_xml.published.upper()[:-4],
                                 "%Y-%m-%dT%H:%M:%S.")
        return date

    @property
    def mime_type(self):
        return self.__photo_xml.metadata[u'mimeType']
