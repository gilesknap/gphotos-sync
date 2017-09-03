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
        gd_client = Utils.patch_http_client(self.auth2token, gd_client)
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
        file_keys = self.db.find_file_ids_dates(size=media.size)
        if file_keys and len(file_keys) == 1:
            return file_keys

        file_keys = self.db.find_file_ids_dates(filename=media.filename)
        if file_keys and len(file_keys) == 1:
            return file_keys

        if file_keys and len(file_keys) > 1:
            file_keys = self.db.find_file_ids_dates(filename=media.filename,
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
                self.db.find_file_ids_dates(filename=media.filename,
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
        albums = Utils.retry(10, self.gdata_client.GetUserFeed, limit=limit)
        total_photos = multiple = picasa_only = 0
        print('Album count %d\n' % len(albums.entry))

        for album in albums.entry:
            total_photos += int(album.numphotos.text)
            print('Album title: {}, number of photos: {}, date: {}'.format(
                album.title.text, album.numphotos.text, album.updated.text))

            if album_name and album_name != album.title.text \
                    or album.title.text in self.HIDDEN_ALBUMS:
                continue

            # todo date filtering is too crude at present - if I have changed
            # the title of an old album recently then a scan for recent files
            # would pick it up but its contents would be skipped in the drive
            # phase - Only problem for partially indexed photo stores
            start_date = Utils.string_to_date(album.updated.text)
            if self.args.start_date:
                if Utils.string_to_date(self.args.start_date) > start_date:
                    continue
            if self.args.end_date:
                if Utils.string_to_date(self.args.end_date) < start_date:
                    continue

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
                    # calling is_indexed to make sure duplicate_no is correct
                    # todo remove this when duplicate no handling is moved
                    media.is_indexed(self.db)
                    results = self.match_drive_photo(media)
                    if results and len(results) == 1:
                        # store link between album and drive file
                        (file_key, date) = results[0]
                        self.db.put_album_file(album_id, file_key)
                        file_date = Utils.string_to_date(date)
                        # make the album dates cover the range of its contents
                        if end_date < file_date:
                            end_date = file_date
                        if start_date > file_date:
                            start_date = file_date
                    elif results is None:
                        # no match so this exists only in picasa
                        picasa_only += 1
                        new_file_key = media.save_to_db(self.db)
                        self.db.put_album_file(album_id, new_file_key)
                        print(u"Added {} {}".format(picasa_only,
                                                    media.local_full_path))
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

        print('\nTotal Album Photos in Drive %d, Picasa %d, multiples %d' % (
            total_photos, picasa_only, multiple))

    def download_album_media(self):
        print('\nDownloading Picasa Only Files ...')
        for media in DatabaseMedia.get_media_by_search(
                self.args.root_folder, self.db, media_type=MediaType.PICASA,
                start_date=self.args.start_date, end_date=self.args.end_date):
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
        print("\nCreating album folder links to media ...")
        for (path, file_name, album_name, end_date) in \
                self.db.get_album_files():
            full_file_name = os.path.join(path, file_name)

            prefix = Utils.string_to_date(end_date).strftime('%Y/%m%d')
            rel_path = u"{0} {1}".format(prefix, album_name)
            link_folder = os.path.join(self.args.root_folder, 'albums',
                                       rel_path)

            link_file = os.path.join(link_folder, file_name)
            if not os.path.islink(link_file):
                if not os.path.isdir(link_folder):
                    os.makedirs(link_folder)
                os.symlink(full_file_name, link_file)

        print("album links done.\n")
