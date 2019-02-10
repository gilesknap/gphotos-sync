#!/usr/bin/env python3
# coding: utf8

from pathlib import Path
from . import Utils
from .BaseMedia import BaseMedia
from typing import Dict, List, Union, Any, Optional
from datetime import datetime
import piexif
import magic
import re

JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONType = Union[Dict[str, JSONValue], List[JSONValue]]

# Huawei adds these camera modes to description but Google Photos seems wise to
# it and does not report this in its description metadata
# noinspection SpellCheckingInspection
HUAWEI_JUNK = ['jhdr', 'edf', 'sdr', 'cof', 'nor', 'mde', 'oznor', 'btf',
               'btfmdn', 'ptfbty', 'mef', 'bsh', 'dav', 'rpt', 'fbt',
               'burst', 'rhdr', 'fbtmdn', 'ptr', 'rbtoz', 'btr', 'rbsh',
               'btroz']
# regex to check if this (might be) a duplicate with ' (n)' suffix. Note that
# 'demo (0).jpg' and 'demo (1).jpg' are note in the scheme
# bit 'demo (2).jpg' to 'demo (999).jpg' are
DUPLICATE_MATCH = re.compile(r'(.*) \(([2-9]|\d{2,3})\)\.(.*)')


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

        matches = DUPLICATE_MATCH.match(str(full_path.name))
        if matches:
            # this is a duplicate with 'file (n).jpg' format
            # extract the original name and duplicate no.
            # -1 is because the first duplicate is labelled ' (2)'
            self.duplicate_number = int(matches[2]) - 1
            self.__original_name = matches[1] + '.' + matches[3]
        else:
            self.__original_name = full_path.name
        self.__full_path: Path = full_path

    @property
    def uid(self) -> str:
        return self.__exif.get(piexif.ExifIFD.ImageUniqueID)

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
        d = self.__exif_0.get(piexif.ImageIFD.ImageDescription)
        if d:
            result = d.decode("utf-8")
            if result in HUAWEI_JUNK:
                result = ''
        else:
            result = ''
        return result

    @property
    def orig_name(self) -> str:
        return self.__original_name

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
