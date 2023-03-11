# type: ignore
# lots of typing issues in this file, partly due to use of asyncIO Future
# and concurrent Future - TODO: for reviewimport concurrent.futures as futures
import concurrent.futures as futures
import errno
import logging
import os
import shutil
import tempfile
from asyncio import Future
from datetime import datetime
from itertools import zip_longest
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Union

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

from gphotos_sync import Utils
from gphotos_sync.BadIds import BadIds
from gphotos_sync.DatabaseMedia import DatabaseMedia
from gphotos_sync.GooglePhotosRow import GooglePhotosRow
from gphotos_sync.LocalData import LocalData
from gphotos_sync.restclient import RestClient

from .Settings import Settings

try:
    import win32con  # type: ignore
    import win32file  # type: ignore

    _use_win_32 = True
except ImportError:
    win32file, win32con = None, None
    _use_win_32 = False

log = logging.getLogger(__name__)


class GooglePhotosDownload(object):
    """A Class for managing the indexing and download of Google Photos"""

    PAGE_SIZE: int = 100
    BATCH_SIZE: int = 40

    def __init__(
        self, api: RestClient, root_folder: Path, db: LocalData, settings: Settings
    ):
        """
        Parameters:
            api: object representing the Google REST API
            root_folder: path to the root of local file synchronization
            db: local database for indexing
            settings: further arguments
        """
        self._db: LocalData = db
        self._root_folder: Path = root_folder
        self._api: RestClient = api

        self.files_downloaded: int = 0
        self.files_download_started: int = 0
        self.files_download_skipped: int = 0
        self.files_download_failed: int = 0

        self.settings = settings
        self.max_threads = settings.max_threads
        self.start_date: datetime = settings.start_date
        self.end_date: datetime = settings.end_date
        self.retry_download: bool = settings.retry_download
        self.case_insensitive_fs: bool = settings.case_insensitive_fs
        self.video_timeout: int = settings.video_timeout
        self.image_timeout: int = settings.image_timeout

        # attributes related to multi-threaded download
        self.download_pool = futures.ThreadPoolExecutor(max_workers=self.max_threads)
        self.pool_future_to_media: Dict[Future, DatabaseMedia] = {}
        self.bad_ids = BadIds(self._root_folder)

        self.current_umask = os.umask(7)
        os.umask(self.current_umask)

        self._session = requests.Session()
        # define the retry behaviour for each connection. Note that
        # respect_retry_after_header=True means that status codes [413, 429, 503]
        # will backoff for the recommended period defined in the retry after header
        retries = Retry(
            total=settings.max_retries,
            backoff_factor=5,
            status_forcelist=[500, 502, 503, 504, 509, 429],
            allowed_methods=frozenset(["GET", "POST"]),
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        self._session.mount(
            "https://", HTTPAdapter(max_retries=retries, pool_maxsize=self.max_threads)
        )

    def close(self):
        self._session.close()

    def download_photo_media(self):
        """
        here we batch up our requests to get base url for downloading media.
        This avoids the overhead of one REST call per file. A REST call
        takes longer than downloading an image
        """

        def grouper(
            iterable: Iterable[DatabaseMedia],
        ) -> Iterable[Iterable[DatabaseMedia]]:
            """Collect data into chunks size BATCH_SIZE"""
            return zip_longest(*[iter(iterable)] * self.BATCH_SIZE, fillvalue=None)

        if not self.retry_download:
            self.files_download_skipped = self._db.downloaded_count()

        log.warning("Downloading Photos ...")
        try:
            for media_items_block in grouper(
                self._db.get_rows_by_search(
                    GooglePhotosRow,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    skip_downloaded=not self.retry_download,
                )
            ):
                batch = {}

                items = (mi for mi in media_items_block if mi)
                for media_item in items:
                    if self.case_insensitive_fs:
                        relative_folder = str(media_item.relative_folder).lower()
                        filename = str(media_item.filename).lower()
                    else:
                        relative_folder = media_item.relative_folder
                        filename = media_item.filename
                    local_folder = self._root_folder / relative_folder
                    local_full_path = local_folder / filename

                    try:
                        if local_full_path.exists():
                            self.files_download_skipped += 1
                            log.debug(
                                "SKIPPED download (file exists) %d %s",
                                self.files_download_skipped,
                                media_item.relative_path,
                            )
                            self._db.put_downloaded(media_item.id)

                        elif self.bad_ids.check_id_ok(media_item.id):
                            batch[media_item.id] = media_item
                            if not local_folder.is_dir():
                                local_folder.mkdir(parents=True)

                    except Exception as err:
                        # skip files with filenames too long for this OS.
                        # probably thrown by local_full_path.exists().
                        errname = type(err).__name__
                        if errname == "OSError" and (
                            err.errno == errno.ENAMETOOLONG  # type: ignore
                        ):
                            log.warning(
                                "SKIPPED file because name is too long for this OS %s",
                                local_full_path,
                            )
                            self.files_download_failed += 1
                        else:
                            # re-raise other errors
                            raise

                if len(batch) > 0:
                    self.download_batch(batch)
        finally:
            # allow any remaining background downloads to complete
            futures_left = list(self.pool_future_to_media.keys())
            self.do_download_complete(futures_left)
            log.warning(
                "Downloaded %d Items, Failed %d, Already Downloaded %d",
                self.files_downloaded,
                self.files_download_failed,
                self.files_download_skipped,
            )
            self.bad_ids.store_ids()
            self.bad_ids.report()
        return self.files_downloaded

    def download_batch(self, batch: Mapping[str, DatabaseMedia]):
        """Downloads a batch of media items collected in download_photo_media.

        A fresh 'base_url' is required since they have limited lifespan and
        these are obtained by a single call to the service function
        mediaItems.batchGet.
        """
        try:
            response = self._api.mediaItems.batchGet.execute(mediaItemIds=batch.keys())
            r_json = response.json()
            if r_json.get("pageToken"):
                log.error("Ops - Batch size too big, some items dropped!")

            for i, result in enumerate(r_json["mediaItemResults"]):
                media_item_json = result.get("mediaItem")
                if not media_item_json:
                    log.warning("Null response in mediaItems.batchGet %s", batch.keys())
                    log.debug(
                        "Null response in mediaItems.batchGet"
                        "for item %d in\n\n %s \n\n which is \n%s",
                        i,
                        str(r_json),
                        str(result),
                    )
                else:
                    media_item = batch.get(media_item_json["id"])
                    self.download_file(media_item, media_item_json)
        except RequestException:
            self.find_bad_items(batch)

        except KeyboardInterrupt:
            log.warning("Cancelling download threads ...")
            for f in self.pool_future_to_media:
                f.cancel()
            futures.wait(self.pool_future_to_media)
            log.warning("Cancelled download threads")
            raise

    def download_file(self, media_item: DatabaseMedia, media_json: dict):
        """farms a single media download off to the thread pool.

        Uses a dictionary of Futures -> mediaItem to track downloads that are
        currently scheduled/running. When a Future is done it calls
        do_download_complete to remove the Future from the dictionary and
        complete processing of the media item.
        """
        base_url = media_json["baseUrl"]

        # we dont want a massive queue so wait until at least one thread is free
        while len(self.pool_future_to_media) >= self.max_threads:
            # check which futures are done, complete the main thread work
            # and remove them from the dictionary
            done_list = []
            for future in self.pool_future_to_media.keys():
                if future.done():
                    done_list.append(future)

            self.do_download_complete(done_list)

        # start a new background download
        self.files_download_started += 1
        log.info(
            "downloading %d %s", self.files_download_started, media_item.relative_path
        )
        future = self.download_pool.submit(self.do_download_file, base_url, media_item)
        self.pool_future_to_media[future] = media_item

    def do_download_file(self, base_url: str, media_item: DatabaseMedia):
        """Runs in a process pool and does a download of a single media item."""
        if self.case_insensitive_fs:
            relative_folder = str(media_item.relative_folder).lower()
            filename = str(media_item.filename).lower()
        else:
            relative_folder = media_item.relative_folder
            filename = media_item.filename
        local_folder = self._root_folder / relative_folder
        local_full_path = local_folder / filename

        if media_item.is_video:
            download_url = "{}=dv".format(base_url)
            timeout = self.video_timeout
        else:
            download_url = "{}=d".format(base_url)
            timeout = self.image_timeout
        temp_file = tempfile.NamedTemporaryFile(dir=local_folder, delete=False)
        t_path = Path(temp_file.name)

        try:
            response = self._session.get(download_url, stream=True, timeout=timeout)
            response.raise_for_status()
            shutil.copyfileobj(response.raw, temp_file)
            temp_file.close()
            temp_file = None
            response.close()
            t_path.rename(local_full_path)
            create_date = Utils.safe_timestamp(media_item.create_date)
            os.utime(
                str(local_full_path),
                (
                    Utils.safe_timestamp(media_item.modify_date).timestamp(),
                    create_date.timestamp(),
                ),
            )
            if _use_win_32:
                file_handle = win32file.CreateFile(
                    str(local_full_path),
                    win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32con.OPEN_EXISTING,
                    0,
                    None,
                )
                win32file.SetFileTime(file_handle, *(create_date,) * 3)
                file_handle.close()
            os.chmod(str(local_full_path), 0o666 & ~self.current_umask)
        except KeyboardInterrupt:
            log.debug("User cancelled download thread")
            raise
        finally:
            if temp_file:
                temp_file.close()
            if t_path.exists():
                t_path.unlink()

    def do_download_complete(
        self,
        futures_list: Union[
            Mapping[futures.Future, DatabaseMedia], List[futures.Future]
        ],
    ):
        """runs in the main thread and completes processing of a media
        item once (multi threaded) do_download has completed
        """
        for future in futures_list:
            media_item = self.pool_future_to_media.get(future)
            timeout = self.video_timeout if media_item.is_video else self.image_timeout
            e = future.exception(timeout=timeout)
            if e:
                self.files_download_failed += 1
                log.error(
                    "FAILURE %d downloading %s - %s",
                    self.files_download_failed,
                    media_item.relative_path,
                    e,
                )
                # treat API errors as possibly transient. Report them above in
                # log.error but do not raise them. Other exceptions will raise
                # up to the root handler and abort. Note that all retry logic is
                # already handled in urllib3

                # Items that cause API errors go in a BadIds file which must
                # be deleted to retry these items.
                if isinstance(e, RequestException):
                    self.bad_ids.add_id(
                        media_item.relative_path, media_item.id, media_item.url, e
                    )
                else:
                    raise e
            else:
                self._db.put_downloaded(media_item.id)
                self.files_downloaded += 1
                log.debug(
                    "COMPLETED %d downloading %s",
                    self.files_downloaded,
                    media_item.relative_path,
                )
                if self.settings.progress and self.files_downloaded % 10 == 0:
                    log.warning(f"Downloaded {self.files_downloaded} items ...\033[F")
            del self.pool_future_to_media[future]

    def find_bad_items(self, batch: Mapping[str, DatabaseMedia]):
        """
        a batch get failed. Now do all of its contents as individual
        gets so we can work out which ID(s) cause the failure
        """
        for item_id, media_item in batch.items():
            try:
                log.debug("BAD ID Retry on %s (%s)", item_id, media_item.relative_path)
                response = self._api.mediaItems.get.execute(mediaItemId=item_id)
                media_item_json = response.json()
                self.download_file(media_item, media_item_json)
            except RequestException as e:
                self.bad_ids.add_id(
                    str(media_item.relative_path), media_item.id, media_item.url, e
                )
                self.files_download_failed += 1
                log.error(
                    "FAILURE %d in get of %s BAD ID",
                    self.files_download_failed,
                    media_item.relative_path,
                )
