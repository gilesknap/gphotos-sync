#!/usr/bin/env python3
# coding: utf8

from pathlib import Path
from .LocalData import LocalData
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
        self._db: LocalData = db
        self.count = 0

    def scan_files(self):
        log.warning('Indexing comparison folder %s', self._root_folder)
        self.scan_folder(Path(self._root_folder))
        log.warning("Indexed %d files", self.count)

    def scan_folder(self, folder: Path):
        if folder.exists():
            log.debug("scanning %s", folder)
            for pth in folder.iterdir():
                if pth.is_dir():
                    self.scan_folder(pth)
                else:
                    self.count += 1
                    self.index_item(pth)
                    if self.count % 2000 == 0:
                        self._db.store()

    def index_item(self, path: Path):
        try:
            lf = LocalFilesMedia(path)
            log.warning('%s %s size:%d created:%s camera:%s %s',
                        lf.mime_type, lf.orig_name, lf.size, lf.create_date,
                        lf.camera_model, lf.description)
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


    # @classmethod
    # def dump_exif(cls, path: Path):
    #     # use this for analysis if struggling to find relevant EXIF tags
    #     try:
    #         exif_dict = piexif.load(str(path))
    #         log.warning('Indexing %s', path)
    #         for ifd in ("0th", "Exif", "GPS", "1st"):
    #             print('--------', ifd)
    #             for tag in exif_dict[ifd]:
    #                 print(piexif.TAGS[ifd][tag], tag,
    #                       exif_dict[ifd][tag])
    #     except piexif.InvalidImageDataError:
    #         pass
    #         log.warning("NO EXIF.")
