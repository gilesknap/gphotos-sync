#!/usr/bin/env python3
# coding: utf8
import os.path

from . import Utils
from .GooglePhotosMedia import GooglePhotosMedia
from .BaseMedia import MediaType
from .LocalData import LocalData
from .DatabaseMedia import DatabaseMedia
from itertools import zip_longest
import logging
import requests
import shutil
import tempfile
# apparently this is undocumented and may end up in Threading - could use Pool instead
# but have no need for separate processes since our workers are (probably) IO bound
from multiprocessing.pool import ThreadPool
from time import sleep

log = logging.getLogger('gphotos.Photos')

# todo put these in a file that is read at startup - others might have this issue
# these ids wont down load (500 on batchGet)
bad_ids = \
    [
        'AHsKWi8LNGIQN4aLv5wppfNNwasdxZbNdJZwxLrvLGCkZ21YAj3P8E8s2GbKFM7WG-qB93qmSJy1Gy5rGHaMrfbG_nDVDzUmXA',
        'AHsKWi9ODH_V16FQXd7BYLjjQI-sXLXkfcqMnwjZ1F3Ho_mqkNOKD32tsyV1b55ZP-3HQdpYET7UAIEq0msOAYGHloAYjZRocA'
    ]


class GooglePhotosSync(object):
    PAGE_SIZE = 100
    MAX_THREADS = 10

    def __init__(self, api, root_folder, db):
        """
        :param (RestClient) api
        :param (str) root_folder:
        :param (LocalData) db:
        """
        self._db = db
        self._root_folder = root_folder
        self._api = api
        self._media_folder = 'photos'
        self.download_pool = ThreadPool(self.MAX_THREADS)

        self._latest_download = self._db.get_scan_date() or Utils.minimum_date()
        # properties to be set after init
        # thus in theory one instance could so multiple indexes
        self._startDate = None
        self._endDate = None
        self.includeVideo = True

    @property
    def start_date(self):
        return self._startDate

    @start_date.setter
    def start_date(self, val):
        if val:
            self._startDate = Utils.string_to_date(val)

    @property
    def end_date(self):
        return self._endDate

    @end_date.setter
    def end_date(self, val):
        if val:
            self._endDate = Utils.string_to_date(val)

    @property
    def latest_download(self):
        return self._latest_download

    # todo this will currently do nothing unless using --flush-db
    #  need to look for a 'changes' api if we want to properly support deletes
    def check_for_removed(self):
        # note for partial scans using date filters this is still OK because
        # for a file to exist it must have been indexed in a previous scan
        log.warning(u'Finding and removing deleted media ...')
        for (dir_name, _, file_names) in os.walk(self._root_folder):
            for file_name in file_names:
                local_path = os.path.relpath(dir_name, self._root_folder)
                if file_name.startswith('.') or file_name.startswith('gphotos'):
                    continue
                file_row = self._db.get_file_by_path(local_path, file_name)
                if not file_row:
                    name = os.path.join(dir_name, file_name)
                    os.remove(name)
                    log.warning("%s deleted", name)

    def write_media_index(self, media, update=True):
        media.save_to_db(self._db, update)
        if media.create_date > self._latest_download:
            self._latest_download = media.create_date

    def search_media(self, page_token=None, start_date=None, end_date=None, do_video=False):
        class Y:
            def __init__(self, y, m, d):
                self.year = y
                self.month = m
                self.day = d

            def to_dict(self):
                return {"year": self.year, "month": self.month, "day": self.day}

        if not start_date and not end_date and do_video:
            return self._api.mediaItems.list.execute(pageToken=page_token,
                                                     pageSize=self.PAGE_SIZE).json()
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

    # a test function
    def scan_photos_media(self):
        items_json = self.search_media(start_date=self.start_date,
                                       end_date=self.end_date,
                                       do_video=self.includeVideo)
        while items_json:
            media_json = items_json.get('mediaItems')
            # cope with empty response
            if not media_json:
                break
            for media_item_json in media_json:
                media_item = GooglePhotosMedia(media_item_json)
                if len(media_item.id) < 80:
                    log.warning("%s %s %s", media_item.filename, media_item.id,
                                media_item_json["productUrl"])

    def index_photos_media(self):
        log.warning(u'Indexing Google Photos Files ...')
        count = 0

        previous_scan_latest = self._db.get_scan_date()
        items_json = self.search_media(start_date=self.start_date or previous_scan_latest,
                                       end_date=self.end_date,
                                       do_video=self.includeVideo)
        while items_json:
            media_json = items_json.get('mediaItems')
            # cope with empty response
            if not media_json:
                break
            for media_item_json in media_json:
                count += 1
                media_item = GooglePhotosMedia(media_item_json)
                media_item.set_path_by_date(self._media_folder)
                row = media_item.is_indexed(self._db)
                if not row:
                    log.info(u"Indexed %d %s", count, media_item.relative_path)
                    self.write_media_index(media_item, False)
                    if count % 2000 == 0:
                        self._db.store()
                elif media_item.modify_date > row.ModifyDate:
                    # todo at present there is no modify date in the API so updates cannot be monitored
                    log.info(u"Updated %d %s", count, media_item.relative_path)
                    self.write_media_index(media_item, True)
                else:
                    log.debug(u"Skipped %d %s", count, media_item.relative_path)
            next_page = items_json.get('nextPageToken')
            if next_page:
                items_json = self.search_media(page_token=next_page,
                                               start_date=self.start_date or previous_scan_latest,
                                               end_date=self.end_date,
                                               do_video=self.includeVideo)
            else:
                break

        # scan (in reverse date order) completed so the next incremental scan can start from the most recent file
        # file in this scan
        if not self.start_date:
            self._db.set_scan_date(last_date=self._latest_download)

    @classmethod
    def do_download_file(cls, url, local_full_path, media_item):
        # this function runs in a process pool and does the actual downloads
        folder = os.path.dirname(local_full_path)
        log.debug('--> %s background start', local_full_path)
        try:
            with tempfile.NamedTemporaryFile(dir=folder, delete=False) as temp_file:
                r = requests.get(url, stream=True)
                r.raise_for_status()
                shutil.copyfileobj(r.raw, temp_file)
                os.rename(temp_file.name, local_full_path)
            # set the access date to create date since there is nowhere
            # else to put it on linux (and is useful for debugging)
            os.utime(local_full_path,
                     (Utils.to_timestamp(media_item.modify_date),
                      Utils.to_timestamp(media_item.create_date)))
            log.debug('<-- %s background done', local_full_path)
        except requests.exceptions.HTTPError:
            log.warning('failed download of %s', local_full_path)
            log.debug('', exc_info=True)

    def download_file(self, media_item, media_json):
        """ farms media downloads off to the thread pool"""
        local_folder = os.path.join(self._root_folder, media_item.relative_folder)
        local_full_path = os.path.join(local_folder, media_item.filename)
        if media_item.is_video():
            download_url = '{}=dv'.format(media_json['baseUrl'])
        else:
            download_url = '{}=d'.format(media_json['baseUrl'])

        log.info('downloading %s', local_full_path)

        # block this function on small queue size since there is no point in getting ahead
        #  of the downloads and requiring a huge queue which eats memory
        # (uses protected member - because multiprocessing does not expose queue size yet)
        # noinspection PyProtectedMember,PyUnresolvedReferences
        while self.download_pool._inqueue.qsize() > self.MAX_THREADS:
            sleep(1)

        self.download_pool.apply_async(self.do_download_file, (download_url, local_full_path, media_item))

    def download_photo_media(self):
        """
        here we batch up our requests to get baseurl for downloading media. This avoids the overhead of one
        REST call per file. A REST call takes longer than downloading an image
        """
        def grouper(iterable):
            """Collect data into chunks size 20"""
            return zip_longest(*[iter(iterable)] * 20, fillvalue=None)

        log.warning(u'Downloading Photos ...')
        count = 0
        for media_items_block in grouper(
                # todo get rid of mediaType
                DatabaseMedia.get_media_by_search(self._db, media_type=MediaType.PHOTOS,
                                                  start_date=self.start_date, end_date=self.end_date)):
            batch_ids = []
            batch = {}
            for media_item in media_items_block:
                if media_item is None:
                    break

                local_folder = os.path.join(self._root_folder, media_item.relative_folder)
                local_full_path = os.path.join(local_folder, media_item.filename)
                if os.path.exists(local_full_path):
                    count += 1
                    log.debug(u'skipping {} {} ...'.format(count, local_full_path))
                    # todo is there anyway to detect remote updates with photos API?
                    # if Utils.to_timestamp(media.modify_date) > \
                    #         os.path.getctime(local_full_path):
                    #     log.warning(u'{} was modified'.format(local_full_path))
                    # else:
                    continue

                if not os.path.isdir(local_folder):
                    os.makedirs(local_folder)

                if len(media_item.id) < 80 or media_item.id in bad_ids:
                    # some items seem to have duff ids and cause a 400 error in batchGet
                    log.warning("bad media item id on %s", os.path.join(local_folder, media_item.filename))
                else:
                    batch_ids.append(media_item.id)
                    batch[media_item.id] = media_item

            if len(batch_ids) == 0:
                continue

            try:
                response = self._api.mediaItems.batchGet.execute(mediaItemIds=batch_ids)
                r_json = response.json()
                for media_item_json_status in r_json["mediaItemResults"]:
                    count += 1
                    # todo look at media_item_json_status["status"] for individual errors
                    media_item_json = media_item_json_status["mediaItem"]
                    media_item = batch.get(media_item_json["id"])
                    media_item.set_path_by_date(self._media_folder)
                    try:
                        self.download_file(media_item, media_item_json)
                    except requests.exceptions.HTTPError:
                        log.warning('failure downloading of %s', media_item.filename)
                        log.debug('', exc_info=True)
                        # allow process to continue on single failed file
            except Exception:
                log.error('failure in batch get of %s', batch_ids)
                raise

        # allow any remaining background downloads to complete
        self.download_pool.close()
        self.download_pool.join()
        log.warning(u'Download %d Photos complete', count)

    def single_get(self, media_item):
        try:
            response = self._api.mediaItems.get.execute(mediaItemId=media_item.id)
            media_item_json = response.json()
            self.download_file(media_item, media_item_json)
        except requests.exceptions.HTTPError:
            log.warning('failure downloading of %s', media_item.filename)
            log.debug('', exc_info=True)
            # allow process to continue on single failed file
