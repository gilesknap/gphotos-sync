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
                file_key = None
                for hour_offset in range(2):
                    date = datetime.datetime.fromtimestamp(
                        int(photo.timestamp.text) / 1000 - 3600 *
                        hour_offset).strftime(
                        '%Y-%m-%d %H:%M:%S')
                    filename = photo.title.text
                    file_key = self.db.get_file_by_name_date(filename, date)
                    if file_key:
                        break
                if not file_key:
                    # try to match on create date
                    file_key = self.db.get_file_by_name_date(filename, date)
                if not file_key:
                    date = datetime.datetime.fromtimestamp(
                        int(photo.timestamp.text) / 1000).strftime(
                        '%Y-%m-%d %H:%M:%S')
                    print('cant find album file %s %s' %
                          (photo.title.text, date))
                    # todo temp test for particular file
                    assert ('2013-01-04 14.33.44.jpg' != photo.title.text)
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
