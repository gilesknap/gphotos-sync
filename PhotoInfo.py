import gdata.gauth
import gdata.photos.service
import datetime


# https://developers.google.com/oauthplayground/ helpful for testing and
# understanding oauth2


class PhotoInfo:
    PHOTOS_QUERY = '/data/feed/api/user/default/albumid/{0}'

    def __init__(self, args, db):
        self.db = db
        self.args = args
        self.gdata_client = None
        self.credentials = None
        self.auth2token = None

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
            for hour_offset in range(23):
                date = datetime.datetime.fromtimestamp(
                    int(timestamp) / 1000 - 3600 * hour_offset).strftime(
                    '%Y-%m-%d %H:%M:%S')
                dated_file_keys = \
                    self.db.find_drive_file(orig_name=filename,
                                            exif_date=date,
                                            use_create=use_create_date)
                if dated_file_keys:
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
                continue
            return res

    def get_albums(self):
        print('\n----------------- Reading albums ...')
        albums = PhotoInfo.retry(5, self.gdata_client.GetUserFeed)
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
            # if album.title.text == 'Auto-Backup':
            #     # ignore this auto-generated global album
            #     continue

            q = PhotoInfo.PHOTOS_QUERY.format(album.gphoto_id.text)
            photos = PhotoInfo.retry(5, self.gdata_client.GetFeed, q)

            for photo in photos.entry:
                name = photo.title.text
                if '-ANIMATION' in name or '-PANO' in name or '-COLLAGE' in \
                        name or '-EFFECTS' in name:
                    # todo could download using gdata api for these
                    # todo also some are in Drive so need to be more discerning
                    # drive does not see these Google Photos creations
                    continue

                file_keys = self.match_drive_photo(name,
                                                   photo.timestamp.text,
                                                   int(photo.size.text))

                if not file_keys:
                    mismatched += 1
                    date = datetime.datetime.fromtimestamp(
                        int(photo.timestamp.text) / 1000).strftime(
                        '%Y-%m-%d %H:%M:%S')
                    print('WARNING cant find album file %s %s %s' %
                          (photo.title.text, date, photo.size.text))
                elif len(file_keys) > 1:
                    multiple += 1
                    print ('WARNING multiple album file match for %s %s %s' %
                           (name, date, photo.size.text))
        print('---------Total Photos in Albums %d, mismatched %d, multiples %d'
              % (total_photos, mismatched, multiple))
        return albums

    def connect_photos(self, credentials):
        self.credentials = credentials
        self.auth2token = gdata.gauth.OAuth2TokenFromCredentials(credentials)
        gd_client = gdata.photos.service.PhotosService()
        gd_client = self.auth2token.authorize(gd_client)
        gd_client.additional_headers = {
            'Authorization': 'Bearer %s' % credentials.access_token}
        self.gdata_client = gd_client
