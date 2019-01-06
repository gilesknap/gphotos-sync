#!/usr/bin/env python2
# coding: utf8
import os.path

from . import Utils
from .GooglePhotosMedia import GooglePhotosMedia
from .GoogleMedia import MediaType
from .LocalData import LocalData
from .DatabaseMedia import DatabaseMedia
import logging
import requests
import shutil

log = logging.getLogger('gphotos.Photos')


class NoGooglePhotosFolderError(Exception):
    pass


class GooglePhotosMediaSync(object):
    PAGE_SIZE = 100

    def __init__(self, root_folder, db, api):
        """
        :param (str) root_folder:
        :param (LocalData) db:
        """
        self._db = db
        self._root_folder = root_folder
        self.api = api

        self._latest_download = Utils.minimum_date()
        # properties to be set after init
        # thus in theory one instance could so multiple indexes
        self._startDate = None
        self._endDate = None
        self._includeVideo = False

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
    # need to look at drive changes api if we want to support deletes and
    # incremental backup.
    def check_for_removed(self):
        # note for partial scans using date filters this is still OK because
        # for a file to exist it must have been indexed in a previous scan
        log.info(u'Finding deleted media ...')
        for (dir_name, _, file_names) in os.walk(self._root_folder):
            for file_name in file_names:
                local_path = os.path.relpath(dir_name, self._root_folder)
                if file_name.startswith('.'):
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

    # todo add media type filtering (video/image)
    @classmethod
    def make_search_parameters(cls, page_token=None, start_date=None, end_date=None):
        # todo - instead of this crude code,
        #  should probably work out a nice way to read the REST schema into some useful dynamic classes
        class Y:
            def __init__(self, y, m, d):
                self.year = y
                self.month = m
                self.day = d

            def to_dict(self):
                return {"year": self.year, "month": self.month, "day": self.day}

        start = Y(1800, 1, 1)
        end = Y(3000, 1, 1)

        if start_date:
            start = Y(start_date.year, start_date.month, start_date.day)
        if end_date:
            end = Y(end_date.year, end_date.month, end_date.day)

        body = {'pageToken': page_token, 'filters': {'dateFilter':
            {'ranges':
                [
                    {'startDate': start.to_dict(),
                     'endDate': end.to_dict()
                     }
                ]
            }}}
        return body

    def index_photos_media(self):
        log.info(u'Indexing Google Photos Files ...')

        count = 0
        try:
            body = self.make_search_parameters(start_date=self.start_date, end_date=self.end_date)
            response = self.api.mediaItems.search.execute(body)
            while response:
                items = response.json()
                for media_item_json in items['mediaItems']:
                    media_item = GooglePhotosMedia(media_item_json)
                    media_item.set_path_by_date()
                    row = media_item.is_indexed(self._db)
                    if not row:
                        count += 1
                        log.info(u"Added %d %s", count, media_item.relative_path)
                        self.write_media_index(media_item, False)
                        if count % 1000 == 0:
                            self._db.store()
                    elif media_item.modify_date > row.ModifyDate:
                        log.info(u"Updated %s", media_item.relative_path)
                        self.write_media_index(media_item, True)
                    else:
                        log.debug(u"Skipped %s", media_item.relative_path)
                next_page = items.get('nextPageToken')
                if next_page:
                    body = self.make_search_parameters(page_token=next_page,
                                                       start_date=self.start_date, end_date=self.end_date)
                    response = self.api.mediaItems.search.execute(body)
                else:
                    break
        finally:
            # store latest date for incremental backup only if scanning all
            if not (self.start_date or self.end_date):
                self._db.set_scan_dates(drive_last_date=self._latest_download)

    @classmethod
    def download_file(cls, url, local_path):
        r = requests.get(url, stream=True)
        with open(local_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    def download_photo_media(self):
        log.info(u'Downloading Photos ...')
        count = 0
        # noinspection PyTypeChecker
        for media_item in DatabaseMedia.get_media_by_search(self._db, media_type=MediaType.PHOTOS,
                                                            start_date=self.start_date, end_date=self.end_date):
            local_folder = os.path.join(self._root_folder, media_item.relative_folder)
            local_full_path = os.path.join(local_folder, media_item.filename)
            if os.path.exists(local_full_path):
                log.info(u'skipping {} ...'.format(local_full_path))
                # todo is there anyway to detect remote updates with photos API?
                # if Utils.to_timestamp(media.modify_date) > \
                #         os.path.getctime(local_full_path):
                #     log.warning(u'{} was modified'.format(local_full_path))
                # else:
                continue

            if not os.path.isdir(local_folder):
                os.makedirs(local_folder)
            temp_filename = os.path.join(self._root_folder, '.temp-photo')

            count += 1
            try:
                response = self.api.mediaItems.get.execute(mediaItemId=str(media_item.id))
                r_json = response.json()
                if media_item.is_video():
                    log.info(u'downloading video {} {} ...'.format(count, local_full_path))
                    download_url = '{}=dv'.format(r_json['baseUrl'])
                else:
                    log.info(u'downloading image {} {} ...'.format(count, local_full_path))
                    download_url = '{}=d'.format(r_json['baseUrl'])
                self.download_file(download_url, temp_filename)
                os.rename(temp_filename, local_full_path)
                # set the access date to create date since there is nowhere
                # else to put it on linux (and is useful for debugging)
                os.utime(local_full_path,
                         (Utils.to_timestamp(media_item.modify_date),
                          Utils.to_timestamp(media_item.create_date)))
            except Exception as e:
                log.error('failure downloading {}.\n{}{}'.format(local_full_path, type(e), e))
