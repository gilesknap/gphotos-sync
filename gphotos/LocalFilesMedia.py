#!/usr/bin/env python3
# coding: utf8

from pathlib import Path
from . import Utils
from .BaseMedia import BaseMedia
from typing import Dict, List, Union, Any, Optional
from datetime import datetime
import piexif
import magic

JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONType = Union[Dict[str, JSONValue], List[JSONValue]]


class LocalFilesMedia(BaseMedia):
    mime = magic.Magic(mime=True)

    def __init__(self, full_path: Path):
        super(LocalFilesMedia, self).__init__()
        try:
            exif = piexif.load(str(full_path))
            self.got_exif = True
            self.__exif_0: dict = exif["0th"]
            self.__exif: dict = exif["Exif"]
        except piexif.InvalidImageDataError:
            self.got_exif = False
            self.__exif_0: dict = {}
            self.__exif: dict = {}
        self.__full_path: Path = full_path

    # ----- override Properties below -----
    @property
    def relative_folder(self) -> str:
        return str(self.__full_path.parent)

    @property
    def size(self) -> int:
        return self.__full_path.stat().st_size

    @property
    def id(self) -> Optional[str]:
        return None

    @property
    def description(self) -> str:
        return self.__exif_0.get(piexif.ImageIFD.ImageDescription)

    @property
    def orig_name(self) -> str:
        return self.__full_path.name

    @property
    def create_date(self) -> datetime:
        photo_date = None
        if self.got_exif:
            try:
                d_bytes = self.__exif.get(piexif.ExifIFD.DateTimeOriginal)
                photo_date = Utils.string_to_date(d_bytes.decode("utf-8"))
            except (KeyError, ValueError, AttributeError):
                try:
                    d_bytes = self.__exif_0.get(piexif.ImageIFD.DateTime)
                    photo_date = Utils.string_to_date(d_bytes.decode("utf-8"))
                except (KeyError, ValueError, AttributeError):
                    pass

        if not photo_date:
            # just use file date
            photo_date = datetime.utcfromtimestamp(
                self.__full_path.stat().st_mtime)
        return photo_date

    @property
    def modify_date(self) -> datetime:
        return self.create_date

    @property
    def mime_type(self) -> str:
        return self.mime.from_file(str(self.__full_path))

    @property
    def url(self) -> Optional[str]:
        return None

    @property
    def camera_model(self):
        return self.__exif_0.get(piexif.ImageIFD.CameraSerialNumber)
