#!/usr/bin/env python3
# coding: utf8
import shutil
from datetime import datetime
from typing import Dict
from pathlib import Path
import os.path

from . import Utils
from .GoogleAlbumMedia import GoogleAlbumMedia
from .GooglePhotosMedia import GooglePhotosMedia
from .GoogleAlbumsRow import GoogleAlbumsRow
from .LocalData import LocalData
from .restclient import RestClient
import logging

log = logging.getLogger(__name__)


class GoogleAlbumsSync(object):
    """A Class for managing the indexing and download Google of Albums
    """

    def __init__(self, api: RestClient, root_folder: Path, db: LocalData,
                 flush: bool):
        """
        Parameters:
            root_folder: path to the root of local file synchronization
            api: object representing the Google REST API
            db: local database for indexing
        """
        self._root_folder: Path = root_folder
        self._db: LocalData = db
        self._api: RestClient = api
        self.flush = flush

    @classmethod
    def make_search_parameters(cls, album_id: str,
                               page_token: str = None) -> Dict:
        body = {
            'pageToken': page_token,
            'albumId': album_id,
            'pageSize': 100
        }
        return body

    def fetch_album_contents(self, album_id: str) -> (datetime, datetime):
        first_date = Utils.maximum_date()
        last_date = Utils.minimum_date()
        body = self.make_search_parameters(album_id=album_id)
        response = self._api.mediaItems.search.execute(body)
        while response:
            items_json = response.json()
            media_json = items_json.get('mediaItems')
            # cope with empty albums
            if not media_json:
                break
            for media_item_json in media_json:
                media_item = GooglePhotosMedia(media_item_json)
                log.debug('----%s', media_item.filename)
                self._db.put_album_file(album_id, media_item.id)
                self._db.put_album_file(album_id, media_item.id)
                last_date = max(media_item.create_date, last_date)
                first_date = min(media_item.create_date, first_date)
            next_page = items_json.get('nextPageToken')
            if next_page:
                body = self.make_search_parameters(album_id=album_id,
                                                   page_token=next_page)
                response = self._api.mediaItems.search.execute(body)
            else:
                break
        return first_date, last_date

    def index_album_media(self):
        """
        query google photos interface for a list of all albums and index their
        contents into the db
        """
        log.warning('Indexing Albums ...')

        # there are no filters in album listing at present so it always a
        # full rescan - it's quite quick

        count = 0
        response = self._api.albums.list.execute(pageSize=50)
        while response:
            results = response.json()
            for album_json in results['albums']:
                count += 1

                album = GoogleAlbumMedia(album_json)
                indexed_album = self._db.get_album(album_id=album.id)
                already_indexed = indexed_album.size == album.size if \
                    indexed_album else False

                if already_indexed:
                    log.debug('Skipping Album: %s, photos: %d', album.filename,
                              album.size)
                else:
                    log.info('Indexing Album: %s, photos: %d', album.filename,
                             album.size)
                    first_date, last_date = self.fetch_album_contents(album.id)
                    # write the album data down now we know the contents'
                    # date range
                    gar = GoogleAlbumsRow.from_parm(
                        album.id, album.filename, album.size,
                        first_date, last_date)
                    self._db.put_row(gar, update=indexed_album)

            next_page = results.get('nextPageToken')
            if next_page:
                response = self._api.albums.list.execute(pageSize=50,
                                                         pageToken=next_page)
            else:
                break
        log.warning('Indexed %d Albums', count)

    def create_album_content_links(self):
        log.warning("Creating album folder links to media ...")
        count = 0
        links_root = self._root_folder / 'albums'
        if links_root.exists() and self.flush:
            log.debug('removing previous album links tree')
            shutil.rmtree(links_root)

        for (path, file_name, album_name, end_date) in \
                self._db.get_album_files():

            full_file_name = self._root_folder / path / file_name

            year = Utils.safe_str_time(Utils.string_to_date(end_date), '%Y')
            month = Utils.safe_str_time(Utils.string_to_date(end_date), '%m%d')

            rel_path = u"{0} {1}".format(month, album_name)
            link_folder: Path = links_root / year / rel_path
            link_file = link_folder / file_name
            if link_file.exists():
                log.debug('album link exists: %s', link_file)
            else:
                # incredibly, pathlib.Path.relative_to cannot handle
                # '../' in a relative path !!! reverting to os.path for this.
                relative_filename = os.path.relpath(full_file_name,
                                                    str(link_folder))
                log.debug('adding album link %s -> %s', relative_filename,
                          link_file)
                try:
                    if not link_folder.is_dir():
                        log.debug('new album folder %s', link_folder)
                        link_folder.mkdir(parents=True)

                    link_file.symlink_to(relative_filename)
                    count += 1
                except FileExistsError:
                    log.error('bad link to %s', full_file_name)

        log.warning("Created %d new album folder links", count)
