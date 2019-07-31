#!/usr/bin/env python3
# coding: utf8
from pathlib import Path
import os
from gphotos import Utils
from gphotos.LocalData import LocalData
from gphotos.restclient import RestClient
from gphotos.DatabaseMedia import DatabaseMedia
from gphotos.GooglePhotosRow import GooglePhotosRow
from gphotos.BadIds import BadIds

from itertools import zip_longest
from typing import Iterable, Mapping, Union, List
from datetime import datetime
import logging
import shutil
import tempfile
import concurrent.futures as futures

import requests
from requests.exceptions import RequestException
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)


class GooglePhotosDownload(object):
    """A Class for managing the indexing and download of Google Photos
    """
    PAGE_SIZE: int = 100
    MAX_THREADS: int = 20
    BATCH_SIZE: int = 40

    def __init__(self, api: RestClient, root_folder: Path, db: LocalData):
        """
        Parameters:
            api: object representing the Google REST API
            root_folder: path to the root of local file synchronization
            db: local database for indexing
        """
        self._db: LocalData = db
        self._root_folder: Path = root_folder
        self._api: RestClient = api

        self.files_downloaded: int = 0
        self.files_download_started: int = 0
        self.files_download_skipped: int = 0
        self.files_download_failed: int = 0

        # attributes to be set after init
        # thus in theory one instance could so multiple indexes
        self.start_date: datetime = None
        self.end_date: datetime = None
        self.retry_download: bool = False
        self.video_timeout: int = 2000
        self.image_timeout: int = 60

        # attributes related to multi-threaded download
        self.download_pool = futures.ThreadPoolExecutor(
            max_workers=self.MAX_THREADS)
        self.pool_future_to_media = {}
        self.bad_ids = BadIds(self._root_folder)

        self.current_umask = os.umask(7)
        os.umask(self.current_umask)

        self._session = requests.Session()
        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[500, 502, 503, 504],
                        method_whitelist=frozenset(['GET', 'POST']),
                        raise_on_status=False)
        self._session.mount(
            'https://', HTTPAdapter(max_retries=retries,
                                    pool_maxsize=self.MAX_THREADS))

    def download_photo_media(self):
        """
        here we batch up our requests to get base url for downloading media.
        This avoids the overhead of one REST call per file. A REST call
        takes longer than downloading an image
        """

        def grouper(
                iterable: Iterable[DatabaseMedia]) \
                -> Iterable[Iterable[DatabaseMedia]]:
            """Collect data into chunks size BATCH_SIZE"""
            return zip_longest(*[iter(iterable)] * self.BATCH_SIZE,
                               fillvalue=None)

        if not self.retry_download:
            self.files_download_skipped = self._db.downloaded_count()

        log.warning('Downloading Photos ...')
        try:
            for media_items_block in grouper(
                    self._db.get_rows_by_search(
                        GooglePhotosRow,
                        start_date=self.start_date,
                        end_date=self.end_date,
                        skip_downloaded=not self.retry_download)):
                batch = {}

                items = (mi for mi in media_items_block if mi)
                for media_item in items:
                    local_folder = \
                        self._root_folder / media_item.relative_folder
                    local_full_path = \
                        local_folder / media_item.filename

                    if local_full_path.exists():
                        self.files_download_skipped += 1
                        log.debug('SKIPPED download (file exists) %d %s',
                                  self.files_download_skipped,
                                  media_item.relative_path)
                        self._db.put_downloaded(media_item.id)

                    elif self.bad_ids.check_id_ok(media_item.id):
                        batch[media_item.id] = media_item
                        if not local_folder.is_dir():
                            local_folder.mkdir(parents=True)

                if len(batch) > 0:
                    self.download_batch(batch)
        finally:
            # allow any remaining background downloads to complete
            futures_left = list(self.pool_future_to_media.keys())
            self.do_download_complete(futures_left)
            log.warning(
                'Downloaded %d Items, Failed %d, Already Downloaded %d',
                self.files_downloaded, self.files_download_failed,
                self.files_download_skipped)
            self.bad_ids.store_ids()
            self.bad_ids.report()

    def download_batch(self, batch: Mapping[str, DatabaseMedia]):
        """ Downloads a batch of media items collected in download_photo_media.

        A fresh 'base_url' is required since they have limited lifespan and
        these are obtained by a single call to the service function
        mediaItems.batchGet.
        """
        try:
            response = self._api.mediaItems.batchGet.execute(
                mediaItemIds=batch.keys())
            r_json = response.json()
            if r_json.get('pageToken'):
                log.error("Ops - Batch size too big, some items dropped!")

            for media_item_json_status in r_json["mediaItemResults"]:
                # todo look at media_item_json_status["status"] for errors
                media_item_json = media_item_json_status.get("mediaItem")
                if not media_item_json:
                    log.warning('Null response in mediaItems.batchGet %s',
                                batch.keys())
                else:
                    media_item = batch.get(media_item_json["id"])
                    self.download_file(media_item, media_item_json)

        except KeyboardInterrupt:
            log.warning('Cancelling download threads ...')
            for f in self.pool_future_to_media:
                f.cancel()
            futures.wait(self.pool_future_to_media)
            log.warning('Cancelled download threads')
            raise
        except RequestException:
            self.find_bad_items(batch)

    def download_file(self, media_item: DatabaseMedia, media_json: dict):
        """ farms a single media download off to the thread pool.

        Uses a dictionary of Futures -> mediaItem to track downloads that are
        currently scheduled/running. When a Future is done it calls
        do_download_complete to remove the Future from the dictionary and
        complete processing of the media item.
        """
        base_url = media_json['baseUrl']

        # we dont want a massive queue so wait until at least one thread is free
        while len(self.pool_future_to_media) >= self.MAX_THREADS:
            # check which futures are done, complete the main thread work
            # and remove them from the dictionary
            done_list = []
            for future in self.pool_future_to_media.keys():
                if future.done():
                    done_list.append(future)

            self.do_download_complete(done_list)

        # start a new background download
        self.files_download_started += 1
        log.info('downloading %d %s', self.files_download_started,
                 media_item.relative_path)
        future = self.download_pool.submit(self.do_download_file,
                                           base_url, media_item)
        self.pool_future_to_media[future] = media_item

    def do_download_file(self, base_url: str, media_item: DatabaseMedia):
        """ Runs in a process pool and does a download of a single media item.
        """
        local_folder = self._root_folder / media_item.relative_folder
        local_full_path = local_folder / media_item.filename
        if media_item.is_video():
            download_url = '{}=dv'.format(base_url)
            timeout = self.video_timeout
        else:
            download_url = '{}=d'.format(base_url)
            timeout = self.image_timeout
        temp_file = tempfile.NamedTemporaryFile(dir=local_folder, delete=False)
        t_path = Path(temp_file.name)

        try:
            response = self._session.get(download_url, stream=True,
                                         timeout=timeout)
            response.raise_for_status()
            shutil.copyfileobj(response.raw, temp_file)
            temp_file.close()
            temp_file = None
            response.close()
            t_path.rename(local_full_path)
            os.utime(str(local_full_path),
                     (Utils.safe_timestamp(media_item.modify_date),
                      Utils.safe_timestamp(media_item.create_date)))
            os.chmod(str(local_full_path), 0o666 & ~self.current_umask)
        except KeyboardInterrupt:
            log.debug("User cancelled download thread")
            raise
        finally:
            if temp_file:
                temp_file.close()
            if t_path.exists():
                t_path.unlink()

    def do_download_complete(self,
                             futures_list: Union[
                                 Mapping[futures.Future, DatabaseMedia],
                                 List[futures.Future]]):
        """ runs in the main thread and completes processing of a media
        item once (multi threaded) do_download has completed
        """
        for future in futures_list:
            media_item = self.pool_future_to_media.get(future)
            timeout = self.video_timeout if media_item.is_video() else \
                self.image_timeout
            e = future.exception(timeout=timeout)
            if e:
                self.files_download_failed += 1
                log.error('FAILURE %d downloading %s',
                          self.files_download_failed, media_item.relative_path)
                if isinstance(e, RequestException):
                    self.bad_ids.add_id(
                        media_item.relative_path, media_item.id,
                        media_item.url, e)
                else:
                    raise e
            else:
                self._db.put_downloaded(media_item.id)
                self.files_downloaded += 1
                log.debug('COMPLETED %d downloading %s',
                          self.files_downloaded, media_item.relative_path)
            del self.pool_future_to_media[future]

    def find_bad_items(self, batch: Mapping[str, DatabaseMedia]):
        """
        a batch get failed. Now do all of its contents as individual
        gets so we can work out which ID(s) cause the failure
        """
        for item_id, media_item in batch.items():
            try:
                log.debug('BAD ID Retry on %s (%s)', item_id,
                          media_item.relative_path)
                response = self._api.mediaItems.get.execute(mediaItemId=item_id)
                media_item_json = response.json()
                self.download_file(media_item, media_item_json)
            except RequestException as e:
                self.bad_ids.add_id(str(media_item.relative_path),
                                    media_item.id, media_item.url, e)
                self.files_download_failed += 1
                log.error('FAILURE %d in get of %s BAD ID',
                          self.files_download_failed, media_item.relative_path)
