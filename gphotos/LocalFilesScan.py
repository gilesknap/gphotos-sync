#!/usr/bin/env python3
# coding: utf8

from pathlib import Path
from typing import Callable
from .LocalData import LocalData
import piexif
import logging
from .LocalFilesMedia import LocalFilesMedia
from .LocalFilesRow import LocalFilesRow

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
        self._sync_root: str = None
        self._db: LocalData = db
        self.count = 0

    def scan_local_files(self):
        log.warning('Indexing comparison folder %s', self._root_folder)
        self.scan_folder(Path(self._root_folder), self.index_local_item)
        log.warning("Indexed %d files in comparison folder %s",
                    self.count, self._root_folder)

    def scan_sync_files(self, sync_root: str):
        log.warning('Extracting extra metadata from synced files in %s',
                    sync_root)
        self._sync_root = sync_root
        self.scan_folder(Path(sync_root), self.index_sync_item)
        log.warning('Completed metadata extraction from synced files in %s',
                    sync_root)

    def scan_folder(self, folder: Path, index: Callable):
        if folder.exists():
            log.debug("scanning %s", folder)
            for pth in folder.iterdir():
                if pth.is_dir():
                    self.scan_folder(pth, index)
                else:
                    self.count += 1
                    index(pth)
                    if self.count % 2000 == 0:
                        self._db.store()

    def index_local_item(self, path: Path):
        if self._db.local_exists(file_name=path.name, path=str(path.parent)):
            log.debug("already indexed local file: %s", path)
        else:
            try:
                lf = LocalFilesMedia(path)
                log.info('indexed local file: %s %s',
                         lf.relative_folder, lf.filename)
                self._db.put_row(LocalFilesRow.from_media(lf))
            except Exception:
                log.error("file %s could not be made into a media obj", path,
                          exc_info=True)
                raise

        # if path.suffix in ['.AVI', '.avi', '.mp4', '.mov', '.MOV',
        #                    '.m4v', '.3gp', '.MTS', '.gif', '.png',
        #                    '.bmp', '.pdf', '.wmv', '.mpg']:
        #     pass  # todo - non exif processing
        # else:
        #     self.index_exif_item(path)

    def index_sync_item(self, path: Path):
        try:
            lf = LocalFilesMedia(path)
            log.info('indexed EXIF for synced file: %s %s',
                     lf.relative_folder, lf.filename)
            # todo - need to have root and relative paths in LocalFilesMedia
            #  then we can extract CreateDate and UID from EXIF and add it
            #  to syncfiles columns
            # self._db.put_row(LocalFilesRow.from_media(lf))
        except Exception:
            log.error("file %s could not be made into a media obj", path,
                      exc_info=True)
            raise

    @classmethod
    def dump_exif(cls, path: Path):
        count = 0
        # use this for analysis if struggling to find relevant EXIF tags
        try:
            exif_dict = piexif.load(str(path))
            uid = exif_dict['Exif'].get(piexif.ExifIFD.ImageUniqueID)
            if uid and uid != '':
                log.warning(
                    '%s = %s', path,
                    exif_dict['Exif'].get(piexif.ExifIFD.ImageUniqueID))
            else:
                count += 1
                log.warning('No ID on %d %s', count, path)

            # for ifd in ("0th", "Exif", "GPS", "1st"):
            #     print('--------', ifd)
            #     for tag in exif_dict[ifd]:
            #         print(piexif.TAGS[ifd][tag], tag,
            #               exif_dict[ifd][tag])
        except piexif.InvalidImageDataError:
            pass
            log.debug("NO EXIF. %s", path)
