#!/usr/bin/python
# coding: utf8
from GoogleMedia import GoogleMedia, MediaType, MediaFolder
import Utils
import mimetypes


class AlbumMedia(GoogleMedia):
    MEDIA_TYPE = MediaType.ALBUM
    MEDIA_FOLDER = MediaFolder[MEDIA_TYPE]

    def __init__(self,  album_xml=None):
        # albums so not get saved to the filesystem so require no paths
        # (album_links on the other had do)
        # todo implement album_links derivation of GoogleMedia
        super(AlbumMedia, self).__init__('', '')
        self.__album_xml = album_xml

    # ----- override Properties below -----
    @property
    def size(self):
        return int(self.__album_xml.numphotos.text)

    @property
    def id(self):
        return self.__album_xml.gphoto_id.text

    @property
    def description(self):
        # NOTE: picasa API returns empty description field, use title
        return GoogleMedia.validate_encoding(
            self.__album_xml.title.text)

    @property
    def create_date(self):
        return Utils.string_to_date(self.__album_xml.published.text)

    @property
    def date(self):
        return Utils.string_to_date(self.__album_xml.updated.text)

    @property
    def orig_name(self):
        return GoogleMedia.validate_encoding(self.__album_xml.title.text)

    # the below base class abstract properties are not relevant to album
    @property
    def checksum(self):
        return None

    @property
    def url(self):
        return None

    @property
    def mime_type(self):
        return None
