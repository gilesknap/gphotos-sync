import gdata.gauth
import gdata.photos.service
import datetime
import os.path
import urllib
import httplib2
import threading
import time


# https://developers.google.com/oauthplayground/ helpful for testing and
# understanding oauth2


class PhotoInfo:
    PHOTOS_QUERY = '/data/feed/api/user/default/albumid/{0}'
    BLOCK_SIZE = 500
    ALBUM_MAX = 10000  # picasa web api gets 500 response after 10000 files

    def __init__(self, args, db):
        self.db = db
        self.args = args
        self.gdata_client = None
        self.credentials = None
        self.auth2token = None
        self.local_folder = os.path.join(self.args.root_folder, 'picasa')
        if not os.path.exists(self.local_folder):
            os.mkdir(self.local_folder)

    def time_from_timestamp(self, time_secs, hour_offset=0):
        date = datetime.datetime.fromtimestamp(
            int(time_secs) / 1000 - 3600 * hour_offset).strftime(
            '%Y-%m-%d %H:%M:%S')
        return date

    def match_drive_photo(self, filename, timestamp, size):
        file_keys = self.db.find_drive_file(size=size)
        if file_keys and len(file_keys) == 1:
            return file_keys

        file_keys = self.db.find_drive_file(orig_name=filename)
        if file_keys and len(file_keys) == 1:
            return file_keys

        if file_keys and len(file_keys) > 1:
            file_keys = self.db.find_drive_file(orig_name=filename, size=size)
            # multiple matches here represent the same image
            if file_keys:
                return file_keys[0:1]

        # search with date, but check for timezone slips due to camera not
        # set to correct timezone and missing or corrupted exif_date,
        # in which case revert to create date
        for use_create_date in [False, True]:
            for hour_offset in range(-12, 12):
                date = self.time_from_timestamp(timestamp, hour_offset)
                dated_file_keys = \
                    self.db.find_drive_file(orig_name=filename,
                                            exif_date=date,
                                            use_create=use_create_date)
                if dated_file_keys:
                    print("MATCH ON DATE, offset %d (create %r) %s, file: %s" %
                          (hour_offset, use_create_date, date, filename))
                    return dated_file_keys
        # not found anything or found >1 result
        return file_keys

    # todo move to utility module
    @classmethod
    def retry(cls, count, func, *arg, **k_arg):
        for retry in range(count):
            try:
                res = func(*arg, **k_arg)
            except Exception as e:
                print("\nRETRYING due to", e)
                print "Call was:", func, arg, k_arg
                time.sleep(.1)
                continue
            return res

    def define_path(self, date, name, photo_id):
        year = date.strftime('%Y')
        folder = os.path.join(self.local_folder, year)
        if not os.path.exists(folder):
            os.mkdir(folder)

        local_path = os.path.join(folder, photo_id + '-' + name)
        return local_path

    def get_albums(self):
        print('\n----------------- Reading albums ...')
        albums = PhotoInfo.retry(10, self.gdata_client.GetUserFeed)
        total_photos = 0
        mismatched = 0
        multiple = 0

        print('\n----------------- Album count %d' % len(albums.entry))
        for album in albums.entry:
            total_photos += int(album.numphotos.text)
            print('----------------------- Album title: %s, number of photos:'
                  ' %s, id: %s' % (album.title.text,
                                   album.numphotos.text,
                                   album.gphoto_id.text))
            # todo use this flag to make this album not show in local albums
            hide_this_album = album.title.text == 'Auto-Backup'
            if hide_this_album:
                continue

            end_date = self.time_from_timestamp(album.timestamp.text, 0)
            start_date = 0
            album_id = self.db.put_album(album.gphoto_id.text, album.title.text,
                                         start_date, end_date)

            q = album.GetPhotosUri() + "&imgmax=d"

            downloading = True
            start_entry = 1
            limit = PhotoInfo.BLOCK_SIZE
            while downloading:
                photos = PhotoInfo.retry(10, self.gdata_client.GetFeed, q,
                                         limit=limit,
                                         start_index=start_entry)
                # todo very temp download code for testing - will refactor
                # as per GoogleDriveSync
                for photo in photos.entry:
                    date = datetime.datetime.fromtimestamp(
                        int(photo.timestamp.text) / 1000)
                    date_str = date.strftime('%Y-%m-%d %H:%M:%S')
                    item_name = photo.title.text
                    item_url = photo.content.src
                    item_id = photo.gphoto_id.text
                    item_updated = photo.updated.text
                    item_published = photo.published.text

                    # for videos use last (highest res) media.content entry url
                    if photo.media.content:
                        high_res_content = photo.media.content[-1]
                        if high_res_content.type.startswith('video'):
                            if high_res_content.url:
                                item_url = high_res_content.url

                    file_keys = self.match_drive_photo(item_name,
                                                       photo.timestamp.text,
                                                       int(photo.size.text))
                    if not file_keys:
                        print(
                            'WARNING no drive entry for album file %s %s %s' % (
                                photo.title.text, date_str, photo.size.text))
                        mismatched += 1
                        local_path = self.define_path(date, item_name, item_id)

                        if not (self.args.index_only or
                                    os.path.exists(local_path)):
                            print('downloading ...')
                            # todo add a file to SyncFiles and set file_id
                            tmp_path = os.path.join(self.local_folder,
                                                    '.gphoto.tmp')
                            res = self.retry(5, urllib.urlretrieve, item_url,
                                             tmp_path)
                            if res:
                                os.rename(tmp_path, local_path)
                            else:
                                print("failed to download %s" % local_path)
                    elif len(file_keys) > 1:
                        multiple += 1
                        print (
                            'WARNING multiple album file match for %s %s %s' %
                            (item_name, date_str, photo.size.text))
                    else:
                        # OK - just got one record back
                        file_id = file_keys[0]['Id']
                        self.db.put_album_file(album_id, file_id)

                start_entry += PhotoInfo.BLOCK_SIZE
                if start_entry + PhotoInfo.BLOCK_SIZE > PhotoInfo.ALBUM_MAX:
                    limit = PhotoInfo.ALBUM_MAX - start_entry
                    print ("LIMITING ALBUM TO 10000 entries")
                downloading = limit > 0 and PhotoInfo.BLOCK_SIZE == len(
                    photos.entry)

        print('---------Total Photos in Albums %d, mismatched %d, multiples %d'
              % (total_photos, mismatched, multiple))
        return albums

    def connect_photos(self, credentials):
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
