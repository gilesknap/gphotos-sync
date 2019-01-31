#!/usr/bin/env python3
# coding: utf8
import os.path
from datetime import datetime

from gphotos import Utils
from gphotos.GooglePhotosMedia import GooglePhotosMedia
from gphotos.LocalData import LocalData
from gphotos.restclient import RestClient

import logging

log = logging.getLogger(__name__)


class GooglePhotosIndex(object):
    PAGE_SIZE = 100

    def __init__(self, api: RestClient, root_folder: str, db: LocalData):
        self._api: RestClient = api
        self._root_folder: str = root_folder
        self._db: LocalData = db
        self._media_folder: str = 'photos'

        self.files_indexed: int = 0
        self.files_index_skipped: int = 0

        if db:
            self.latest_download = self._db.get_scan_date() or \
                                   Utils.minimum_date()

        # attributes to be set after init
        # those with _ must be set through their set_ function
        # thus in theory one instance could so multiple indexes
        self._start_date: datetime = None
        self._end_date: datetime = None
        self.include_video: bool = True
        self.rescan: bool = False

    def set_start_date(self, val: str):
        self._start_date = Utils.string_to_date(val)

    def set_end_date(self, val: str):
        self._end_date = Utils.string_to_date(val)

    def check_for_removed(self):
        """ Removes local files that are no longer represented in the Photos
        Library - presumably because they were deleted.

        note for partial scans using date filters this is still OK because
        for a file to exist it must have been indexed in a previous scan
        """
        log.warning('Finding and removing deleted media ...')
        start_folder = os.path.join(self._root_folder, self._media_folder)
        for (dir_name, _, file_names) in os.walk(start_folder):
            for file_name in file_names:
                local_path = os.path.relpath(dir_name, self._root_folder)
                if file_name.startswith('.') or file_name.startswith('gphotos'):
                    continue
                file_row = self._db.get_file_by_path(local_path, file_name)
                if not file_row:
                    name = os.path.join(dir_name, file_name)
                    os.remove(name)
                    log.warning("%s deleted", name)

    def write_media_index(self, media: GooglePhotosMedia,
                          update: bool = True):
        media.save_to_db(self._db, update)
        if media.create_date > self.latest_download:
            self.latest_download = media.create_date

    def search_media(self, page_token: int = None,
                     start_date: datetime = None,
                     end_date: datetime = None,
                     do_video: bool = False) -> dict:
        class Y:
            def __init__(self, y, m, d):
                self.year = y
                self.month = m
                self.day = d

            def to_dict(self):
                return {"year": self.year, "month": self.month, "day": self.day}

        if not page_token:
            log.info('searching for media start=%s, end=%s, videos=%s',
                     start_date, end_date, do_video)
        if not start_date and not end_date and do_video:
            # no search criteria so do a list of the entire library
            return self._api.mediaItems.list.execute(
                pageToken=page_token, pageSize=self.PAGE_SIZE).json()
        else:
            start = Y(1900, 1, 1)
            end = Y(3000, 1, 1)
            type_list = ["ALL_MEDIA"]

            if start_date:
                start = Y(start_date.year, start_date.month, start_date.day)
            if end_date:
                end = Y(end_date.year, end_date.month, end_date.day)
            if not do_video:
                type_list = ["PHOTO"]

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
                }
            }
            return self._api.mediaItems.search.execute(body).json()

    def index_photos_media(self):
        log.warning('Indexing Google Photos Files ...')

        if self.rescan:
            start_date = None
        else:
            start_date = self._start_date or self._db.get_scan_date()

        items_json = self.search_media(start_date=start_date,
                                       end_date=self._end_date,
                                       do_video=self.include_video)

        while items_json:
            media_json = items_json.get('mediaItems')
            # cope with empty response
            if not media_json:
                break
            for media_item_json in media_json:
                media_item = GooglePhotosMedia(media_item_json)
                media_item.set_path_by_date(self._media_folder)
                row = media_item.is_indexed(self._db)
                if not row:
                    self.files_indexed += 1
                    log.info("Indexed %d %s", self.files_indexed,
                             media_item.relative_path)
                    self.write_media_index(media_item, False)
                    if self.files_indexed % 2000 == 0:
                        self._db.store()
                elif media_item.modify_date > row.ModifyDate:
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
            next_page = items_json.get('nextPageToken')
            if next_page:
                items_json = self.search_media(page_token=next_page,
                                               start_date=start_date,
                                               end_date=self._end_date,
                                               do_video=self.include_video)
            else:
                break

        # scan (in reverse date order) completed so the next incremental scan
        # can start from the most recent file in this scan
        if not self._start_date:
            self._db.set_scan_date(last_date=self.latest_download)
