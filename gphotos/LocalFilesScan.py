#!/usr/bin/env python3
# coding: utf8
from pathlib import Path
import piexif
from libxmp.utils import file_to_dict

from . import Utils
from .LocalData import LocalData
import logging

log = logging.getLogger(__name__)


class LocalFilesScan(object):
    """A Class for indexing media files in a folder for comparison to a
    Google Photos Library
    """

    def __init__(self, root_folder: str, db: LocalData):
        """
        Parameters:
            root_folder: path to the root of local files to scan
            db: local database for indexing
        """
        self._root_folder: str = root_folder
        self._db: LocalData = db

    def scan_files(self):
        log.warning('Indexing comparison folder %s', self._root_folder)
        total = self.scan_folder(Path(self._root_folder))
        log.warning("Indexed %d files", total)

    def scan_folder(self, folder: Path):
        count = 0
        log.debug("scanning %s", folder)
        for pth in folder.iterdir():
            if pth.is_dir():
                count += self.scan_folder(pth)
            else:
                count += 1
                self.index_item(pth)
        return count

    def index_item(self, path: Path):
        if path.suffix in ['.AVI', '.avi', '.mp4', '.mov', '.MOV',
                           '.m4v', '.3gp', '.MTS', '.gif', '.png',
                           '.bmp', '.pdf', '.wmv', '.mpg']:
            self.index_xmp_item(path)
            pass  # todo - non exif processing
        else:
            self.index_exif_item(path)

    @classmethod
    def index_xmp_item(cls, path: Path):
        # use of xmp
        # this shows up in some video files that have no EXIF
        # most useful would be for google generated MOVIE.mp4 files BUT
        # the created date in these represents when they were made rather than
        # the date of their contents (in my library frequently a 10 year
        # discrepancy!)
        # Given the above restriction there is likely not much benefit in
        # reading this information
        xmp = file_to_dict(str(path))
        print(path, xmp)

    @classmethod
    def index_exif_item(cls, path: Path):
        try:
            exif_dict = piexif.load(str(path))
            date_img = exif_dict["0th"].get(piexif.ImageIFD.DateTime)
            desc = exif_dict["0th"].get(piexif.ImageIFD.ImageDescription)
            date_create = exif_dict["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
            date_ok = False
            try:
                if not date_create:
                    log.debug('PRIMARY MISSING DATE %s,%s in %s',
                              date_img, date_create, path)
                else:
                    try:
                        date_create = Utils.string_to_date(
                            date_create.decode("utf-8"))
                        date_ok = True
                    except ValueError:
                        log.debug('PRIMARY DATE BAD %s,%s in %s',
                                  date_img, date_create, path)

                if not date_ok:
                    if not date_img:
                        log.debug('BOTH DATES MISSING %s,%s in %s',
                                  date_img, date_create, path)
                    else:
                        try:
                            date_img = Utils.string_to_date(
                                date_img.decode("utf-8"))
                        except ValueError:
                            log.error('SECONDARY DATE BAD %s,%s in %s',
                                      date_img, date_create, path)

                log.debug('indexed %s, %s, %s', path, desc, date_img)
            except ValueError:
                log.error('BAD DATES %s,%s in %s', date_img, date_create, path)
            # log.warning("Date: %s, Desc %s, File %s",
            #             date_create, desc, path)
        except piexif.InvalidImageDataError:
            log.error("NO EXIF in IMAGE %s", path)

    @classmethod
    def dump_exif(cls, path: Path):
        # use this for analysis if struggling to find relevant EXIF tags
        try:
            exif_dict = piexif.load(str(path))
            log.warning('Indexing %s', path)
            for ifd in ("0th", "Exif", "GPS", "1st"):
                print('--------', ifd)
                for tag in exif_dict[ifd]:
                    print(piexif.TAGS[ifd][tag], tag,
                          exif_dict[ifd][tag])
        except piexif.InvalidImageDataError:
            pass
            log.warning("NO EXIF.")
