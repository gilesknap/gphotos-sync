#!/usr/bin/env python3
# coding: utf8
import shutil
from datetime import datetime
from typing import Dict, Callable
from pathlib import Path
import os.path

from . import Utils
from .GoogleAlbumMedia import GoogleAlbumMedia
from .GooglePhotosMedia import GooglePhotosMedia
from .GoogleAlbumsRow import GoogleAlbumsRow
from .GooglePhotosRow import GooglePhotosRow
from .LocalData import LocalData
from .restclient import RestClient
import logging

log = logging.getLogger(__name__)


class GoogleAlbumsSync(object):
    """A Class for managing the indexing and download Google of Albums
    """

    def __init__(self, api: RestClient, root_folder: Path, db: LocalData,
                 flush: bool, photos_path: Path,
                 albums_path: Path, use_flat_path=True, use_hardlinks=False):
        """
        Parameters:
            root_folder: path to the root of local file synchronization
            api: object representing the Google REST API
            db: local database for indexing
            :param use_flat_path:
            :param use_hardlinks:
            :param photos_path:
            :param albums_path:
        """
        self._root_folder: Path = root_folder
        self._photos_folder = Path(photos_path)
        self._albums_folder = Path(albums_path)
        self._links_root = self._root_folder / self._albums_folder
        self._photos_root = self._root_folder / self._photos_folder
        self._db: LocalData = db
        self._api: RestClient = api
        self._use_flat_path = use_flat_path
        self._use_hardlinks = use_hardlinks
        self.flush = flush
        # these properties are set after construction
        self.album = None
        self.shared_albums = True
        self.album_index = True

    @classmethod
    def make_search_parameters(cls, album_id: str,
                               page_token: str = None) -> Dict:
        body = {
            'pageToken': page_token,
            'albumId': album_id,
            'pageSize': 100
        }
        return body

    def fetch_album_contents(self, album_id: str,
                             add_media_items: bool) -> (datetime, datetime):
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
                last_date = max(media_item.create_date, last_date)
                first_date = min(media_item.create_date, first_date)

                # this adds other users photos from shared albums
                # Todo - This will cause two copies of a file to appear for
                #  those shared items you have imported into your own library.
                #  They will have different RemoteIds, one will point to your
                #  library copy (you own) and one to the shared item in the
                #  the folder. Currently with the meta data available it would
                #  be impossible to eliminate these without eliminating other
                #  cases where date and filename (TITLE) match
                if add_media_items:
                    media_item.set_path_by_date(self._photos_folder,
                                                self._use_flat_path)
                    (num, row) = self._db.file_duplicate_no(
                        str(media_item.filename),
                        str(media_item.relative_folder),
                        media_item.id)
                    # we just learned if there were any duplicates in the db
                    media_item.duplicate_number = num

                    log.debug('Adding album media item %s %s %s',
                              media_item.relative_path, media_item.filename,
                              media_item.duplicate_number)
                    self._db.put_row(
                        GooglePhotosRow.from_media(media_item), False)

            next_page = items_json.get('nextPageToken')
            if next_page:
                body = self.make_search_parameters(album_id=album_id,
                                                   page_token=next_page)
                response = self._api.mediaItems.search.execute(body)
            else:
                break
        return first_date, last_date

    def index_album_media(self):
        # we now index all contents of non-shared albums due to the behaviour
        # reported here https://github.com/gilesknap/gphotos-sync/issues/89
        if self.shared_albums:
            self.index_albums_type(self._api.sharedAlbums.list.execute,
                                   'sharedAlbums', "Shared (titled) Albums",
                                   False, True)
        self.index_albums_type(self._api.albums.list.execute,
                               'albums', "Albums", True, self.album_index)

    def index_albums_type(self, api_function: Callable, item_key: str,
                          description: str, allow_null_title: bool,
                          add_media_items: bool):
        """
        query google photos interface for a list of all albums and index their
        contents into the db
        """
        log.warning('Indexing {} ...'.format(description))

        # there are no filters in album listing at present so it always a
        # full rescan - it's quite quick

        count = 0
        response = api_function(pageSize=50)
        while response:
            results = response.json()
            for album_json in results.get(item_key, []):
                count += 1

                album = GoogleAlbumMedia(album_json)
                indexed_album = self._db.get_album(album_id=album.id)
                already_indexed = indexed_album.size == album.size if \
                    indexed_album else False

                if self.album and self.album != album.orig_name:
                    log.debug('Skipping Album: %s, photos: %d '
                              '(does not match --album)', album.filename,
                              album.size)
                elif not allow_null_title and album.description == 'none':
                    log.debug('Skipping no-title album, photos: %d',
                              album.size)
                elif already_indexed and not self.flush:
                    log.debug('Skipping Album: %s, photos: %d', album.filename,
                              album.size)
                else:
                    log.info('Indexing Album: %s, photos: %d', album.filename,
                             album.size)
                    first_date, last_date = self.fetch_album_contents(
                        album.id, add_media_items)
                    # write the album data down now we know the contents'
                    # date range
                    gar = GoogleAlbumsRow.from_parm(
                        album.id, album.filename, album.size,
                        first_date, last_date)
                    self._db.put_row(gar, update=indexed_album)

                    # re-indexing means the local links are out of date: remove
                    # links in preparation for create_album_content_links
                    if indexed_album:
                        old_album_folder = self.album_folder_name(
                            indexed_album.filename, indexed_album.create_date)
                        if old_album_folder.exists():
                            log.debug('removing previous album folder %s',
                                      old_album_folder)
                            shutil.rmtree(old_album_folder)

            next_page = results.get('nextPageToken')
            if next_page:
                response = api_function(pageSize=50,
                                        pageToken=next_page)
            else:
                break
        log.warning('Indexed %d %s', count, description)

    def album_folder_name(self, album_name: str, end_date: datetime) -> Path:
        year = Utils.safe_str_time(end_date, '%Y')
        month = Utils.safe_str_time(end_date, '%m%d')

        rel_path = u"{0} {1}".format(month, album_name)
        link_folder: Path = self._links_root / year / rel_path
        return link_folder

    def create_album_content_links(self):
        log.warning("Creating album folder links to media ...")
        count = 0
        album_item = 0
        current_rid = ''
        if self._links_root.exists() and self.flush:
            log.debug('removing previous album links tree')
            shutil.rmtree(self._links_root)
        re_download = not self._links_root.exists()

        for (path, file_name, album_name, end_date_str, rid, created) in \
                self._db.get_album_files(download_again=re_download):
            if current_rid == rid:
                album_item += 1
            else:
                self._db.put_album_downloaded(rid)
                current_rid = rid
                album_item = 0
            end_date = Utils.string_to_date(end_date_str)
            full_file_name = self._root_folder / path / file_name

            link_folder: Path = self.album_folder_name(album_name, end_date)

            link_file = link_folder / "{:04d}_{}".format(album_item, file_name)
            # incredibly, pathlib.Path.relative_to cannot handle
            # '../' in a relative path !!! reverting to os.path
            relative_filename = os.path.relpath(full_file_name,
                                                str(link_folder))
            log.debug('adding album link %s -> %s', relative_filename,
                      link_file)
            try:
                if not link_folder.is_dir():
                    log.debug('new album folder %s', link_folder)
                    link_folder.mkdir(parents=True)

                created_date = Utils.string_to_date(created)
                if self._use_hardlinks:
                    if full_file_name.exists():
                        os.link(full_file_name, link_file)
                    else:
                        log.debug('skip hardlink for %s, not downloaded',
                                  file_name)
                else:
                    link_file.symlink_to(relative_filename)

                if link_file.exists():
                    count += 1
                    # Windows tries to follow symlinks even though we specify
                    # follow_symlinks=False. So disable setting of link date
                    # if follow not supported
                    if os.utime in os.supports_follow_symlinks:
                        os.utime(str(link_file),
                                 (Utils.safe_timestamp(created_date),
                                  Utils.safe_timestamp(created_date)),
                                 follow_symlinks=False)

            except FileExistsError:
                log.error('bad link to %s', full_file_name)

        log.warning("Created %d new album folder links", count)
