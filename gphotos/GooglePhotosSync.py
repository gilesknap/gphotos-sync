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

log = logging.getLogger('gphotos.Photos')


class GooglePhotosSync(object):
    PAGE_SIZE = 100

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
        self.download_pool = ThreadPool(10)

        self._latest_download = Utils.minimum_date()
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
        log.info(u'Finding deleted media ...')
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
        if media.modify_date > self._latest_download:
            self._latest_download = media.modify_date

    @classmethod
    def make_search_parameters(cls, page_token=None, start_date=None, end_date=None, do_video=False):
        # todo - instead of this crude code,
        #  should probably work out a nice way to read the REST schema into some useful dynamic classes
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

        body = {
            'pageToken': page_token,
            'pageSize': 100,
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
        return body

    def index_photos_media(self):
        log.info(u'Indexing Google Photos Files ...')
        count = 0
        try:
            body = self.make_search_parameters(start_date=self.start_date,
                                               end_date=self.end_date,
                                               do_video=self.includeVideo)
            response = self._api.mediaItems.search.execute(body)
            while response:
                items_json = response.json()
                media_json = items_json.get('mediaItems')
                # cope with empty response
                if not media_json:
                    break
                for media_item_json in media_json:
                    media_item = GooglePhotosMedia(media_item_json)
                    media_item.set_path_by_date(self._media_folder)
                    row = media_item.is_indexed(self._db)
                    if not row:
                        count += 1
                        log.info(u"Indexed %d %s", count, media_item.relative_path)
                        self.write_media_index(media_item, False)
                        if count % 1000 == 0:
                            self._db.store()
                    elif media_item.modify_date > row.ModifyDate:
                        log.info(u"Updated %s", media_item.relative_path)
                        self.write_media_index(media_item, True)
                    else:
                        log.debug(u"Skipped %s", media_item.relative_path)
                next_page = items_json.get('nextPageToken')
                if next_page:
                    body = self.make_search_parameters(page_token=next_page,
                                                       start_date=self.start_date,
                                                       end_date=self.end_date,
                                                       do_video=self.includeVideo)
                    response = self._api.mediaItems.search.execute(body)
                else:
                    break
        finally:
            # store latest date for incremental backup only if scanning all
            if not (self.start_date or self.end_date):
                self._db.set_scan_dates(drive_last_date=self._latest_download)

    @classmethod
    def do_download_file(cls, url, local_full_path, media_item):
        # this function runs in a process pool and does the actual downloads
        folder = os.path.dirname(local_full_path)
        log.debug('--> %s background start', local_full_path)
        try:
            with tempfile.NamedTemporaryFile(dir=folder, delete=False) as temp_file:
                r = requests.get(url, stream=True)
                shutil.copyfileobj(r.raw, temp_file)
                os.rename(temp_file.name, local_full_path)
            # set the access date to create date since there is nowhere
            # else to put it on linux (and is useful for debugging)
            os.utime(local_full_path,
                     (Utils.to_timestamp(media_item.modify_date),
                      Utils.to_timestamp(media_item.create_date)))
            log.debug('<-- %s background done', local_full_path)
        except Exception:
            log.error('failed download of %s', local_full_path, exc_info=True)

    def download_file(self, url=None, local_full_path=None, media_item=None):
        """ farms downloads off to a thread pool"""
        # (uses protected member) block this function on reasonable queue size
        # this is lieu of multiprocessing.Pool providing a queue size initializer
        while self.download_pool._taskqueue.qsize() > 100:
            time.sleep(1)
        self.download_pool.apply_async(self.do_download_file, (url, local_full_path, media_item))

    def download_photo_media(self):
        def grouper(iterable):
            """Collect data into chunks size 20"""
            return zip_longest(*[iter(iterable)] * 20, fillvalue=None)

        log.info(u'Downloading Photos ...')
        count = 0
        for media_items_block in grouper(
                DatabaseMedia.get_media_by_search(self._db, media_type=MediaType.PHOTOS,
                                                  start_date=self.start_date, end_date=self.end_date)):
            batch_ids = []
            for media_item in media_items_block:
                if media_item is None:
                    break

                local_folder = os.path.join(self._root_folder, media_item.relative_folder)
                local_full_path = os.path.join(local_folder, media_item.filename)
                if os.path.exists(local_full_path):
                    log.debug(u'skipping {} ...'.format(local_full_path))
                    # todo is there anyway to detect remote updates with photos API?
                    # if Utils.to_timestamp(media.modify_date) > \
                    #         os.path.getctime(local_full_path):
                    #     log.warning(u'{} was modified'.format(local_full_path))
                    # else:
                    continue

                if not os.path.isdir(local_folder):
                    os.makedirs(local_folder)
                batch_ids.append(media_item.id)

            if len(batch_ids) == 0:
                continue

            try:
                response = self._api.mediaItems.batchGet.execute(mediaItemIds=batch_ids)
                r_json = response.json()
                for media_item_json_status in r_json["mediaItemResults"]:
                    count += 1
                    # todo look at media_item_json_status["status"] for individual errors
                    media_item_json = media_item_json_status["mediaItem"]
                    media_item = GooglePhotosMedia(media_item_json)
                    media_item.set_path_by_date(self._media_folder)
                    try:
                        local_folder = os.path.join(self._root_folder, media_item.relative_folder)
                        local_full_path = os.path.join(local_folder, media_item.filename)
                        if media_item.is_video():
                            log.info(u'downloading video {} {} ...'.format(count, local_full_path))
                            download_url = '{}=dv'.format(media_item_json['baseUrl'])
                        else:
                            log.info(u'downloading image {} {} ...'.format(count, local_full_path))
                            download_url = '{}=d'.format(media_item_json['baseUrl'])
                        self.download_file(download_url, local_full_path, media_item)
                    except Exception as e:
                        log.error('failure downloading of {}.\n{}{}'.format(media_item.filename, type(e), e))
            except Exception as e:
                log.error('failure in batch get of {}.\n{}{}'.format(batch_ids, type(e), e))

        # allow any remaining background downloads to complete
        self.download_pool.close()
        self.download_pool.join()
