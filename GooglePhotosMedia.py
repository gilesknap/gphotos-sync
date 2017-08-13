#!/usr/bin/python
# coding: utf8
import os.path
import re
from datetime import datetime


class GooglePhotosMedia(object):
    def __init__(self, drive_file, path):
        # todo make drive_file private and path/duplicate properties
        # (requires changes to callers)
        self.drive_file = drive_file
        self.duplicate_number = 0
        self.path = path

    def get_custom_property_value(self, key):
        for prop in self.drive_file["properties"]:
            if prop["key"] == key:
                return prop["value"]

        raise KeyError()

    def get_exif_value(self, tag_name):
        try:
            exif_override_property_name = "exif-%s" % tag_name
            return self.get_custom_property_value(exif_override_property_name)
        except KeyError:
            return self.drive_file["imageMediaMetadata"][tag_name]

    @property
    def date(self):
        try:
            exif_date = self.get_exif_value("date")
            photo_date = datetime.strptime(exif_date, "%Y:%m:%d %H:%M:%S")
        except (KeyError, ValueError):
            import_date = self.drive_file["createdDate"]
            # some times are ucase T and non zero millisecs - normalize
            photo_date = datetime.strptime(import_date.upper()[:-4],
                                           "%Y-%m-%dT%H:%M:%S.")

        return photo_date

    @property
    def size(self):
        return int(self.drive_file["fileSize"])

    @property
    def checksum(self):
        return self.drive_file["md5Checksum"]

    @property
    def id(self):
        return self.drive_file["id"]

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
    def extension(self):
        try:
            return self.drive_file["fileExtension"]
        except KeyError:
            return ''

    @property
    def description(self):
        try:
            return self.drive_file["description"]
        except KeyError:
            return ''

    @property
    def orig_name(self):
        try:
            return self.drive_file["originalFilename"]
        except KeyError:
            return ''

    @property
    def filename(self):
        base, ext = os.path.splitext(os.path.basename(self.drive_file["title"]))
        if self.duplicate_number > 0:
            return "%(base)s (%(duplicate)d)%(ext)s" % {
                'base': base,
                'ext': ext,
                'duplicate': self.duplicate_number
            }
        else:
            return self.drive_file["title"]

    @property
    def create_date(self):
        # todo this is duplicated above in date property
        date = datetime.strptime(self.drive_file["createdDate"].upper()[:-4],
                                           "%Y-%m-%dT%H:%M:%S.")
        # todo consolidate time format across all uses in the project
        return date.strftime('%Y-%m-%d %H:%M:%S')
