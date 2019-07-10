#!/usr/bin/env python3
# coding: utf8
from pathlib import Path
from datetime import datetime

from gphotos import Utils
from gphotos.GooglePhotosMedia import GooglePhotosMedia
from gphotos.GooglePhotosRow import GooglePhotosRow
from gphotos.LocalFilesMedia import LocalFilesMedia
from gphotos.LocalData import LocalData
from gphotos.restclient import RestClient

import logging

log = logging.getLogger(__name__)


class GooglePhotosIndex(object):
    PAGE_SIZE = 100

    def __init__(self, api: RestClient, root_folder: Path, db: LocalData,
                 photos_path: Path, use_flat_path: bool = False):
        self._api: RestClient = api
        self._root_folder: Path = root_folder
        self._db: LocalData = db
        self._media_folder: Path = Path(photos_path)
        self._use_flat_path = use_flat_path

        self.files_indexed: int = 0
        self.files_index_skipped: int = 0

        if db:
            self.latest_download = self._db.get_scan_date() or \
                                   Utils.minimum_date()

        # attributes to be set after init
        # thus in theory one instance could do multiple indexes
        self.start_date: datetime = None
        self.end_date: datetime = None
        self.include_video: bool = True
        self.rescan: bool = False
        self.favourites = False

    def check_for_removed_in_folder(self, folder: Path):
        for pth in folder.iterdir():
            if pth.is_dir():
                self.check_for_removed_in_folder(pth)
            else:
                local_path = pth.relative_to(self._root_folder).parent
                if pth.match('.*') or pth.match('gphotos*'):
                    continue
                file_row = self._db.get_file_by_path(
                    GooglePhotosRow, local_path, pth.name)
                if not file_row:
                    pth.unlink()
                    log.warning("%s deleted", pth)

    def check_for_removed(self):
        """ Removes local files that are no longer represented in the Photos
        Library - presumably because they were deleted.

        note for partial scans using date filters this is still OK because
        for a file to exist it must have been indexed in a previous scan
        """
        log.warning('Finding and removing deleted media ...')
        self.check_for_removed_in_folder(self._root_folder / self._media_folder)

    def write_media_index(self, media: GooglePhotosMedia,
                          update: bool = True):
        self._db.put_row(GooglePhotosRow.from_media(media), update)
        if media.create_date > self.latest_download:
            self.latest_download = media.create_date

    def search_media(self, page_token: int = None,
                     start_date: datetime = None,
                     end_date: datetime = None,
                     do_video: bool = False,
                     favourites: bool = False) -> dict:
        class Y:
            def __init__(self, y, m, d):
                self.year = y
                self.month = m
                self.day = d

            def to_dict(self):
                return {"year": self.year, "month": self.month, "day": self.day}

        start = Y(1900, 1, 1)
        end = Y(3000, 1, 1)
        type_list = ["ALL_MEDIA"]

        if start_date:
            start = Y(start_date.year, start_date.month, start_date.day)
        if end_date:
            end = Y(end_date.year, end_date.month, end_date.day)
        if not do_video:
            type_list = ["PHOTO"]
        if favourites:
            feature = 'FAVORITES'
        else:
            feature = 'NONE'

        if not page_token:
            log.info('searching for media start=%s, end=%s, videos=%s',
                     start_date, end_date, do_video)
        if not start_date and not end_date and do_video and not favourites:
            # no search criteria so do a list of the entire library
            log.debug('mediaItems.list ...')
            return self._api.mediaItems.list.execute(
                pageToken=page_token, pageSize=self.PAGE_SIZE).json()
        else:
            body = {
                'pageToken': page_token,
                'pageSize': self.PAGE_SIZE,
                'filters': {
                    'dateFilter': {
                        'ranges':
                            [
                                {'startDate': start.to_dict(),
                                 'endDate': end.to_dict()
                                 }
                            ]
                    },
                    'mediaTypeFilter': {'mediaTypes': type_list},
                    "featureFilter": {
                        "includedFeatures": [feature]
                    },
                }
            }
            log.debug('mediaItems.search with body:\n{}'.format(body))
            return self._api.mediaItems.search.execute(body).json()

    def index_photos_media(self) -> bool:
        log.warning('Indexing Google Photos Files ...')

        if self.start_date:
            start_date = self.start_date
        elif self.rescan:
            start_date = None
        else:
            start_date = self._db.get_scan_date()

        items_json = self.search_media(start_date=start_date,
                                       end_date=self.end_date,
                                       do_video=self.include_video,
                                       favourites=self.favourites)

        while items_json:
            media_json = items_json.get('mediaItems')
            # cope with empty response
            if not media_json:
                break
            for media_item_json in media_json:
                media_item = GooglePhotosMedia(media_item_json)
                media_item.set_path_by_date(self._media_folder,
                                            self._use_flat_path)
                (num, row) = self._db.file_duplicate_no(
                    str(media_item.filename), str(media_item.relative_folder),
                    media_item.id)
                # we just learned if there were any duplicates in the db
                media_item.duplicate_number = num

                if not row:
                    self.files_indexed += 1
                    log.info("Indexed %d %s", self.files_indexed,
                             media_item.relative_path)
                    self.write_media_index(media_item, False)
                    if self.files_indexed % 2000 == 0:
                        self._db.store()
                elif media_item.modify_date > row.modify_date:
                    self.files_indexed += 1
                    # todo at present there is no modify date in the API
                    #  so updates cannot be monitored - this won't get called
                    log.info("Updated Index %d %s", self.files_indexed,
                             media_item.relative_path)
                    self.write_media_index(media_item, True)
                else:
                    self.files_index_skipped += 1
                    log.debug("Skipped Index (already indexed) %d %s",
                              self.files_index_skipped,
                              media_item.relative_path)
                    self.latest_download = max(self.latest_download,
                                               media_item.create_date)
            next_page = items_json.get('nextPageToken')
            if next_page:
                items_json = self.search_media(page_token=next_page,
                                               start_date=start_date,
                                               end_date=self.end_date,
                                               do_video=self.include_video,
                                               favourites=self.favourites)
            else:
                break

        # scan (in reverse date order) completed so the next incremental scan
        # can start from the most recent file in this scan
        if not self.start_date:
            self._db.set_scan_date(last_date=self.latest_download)

        return self.files_indexed > 0

    def get_extra_meta(self):
        count = 0
        log.warning('updating index with extra metadata for comparison '
                    '(may take some time) ...')
        media_items = self._db.get_rows_by_search(
            GooglePhotosRow, uid='ISNULL')
        for item in media_items:
            file_path = self._root_folder / item.relative_path
            # if this item has a uid it has been scanned before
            if file_path.exists():
                local_file = LocalFilesMedia(file_path)
                count += 1
                log.info('updating metadata %d on %s', count, file_path)
                item.update_extra_meta(local_file.uid,
                                       local_file.create_date,
                                       local_file.size)
                # erm lets try some duck typing then !
                # todo is the DbRow class model rubbish or brilliant Python?
                # noinspection PyTypeChecker
                self._db.put_row(GooglePhotosRow.from_media(item),
                                 update=True)
                if count % 2000 == 0:
                    self._db.store()
            else:
                log.debug('skipping metadata (already scanned) on %s',
                          file_path)
        log.warning('updating index with extra metadata complete')
