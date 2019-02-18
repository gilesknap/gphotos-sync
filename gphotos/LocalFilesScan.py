#!/usr/bin/env python3
# coding: utf8

from pathlib import Path
import shutil
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

    def __init__(self, root_folder: Path, scan_folder: Path, db: LocalData):
        """
        Parameters:
            scan_folder: path to the root of local files to scan
            db: local database for indexing
        """
        self._scan_folder: Path = scan_folder
        self._root_folder: Path = root_folder
        self._db: LocalData = db
        self.count = 0

    def scan_local_files(self):
        log.warning('Indexing comparison folder %s', self._scan_folder)
        self.scan_folder(self._scan_folder, self.index_local_item)
        log.warning("Indexed %d files in comparison folder %s",
                    self.count, self._scan_folder)

    def scan_folder(self, folder: Path, index: Callable):
        if folder.exists():
            log.debug("scanning %s", folder)
            for pth in folder.iterdir():
                if pth.is_dir():
                    self.scan_folder(pth, index)
                else:
                    self.count += index(pth)
                    if self.count and self.count % 20000 == 0:
                        self._db.store()

    def index_local_item(self, path: Path) -> int:
        if self._db.local_exists(file_name=path.name, path=str(path.parent)):
            result = 0
            log.debug("already indexed local file: %s", path)
        else:
            result = 1
            try:
                lf = LocalFilesMedia(path)
                log.info('indexed local file: %s %s %s %s',
                         lf.relative_folder, lf.filename,
                         lf.create_date, lf.uid)
                self._db.put_row(LocalFilesRow.from_media(lf))
            except Exception:
                log.error("file %s could not be made into a media obj", path,
                          exc_info=True)
                raise
        return result

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

    def find_missing_gphotos(self):
        log.warning('matching local files and photos library ...')
        self._db.find_local_matches()
        log.warning('creating comparison folder ...')
        comparison_folder = self._root_folder / 'comparison'
        flat_missing = comparison_folder / 'missing_files'
        folders_missing = comparison_folder / 'missing_folders'
        if comparison_folder.exists():
            log.debug('removing previous comparison tree')
            shutil.rmtree(comparison_folder)

        flat_missing.mkdir(parents=True)
        for i, orig_path in enumerate(self._db.get_missing_paths()):
            link_path = folders_missing / \
                        orig_path.relative_to(self._scan_folder)
            log.debug('adding missing file %d link %s', i, link_path)
            if not link_path.parent.exists():
                link_path.parent.mkdir(parents=True)
            if not link_path.exists():
                link_path.symlink_to(orig_path)
            flat_link = flat_missing / "{:05d}_{}".format(i, orig_path.name)
            flat_link.symlink_to(orig_path)

        flat_extras = comparison_folder / 'extra_files'
        folders_extras = comparison_folder / 'extra_folders'
        flat_extras.mkdir(parents=True)
        for i, orig_path in enumerate(self._db.get_extra_paths()):
            link_path = folders_extras / orig_path
            log.debug('adding extra file %d link %s', i, link_path)
            if not link_path.parent.exists():
                link_path.parent.mkdir(parents=True)
            if not link_path.exists():
                link_path.symlink_to(self._root_folder / orig_path)
            flat_link = flat_extras / "{:05d}_{}".format(i, orig_path.name)
            flat_link.symlink_to(self._root_folder / orig_path)

        flat_duplicates = comparison_folder / 'duplicates'
        flat_duplicates.mkdir(parents=True)
        duplicate_group = 0
        prev_id = ''
        for i, (rid, orig_path) in enumerate(self._db.get_duplicates()):
            if rid != prev_id:
                duplicate_group += 1
            prev_id = rid
            log.debug('adding duplicate group %d file %d link %s',
                      duplicate_group, i, orig_path)
            flat_link = flat_duplicates / "{:05d}_{:03d}_{}".format(
                i, duplicate_group, orig_path.name)
            flat_link.symlink_to(self._root_folder / orig_path)
