#!/usr/bin/env python2
# coding: utf8
import os.path
import shutil
import urllib
from datetime import timedelta, datetime

import gdata.gauth
import gdata.photos.service

import Utils
from AlbumMedia import AlbumMedia
from LocalData import LocalData
from PicasaMedia import PicasaMedia
from gphotos.DatabaseMedia import DatabaseMedia, MediaType
import logging

log = logging.getLogger('gphotos.picasa')


# noinspection PyCompatibility
class PicasaSync(object):
    """A Class for managing the indexing and download of media via the
    picasa web API.
    """
    # noinspection SpellCheckingInspection
    PHOTOS_QUERY = '/data/feed/api/user/default/albumid/{0}'
    BLOCK_SIZE = 1000
    ALBUM_MAX = 10000  # picasa web api gets 500 err after approx 10000 files
    HIDDEN_ALBUMS = [u'Profile Photos']
    ALL_FILES_ALBUMS = [u'Auto Backup']

    def __init__(self, credentials, root_folder, db, flush_albums):
        """

        :param (OAutCredentials) credentials:
        :param (str) root_folder:
        :param (LocalData) db:
        :param (bool) flush_albums:
        """
        self._root_folder = root_folder
        self._db = db
        self._gdata_client = None
        self._credentials = credentials
        self.flush_albums = flush_albums
        self._auth2token = gdata.gauth.OAuth2TokenFromCredentials(credentials)

        gd_client = gdata.photos.service.PhotosService()
        orig_request = gd_client.http_client.request
        gd_client = self._auth2token.authorize(gd_client)
        gd_client = Utils.patch_http_client(self._auth2token, gd_client,
                                            orig_request)
        gd_client.additional_headers = {
            'Authorization': 'Bearer %s' % self._credentials.access_token}
        self._gdata_client = gd_client

        # public members to be set after init
        self.startDate = None
        self.endDate = None
        self.album_name = None
        self.includeVideo = False

    def download_picasa_media(self):
        log.info(u'Downloading Picasa Only Files ...')
        # noinspection PyTypeChecker
        for media in DatabaseMedia.get_media_by_search(
                self._root_folder, self._db, media_type=MediaType.PICASA,
                start_date=self.startDate, end_date=self.endDate,
                skip_linked=True):
            if os.path.exists(media.local_full_path):
                continue

            log.info(u"Downloading %s ..." % media.local_full_path)
            tmp_path = os.path.join(media.local_folder, '.gphotos.tmp')

            if not os.path.isdir(media.local_folder):
                os.makedirs(media.local_folder)

            res = Utils.retry(5, urllib.urlretrieve, media.url, tmp_path)
            if res:
                os.rename(tmp_path, media.local_full_path)
                # set the access date to create date since there is nowhere
                # else to put it on linux (and is useful for debugging)
                os.utime(media.local_full_path,
                         (Utils.to_timestamp(media.modify_date),
                          Utils.to_timestamp(media.create_date)))
            else:
                log.warning(u"WARNING: failed to download %s", media.local_path)

    def create_album_content_links(self):
        log.info(u"Creating album folder links to media ...")
        # the simplest way to handle moves or deletes is to clear out all links
        # first, these are quickly recreated anyway
        links_root = os.path.join(self._root_folder, 'albums')
        if os.path.exists(links_root):
            log.debug(u'removing previous album links tree')
            shutil.rmtree(links_root)

        for (path, file_name, album_name, end_date) in \
                self._db.get_album_files():
            if album_name in self.ALL_FILES_ALBUMS:
                continue

            full_file_name = os.path.join(path, file_name)

            year = Utils.safe_str_time(Utils.string_to_date(end_date), '%Y')
            month = Utils.safe_str_time(Utils.string_to_date(end_date), '%m%d')

            rel_path = u"{0} {1}".format(month, album_name)
            link_folder = unicode(os.path.join(links_root, year, rel_path))
            link_file = unicode(os.path.join(link_folder, file_name))

            original_link_file = link_file
            duplicates = 0
            while os.path.exists(link_file):
                duplicates += 1
                link_file = '{} ({})'.format(original_link_file, duplicates)

            log.debug(u'adding album link %s -> %s', full_file_name,
                      link_file)
            if not os.path.isdir(link_folder):
                log.debug(u'new album folder %s', link_folder)
                os.makedirs(link_folder)
            os.symlink(full_file_name, link_file)

        log.info(u"album links done.")

    # this will currently do nothing unless using --flush-db
    def check_for_removed(self):
        # note for partial scans using date filters this is still OK because
        # for a file to exist it must have been indexed in a previous scan
        log.info(u'Finding deleted media ...')
        top_dir = os.path.join(self._root_folder, PicasaMedia.MEDIA_FOLDER)
        for (dir_name, _, file_names) in os.walk(top_dir):
            for file_name in file_names:
                file_id = self._db.get_file_by_path(dir_name, file_name)
                if not file_id:
                    name = os.path.join(dir_name, file_name)
                    os.remove(name)
                    log.warning(u"%s deleted", name)

    def match_drive_photo(self, media):
        sync_row = self._db.find_file_ids_dates(size=media.size,
                                                media_type=MediaType.DRIVE)
        if sync_row and len(sync_row) == 1:
            return sync_row

        sync_row = self._db.find_file_ids_dates(filename=media.filename,
                                                media_type=MediaType.DRIVE)
        if sync_row and len(sync_row) == 1:
            return sync_row

        if sync_row and len(sync_row) > 1:
            sync_row = self._db.find_file_ids_dates(filename=media.filename,
                                                    size=media.size,
                                                    media_type=MediaType.DRIVE)
            # multiple matches here represent the same image (almost certainly!)
            if sync_row:
                return sync_row[0:1]

        sync_row = self._match_by_date(media)
        if sync_row:
            log.warning(u'MATCH BY DATE on %s %s', media.filename,
                        media.modify_date)
            return sync_row

        # not found anything or found >1 result
        return sync_row

    def _match_by_date(self, media, media_type=None):
        """
        Now only use create date here - picasweb modify date is unreliable

        :param (PicasaMedia) media: media item to find a match on
        :param (MediaType) media_type: type of media to search for
        :return ([(str, str)]): list of (file_id, date)
        """

        sync_row = None
        for hour_offset in range(-1, 1):
            date_to_check = media.modify_date + timedelta(hours=hour_offset)
            sync_row = self._db.find_file_ids_dates(
                filename=media.filename,
                exif_date=date_to_check,
                use_create=True,
                media_type=media_type)

        return sync_row

    def index_album_media(self, limit=None):
        """
        query picasa web interface for a list of all albums and index their
        contents into the db
        :param (int) limit: only scan this number of albums (for testing)
        """
        log.info(u'Indexing Albums ...')
        albums = Utils.retry(10, self._gdata_client.GetUserFeed, limit=limit)
        log.info(u'Album count %d', len(albums.entry))

        if self.flush_albums:
            log.debug(u"removing all album links from db (--flush-index)")
            self._db.remove_all_album_files()

        helper = IndexAlbumHelper(self)

        for p_album in albums.entry:
            album = AlbumMedia(p_album)
            helper.setup_next_album(album)
            if helper.skip_this_album():
                continue
            log.info(u'Album: %s, photos: %d, updated: %s, published: %s',
                     album.filename, album.size, album.modify_date,
                     album.create_date)

            # noinspection SpellCheckingInspection
            q = p_album.GetPhotosUri() + "&imgmax=d"

            # Each iteration below processes a BLOCK_SIZE list of photos
            start_entry = 1
            limit = PicasaSync.BLOCK_SIZE
            while True:
                photos = Utils.retry(10, self._gdata_client.GetFeed, q,
                                     limit=limit, start_index=start_entry)
                completed = helper.index_photos(photos)
                if completed:
                    break

                start_entry += limit
                if len(photos.entry) < limit:
                    break
                if start_entry >= PicasaSync.ALBUM_MAX:
                    log.warning(u"LIMITING ALBUM TO %d entries",
                                PicasaSync.ALBUM_MAX)
                    break
                if start_entry + PicasaSync.BLOCK_SIZE > PicasaSync.ALBUM_MAX:
                    limit = PicasaSync.ALBUM_MAX - start_entry

            helper.complete_album()
        helper.complete_scan()

        # todo is this correct
        log.info(u'Total Album Photos in Drive %d, Picasa %d, multiples %d',
                 helper.total_photos, helper.total_photos,
                 helper.multiple_match_count)

        # Making this a 'friend' class of


# PicasaSync by ignoring protected access
# noinspection PyProtectedMember
class IndexAlbumHelper:
    """
    This class is simply here to break up the logic of indexing albums into
    readable sized functions. I allow it to access private members of the
    parent class PicasaSync.
    """

    def __init__(self, picasa_sync):
        # Initialize members global to the whole scan
        self.p = picasa_sync
        self.total_photos = 0
        self.new_picasa_photos = 0
        self.drive_photos = 0
        self.multiple_match_count = 0
        (_, self.latest_download) = self.p._db.get_scan_dates()
        if not self.latest_download:
            self.latest_download = Utils.minimum_date()

        # declare members that are per album within the scan
        self.album = None
        self.album_end_photo = None
        self.album_start_photo = None
        self.sync_date = None

    def setup_next_album(self, album):
        """
        Initialize members that are per album within the scan.

        :param (AlbumMedia) album:
        """
        self.album = album
        self.album_end_photo = Utils.minimum_date()
        self.album_start_photo = album.modify_date
        self.sync_date = self.p._db.get_album(self.album.id).SyncDate
        if self.sync_date:
            self.sync_date = self.sync_date
        else:
            self.sync_date = Utils.minimum_date()

        # start up the album processing
        self.total_photos += int(album.size)

    def skip_this_album(self):
        if (self.p.album_name and self.p.album_name !=
            self.album.filename) or self.album.filename in \
                PicasaSync.HIDDEN_ALBUMS:
            return True
        if self.p.endDate:
            if Utils.string_to_date(self.p.endDate) < self.album.modify_date:
                return True
        if self.p.startDate:
            if Utils.string_to_date(self.p.startDate) > self.album.modify_date:
                return True
        # handle incremental backup but allow startDate to override
        if not self.p.startDate:
            if self.album.modify_date < self.sync_date:
                return True
        if int(self.album.size) == 0:
            return True
        return False

    def set_album_dates(self, photo_date):
        # make the album dates cover the range of its contents
        if self.album_end_photo < photo_date:
            self.album_end_photo = photo_date
        if self.album_start_photo > photo_date:
            self.album_start_photo = photo_date

    def index_photos(self, photos):
        completed = False
        for photo in photos.entry:
            picasa_media = PicasaMedia(None, self.p._root_folder, photo)

            if picasa_media.create_date < self.latest_download and \
                    self.album.filename in PicasaSync.HIDDEN_ALBUMS:
                completed = True
                break

            if (not self.p.includeVideo) and \
                    picasa_media.mime_type.startswith('video/'):
                continue

            self.set_album_dates(picasa_media.create_date)
            log.debug(u'checking %s is indexed', picasa_media.local_full_path)
            picasa_row = picasa_media.is_indexed(self.p._db)
            if picasa_row:
                # modify dates seem quite random in picasa listings and since
                # they cannot reliably compare with drive dates I currently do
                # not check for changes in modify date - drive always wins on
                # a match. (*) see below
                picasa_row_id = picasa_row.Id
                log.debug(u"Already indexed: %s", picasa_media.local_full_path)
            else:
                self.new_picasa_photos += 1
                log.info(u"New index for %d %s", self.new_picasa_photos,
                         picasa_media.local_full_path)
                picasa_row_id = picasa_media.save_to_db(self.p._db)
                if self.new_picasa_photos % 1000 == 0:
                    self.p._db.store()

            log.debug(u'searching for drive match on {}'.format(
                picasa_media.filename))
            drive_rows = self.p.match_drive_photo(picasa_media)
            count, row = (len(drive_rows), drive_rows[0]) if drive_rows \
                else (0, None)

            # experiments have proved that dates of matching drive and picasa
            # files can be out by a matter of days and in either direction
            # even if the files have not been edited in either. Thus I take the
            # decision to always choose drive if there is a match and thus
            # any edits in google photos are not backed up
            #
            # if a workaround is found then the below should have date
            # comparison restored as should (*) above
            if count == 0:
                # no match, link to the picasa file
                log.info(u'unmatched %s', picasa_media.local_full_path)
                self.p._db.put_album_file(self.album.id, picasa_row_id)
            else:
                # store link between album and drive file
                log.debug(u'matched %s', picasa_media.local_full_path)
                self.p._db.put_album_file(self.album.id, drive_rows[0].Id)
                # store the link between picasa and related drive file
                # this also flags it as not requiring download
                self.p._db.put_symlink(picasa_row_id, drive_rows[0].Id)

                if count > 1:
                    self.multiple_match_count += 1
                    log.warning(u'WARNING multiple files match %s %s %s',
                                picasa_media.orig_name,
                                picasa_media.modify_date,
                                picasa_media.size)
        return completed

    def complete_album(self):
        # write the album data down now we know the contents' date range
        row = LocalData.AlbumsRow.make(AlbumId=self.album.id,
                                       AlbumName=self.album.filename,
                                       StartDate=self.album_start_photo,
                                       EndDate=self.album_end_photo,
                                       SyncDate=Utils.date_to_string(
                                           datetime.now()))
        log.debug(u'completed album %s', self.album.filename)
        self.p._db.put_album(row)
        if self.album.modify_date > self.latest_download:
            self.latest_download = self.album.modify_date

    def complete_scan(self):
        # save the latest and earliest update times. We only do this if a
        # complete scan of all existing albums has completed because the order
        # of albums is a little randomized (possibly by photo content?)
        if not (self.p.album_name or self.p.startDate or self.p.endDate):
            self.p._db.set_scan_dates(picasa_last_date=self.latest_download)
