#!/usr/bin/python
# coding: utf8
import re
from datetime import datetime
from GoogleMedia import GoogleMedia, MediaType, MediaFolder


class GoogleDriveMedia(GoogleMedia):
    MEDIA_TYPE = MediaType.DRIVE
    MEDIA_FOLDER = MediaFolder[MEDIA_TYPE]

    def __init__(self, relative_folder, root_folder, drive_file=None):
        super(GoogleDriveMedia, self).__init__(relative_folder, root_folder)
        self.__drive_file = drive_file

    def get_custom_property_value(self, key):
        for prop in self.__drive_file["properties"]:
            if prop["key"] == key:
                return prop["value"]
        raise KeyError()

    def get_exif_value(self, tag_name):
        try:
            exif_override_property_name = "exif-%s" % tag_name
            return self.get_custom_property_value(exif_override_property_name)
        except KeyError:
            return self.__drive_file["imageMediaMetadata"][tag_name]

    # ----- override Properties below -----
    @property
    def size(self):
        return int(self.__drive_file["fileSize"])

    @property
    def checksum(self):
        return self.__drive_file["md5Checksum"]

    @property
    def id(self):
        return self.__drive_file["id"]

    @property
    def description(self):
        try:
            return self.__drive_file["description"]
        except KeyError:
            return ''

    @property
    def orig_name(self):
        try:
            return self.__drive_file["originalFilename"]
        except KeyError:
            return self.__drive_file["title"]

    @property
    def create_date(self):
        # some times are ucase T and non zero millisecs - normalize
        date = datetime.strptime(self.__drive_file["createdDate"].upper()[:-4],
                                 "%Y-%m-%dT%H:%M:%S.")
        return date

    @property
    def date(self):
        try:
            exif_date = self.get_exif_value("date")
            photo_date = self.format_date(exif_date)
        except (KeyError, ValueError):
            photo_date = self.create_date

        return photo_date

    @property
    def mime_type(self):
        return self.__drive_file.metadata[u'mimeType']

    # ----- Base class custom properties below -----
    @property
    def camera_owner(self):
        try:
            artist = self.get_exif_value("artist")
            match = re.match("Camera Owner, ([^;]+)(?:;|$)", artist)
            camera_owner = match.group(1) if match else artist
        except KeyError:
            camera_owner = None

        return camera_owner

    @property
    def camera_model(self):
        try:
            camera_model = self.get_exif_value("cameraModel")
        except KeyError:
            if re.match(r"IMG-\d{8}-WA\d+", self.filename):
                camera_model = "WhatsApp"
            else:
                camera_model = None

        return camera_model
