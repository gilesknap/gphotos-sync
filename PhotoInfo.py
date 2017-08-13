import gdata.gauth
import gdata.photos.service
import datetime


# https://developers.google.com/oauthplayground/ helpful for testing and
# understanding oauth2


class PhotoInfo:
    PHOTOS_QUERY = '/data/feed/api/user/default/albumid/{0}?kind=photo'

    def __init__(self, args, db):
        self.db = db
        self.args = args
        self.gdata_client = None
        self.credentials = None
        self.auth2token = None

    def match_drive_photo(self, filename, timestamp, size):
        for use_create_date in [False, True]:
            for hour_offset in range(2):
                date = datetime.datetime.fromtimestamp(
                    int(timestamp) / 1000 - 3600 *
                    hour_offset).strftime(
                    '%Y-%m-%d %H:%M:%S')
                file_keys = self.db.find_drive_file(filename, date, None,
                                                    use_create_date)
                if file_keys and len(file_keys) > 1:
                    # narrow search on file size
                    file_keys = self.db.find_drive_file(filename, date, size,
                                                        use_create_date)
                if file_keys:
                    return file_keys
        # not found anything yet.
        # MP4s and other non exif files have no date try on name and size only
        file_keys = self.db.find_drive_file(filename, None, size)
        return file_keys

    def get_albums(self):
        albums = self.gdata_client.GetUserFeed()
        for album in albums.entry:
            print('----------------------- Album title: %s, number of photos:"'
                  ' %s, id: %s' % (album.title.text,
                                   album.numphotos.text,
                                   album.gphoto_id.text))
            if album.title.text == 'Auto-Backup':
                continue

            for retry in range(5):
                try:
                    q = PhotoInfo.PHOTOS_QUERY.format(album.gphoto_id.text)
                except Exception as e:
                    print("\nRETRYING due to", e)
                    continue
                break

            photos = self.gdata_client.GetFeed(q)
            for photo in photos.entry:
                name = photo.title.text
                if '-ANIMATION' in name or '-PANO' in name or '-COLLAGE' in \
                        name or '-EFFECTS' in name:
                    # drive does not see these Google Photos creations
                    # Todo could download using gdata api for these
                    continue
                file_keys = self.match_drive_photo(name,
                                                   photo.timestamp.text,
                                                   int(photo.size.text))

                if not file_keys:
                    date = datetime.datetime.fromtimestamp(
                        int(photo.timestamp.text) / 1000).strftime(
                        '%Y-%m-%d %H:%M:%S')
                    print('WARNING cant find album file %s %s %s' %
                          (photo.title.text, date, photo.size.text))
                elif len(file_keys) > 1:
                    print ('WARNING multiple album file match for %s %s %s' %
                           (photo.title.text, date, photo.size.text))
            ('Album count %d' % len(albums.entry))
        return albums

    def connect_photos(self, credentials):
        self.credentials = credentials
        self.auth2token = gdata.gauth.OAuth2TokenFromCredentials(credentials)
        gd_client = gdata.photos.service.PhotosService()
        gd_client = self.auth2token.authorize(gd_client)
        gd_client.additional_headers = {
            'Authorization': 'Bearer %s' % credentials.access_token}
        self.gdata_client = gd_client
