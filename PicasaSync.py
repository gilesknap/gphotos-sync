#!/usr/bin/python
# coding: utf8
import gdata.gauth
import gdata.photos.service
import datetime
import os.path
import urllib
import httplib2
import threading
import time
from PicasaMedia import PicasaMedia
from DatabaseMedia import DatabaseMedia
import Utils


class PicasaSync(object):
    PHOTOS_QUERY = '/data/feed/api/user/default/albumid/{0}'
    BLOCK_SIZE = 500
    ALBUM_MAX = 10000  # picasa web api gets 500 response after 10000 files
    HIDDEN_ALBUMS = ['Auto-Backup', 'Profile Photos']

    def __init__(self, credentials, args, db):
        self.db = db
        self.args = args
        self.gdata_client = None
        self.credentials = credentials
        self.auth2token = gdata.gauth.OAuth2TokenFromCredentials(credentials)
        self.refresh_credentials(0)

    def refresh_credentials(self, sleep):
        time.sleep(sleep)
        self.credentials.refresh(httplib2.Http())

        gd_client = gdata.photos.service.PhotosService()
        gd_client = self.auth2token.authorize(gd_client)
        gd_client.additional_headers = {
            'Authorization': 'Bearer %s' % self.credentials.access_token}
        self.gdata_client = gd_client

        expires = self.gdata_client.auth_token.credentials.token_expiry
        now = datetime.datetime.utcnow()
        expires_seconds = (expires - now).seconds

        d = threading.Thread(name='refresh_credentials',
                             target=self.refresh_credentials,
                             args=(expires_seconds - 10,))
        d.setDaemon(True)
        d.start()

    # todo can this be an instance method and not have time_secs parm?
    def time_from_timestamp(self, time_secs, hour_offset=0):
        date = datetime.datetime.fromtimestamp(
            int(time_secs) / 1000 - 3600 * hour_offset).strftime(
            '%Y-%m-%d %H:%M:%S')
        return date

    def match_drive_photo(self, media):
        file_keys = self.db.find_drive_file_ids(size=media.size)
        if file_keys and len(file_keys) == 1:
            return file_keys

        file_keys = self.db.find_drive_file_ids(orig_name=media.orig_name)
        if file_keys and len(file_keys) == 1:
            return file_keys

        if file_keys and len(file_keys) > 1:
            file_keys = self.db.find_drive_file_ids(orig_name=media.orig_name,
                                                    size=media.size)
            # multiple matches here represent the same image
            if file_keys:
                return file_keys[0:1]

        # search with date, but check for timezone slips due to camera not
        # set to correct timezone and missing or corrupted exif_date,
        # in which case revert to create date
        for use_create_date in [False, True]:
            for hour_offset in range(-12, 12):
                dated_file_keys = \
                    self.db.find_drive_file_ids(orig_name=media.orig_name,
                                                exif_date=media.date,
                                                use_create=use_create_date)
                if dated_file_keys:
                    print("MATCH ON DATE, offset %d (create %r) %s, file: %s" %
                          (hour_offset, use_create_date, media.date,
                           media.orig_name))
                    return dated_file_keys
        # not found anything or found >1 result
        return file_keys

    def index_album_media(self, album_name=None):
        print('\nAlbums index - Reading albums ...')
        albums = Utils.retry(10, self.gdata_client.GetUserFeed)
        total_photos = multiple = picasa_only = 0
        print('Album count %d\n' % len(albums.entry))

        for album in albums.entry:
            total_photos += int(album.numphotos.text)
            print('Album title: %s, number of photos: %s, id: %s' % (
                album.title.text, album.numphotos.text, album.gphoto_id.text))

            if album_name and album_name != album.title.text \
                    or album.title.text in self.HIDDEN_ALBUMS:
                continue

            end_date = self.time_from_timestamp(album.timestamp.text, 0)
            start_date = 0
            album_id = self.db.put_album(album.gphoto_id.text,
                                         album.title.text,
                                         start_date, end_date)

            q = album.GetPhotosUri() + "&imgmax=d"

            start_entry = 1
            limit = PicasaSync.BLOCK_SIZE
            while True:
                photos = Utils.retry(10, self.gdata_client.GetFeed, q,
                                     limit=limit, start_index=start_entry)
                for photo in photos.entry:
                    media = PicasaMedia(None, self.args.root_folder, photo)

                    file_keys = self.match_drive_photo(media)
                    if file_keys and len(file_keys) == 1:
                        # store link between album and drive file
                        self.db.put_album_file(album_id, file_keys[0])
                    elif file_keys is None:
                        # no match so this exists only in picasa
                        picasa_only += 1
                        media.save_to_db(self.db)
                        print("  Added %s" % media.local_full_path)
                    else:
                        multiple += 1
                        print ('  WARNING multiple files match %s %s %s' %
                               (media.orig_name, media.date, media.size))

                # prepare offsets for the next block in next iteration
                start_entry += PicasaSync.BLOCK_SIZE
                if start_entry + PicasaSync.BLOCK_SIZE > PicasaSync.ALBUM_MAX:
                    limit = PicasaSync.ALBUM_MAX - start_entry
                    print ("LIMITING ALBUM TO 10000 entries")
                if limit == 0 or len(photos.entry) < limit:
                    break

        print('Total Album Photos in Drive %d, Picasa %d, multiples %d' % (
            total_photos, picasa_only, multiple))

    def download_album_media(self):
        print('\nDownloading Picasa Only Files ...')
        for media in DatabaseMedia.get_media_by_id(
                self.args.root_folder, self.db):
            # todo add progress bar instead of this print
            print("  Downloading %s ..." % media.local_full_path)
            tmp_path = os.path.join(media.local_folder, '.gphoto.tmp')
            # res = Utils.retry(5, urllib.urlretrieve, media.url, tmp_path)
            # if res:
            #     os.rename(tmp_path, media.local_path)
            # else:
            #     print("  failed to download %s" % media.local_path)
