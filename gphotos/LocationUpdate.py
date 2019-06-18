from pathlib import Path
from datetime import datetime

from gphotos import Utils
from gphotos.GooglePhotosRow import GooglePhotosRow
from gphotos.LocalData import LocalData
from gphotos.LocationExtract import LocationExtract

import logging

log = logging.getLogger(__name__)


class LocationUpdate:
    def __init__(self, root_folder: Path, db: LocalData, photos_path="photos"):
        self._root_folder: Path = root_folder
        self._db: LocalData = db
        self._media_folder: Path = Path(photos_path)
        self.files_indexed: int = 0
        self.files_index_skipped: int = 0
        self.start_date: datetime = None
        self.end_date: datetime = None
        if db:
            self.latest_download = self._db.get_scan_date() or \
                                   Utils.minimum_date()
        self.extractor = LocationExtract()

    def index_locations(self):
        count = 0
        log.warning('indexing image locations via Google Photos Web ...')
        media_items = self._db.get_rows_by_search(
            GooglePhotosRow,
            start_date=self.start_date,
            end_date=self.end_date)
        for item in media_items:
            file_path = self._root_folder / item.relative_path
            log.debug('extracting location %d for %s', count, file_path)
            location = self.extractor.extract_location(item.url)
            if location is None:
                self._db.put_location(item.id, 'none')
            else:
                log.info('location %d for %s is %s',
                         count, file_path, location)
                count += 1
                self._db.put_location(item.id, location)
                if count % 2000 == 0:
                    self._db.store()
        log.warning('indexing image locations complete')

    def set_locations(self):
        # this will insert location into the local files EXIF
        pass

