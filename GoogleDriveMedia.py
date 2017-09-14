#!/usr/bin/python
# coding: utf8
import re

import Utils
from GoogleMedia import GoogleMedia, MediaType, MediaFolder


class GoogleDriveMedia(GoogleMedia):
    MEDIA_TYPE = MediaType.DRIVE
    MEDIA_FOLDER = MediaFolder[MEDIA_TYPE]
    EXTERNAL_LINKS = 'External-Links'

    # todo passing folder_paths (and root_folder) here seems messy, refactor?
    def __init__(self, folder_paths, root_folder, drive_file):
        self.__parent_num = 0
        self.__drive_file = drive_file
        self.find_photos_parent(folder_paths)
        if self.parent_id in folder_paths:
            relative_folder = folder_paths[self.parent_id]
        else:
            relative_folder = self.EXTERNAL_LINKS
        super(GoogleDriveMedia, self).__init__(relative_folder, root_folder)

    def find_photos_parent(self, folder_paths):
        for i in range(len(self.__drive_file["parents"])):
            self.__parent_num = i
            if self.parent_id in folder_paths:
                break

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
            return GoogleMedia.validate_encoding(
                self.__drive_file["description"])
        except KeyError:
            return ''

    @property
    def orig_name(self):
        try:
            name = self.__drive_file["originalFilename"]
        except KeyError:
            name = self.__drive_file["title"]
        return GoogleMedia.validate_encoding(name)

    @property
    def create_date(self):
        date = Utils.string_to_date(self.__drive_file["createdDate"])
        return date

    @property
    def date(self):
        try:
            exif_date = self.get_exif_value("date")
            photo_date = Utils.string_to_date(exif_date)
        except (KeyError, ValueError):
            photo_date = self.create_date

        return photo_date

    @property
    def mime_type(self):
        return self.__drive_file.metadata['mimeType']

    @property
    def url(self):
        return self.__drive_file.metadata['webContentLink']

    # ----- Derived class custom properties below -----
    @property
    def parent_id(self):
        return self.__drive_file["parents"][self.__parent_num]["id"]

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

    @property
    def modified_date(self):
        date = Utils.string_to_date(self.__drive_file["modifiedDate"])
        return date
