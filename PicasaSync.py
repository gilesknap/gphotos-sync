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
from GoogleMedia import GoogleMedia
from DatabaseMedia import DatabaseMedia, MediaType
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

    def match_drive_photo(self, media):
        file_keys = self.db.find_drive_file_ids(size=media.size)
        if file_keys and len(file_keys) == 1:
            return file_keys

        file_keys = self.db.find_drive_file_ids(filename=media.filename)
        if file_keys and len(file_keys) == 1:
            return file_keys

        if file_keys and len(file_keys) > 1:
            file_keys = self.db.find_drive_file_ids(filename=media.filename,
                                                    size=media.size)
            # multiple matches here represent the same image
            if file_keys:
                return file_keys[0:1]

        # search with date
        # todo need to check for timezone slips due to camera not
        # set to correct timezone and missing or corrupted exif_date,
        # in which case revert to create date
        # todo verify that the above is required in my photos collection
        for use_create_date in [False, True]:
            dated_file_keys = \
                self.db.find_drive_file_ids(filename=media.filename,
                                            exif_date=media.date,
                                            use_create=use_create_date)
            if dated_file_keys:
                print("MATCH ON DATE create %r %s, file: %s" %
                      (use_create_date, media.date, media.orig_name))
                return dated_file_keys
        # not found anything or found >1 result
        return file_keys

    def index_album_media(self, album_name=None, limit=None):
        print('\nAlbums index - Reading albums ...')
        # Todo see if it is possible to query for mod date > last scan
        # todo temp max results for faster testing
        albums = Utils.retry(10, self.gdata_client.GetUserFeed, limit=limit)
        total_photos = multiple = picasa_only = 0
        print('Album count %d\n' % len(albums.entry))

        for album in albums.entry:
            total_photos += int(album.numphotos.text)
            print('Album title: %s, number of photos: %s, id: %s' % (
                album.title.text, album.numphotos.text, album.gphoto_id.text))

            if album_name and album_name != album.title.text \
                    or album.title.text in self.HIDDEN_ALBUMS:
                continue

            start_date = PicasaMedia.parse_date_string(album.published.text)
            end_date = start_date
            album_id = album.gphoto_id.text
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
                        (file_key, date) = file_keys[0]
                        self.db.put_album_file(album_id, file_key)
                        file_date = GoogleMedia.format_date(date)
                        # make the album dates cover the range of its contents
                        if end_date < file_date:
                            end_date = file_date
                        if start_date > file_date:
                            start_date = file_date
                    elif file_keys is None:
                        # no match so this exists only in picasa
                        picasa_only += 1
                        new_file_key = media.save_to_db(self.db)
                        self.db.put_album_file(album_id, new_file_key)
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

            # write the album data down now we know the contents' date range
            self.db.put_album(album_id, album.title.text,
                              start_date, end_date)

        print('Total Album Photos in Drive %d, Picasa %d, multiples %d' % (
            total_photos, picasa_only, multiple))

    def download_album_media(self):
        print('\nDownloading Picasa Only Files ...')
        for media in DatabaseMedia.get_media_by_search(
                self.args.root_folder, self.db, media_type=MediaType.PICASA):
            if os.path.exists(media.local_full_path):
                continue

            # todo add progress bar instead of this print
            print("  Downloading %s ..." % media.local_full_path)
            tmp_path = os.path.join(media.local_folder, '.gphoto.tmp')

            if not os.path.isdir(media.local_folder):
                os.makedirs(media.local_folder)

            res = Utils.retry(5, urllib.urlretrieve, media.url, tmp_path)
            if res:
                os.rename(tmp_path, media.local_full_path)
            else:
                print("  failed to download %s" % media.local_path)

    def create_album_content_links(self):
        for (path, file_name, album_name, end_date) in \
                self.db.get_album_files():
            full_file_name = os.path.join(path, file_name)
            if os.path.exists(full_file_name):
                print("WARNING. Duplicate {0} in {1}".format(
                    full_file_name, album_name))
            else:
                pref = GoogleMedia.format_date(end_date).strftime('%Y/%m%d')
                rel_path = "{0} {1}".format(pref, album_name)
                link_folder = os.path.join(self.args.root_folder, 'albums',
                                           rel_path)
                link_file = os.path.join(link_folder, file_name)

                if not os.path.isdir(link_folder):
                    os.makedirs(link_folder)
                os.symlink(full_file_name, link_file)

