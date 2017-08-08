import gdata.gauth
import gdata.photos.service

# https://developers.google.com/oauthplayground/ helpful for testing and
# understanding oauth2


class PhotoInfo:
    PHOTOS_QUERY = '/data/feed/api/user/default/albumid/{0}?kind=photo'

    def __init__(self):
        self.gdata_client = None
        self.credentials = None
        self.auth2token = None

    def get_albums(self):
        albums = self.gdata_client.GetUserFeed(limit=10)
        for album in albums.entry:
            print('title: %s, number of photos:"'
                  ' %s, id: %s' % (album.title.text,
                                   album.numphotos.text,
                                   album.gphoto_id.text))
            q = PhotoInfo.PHOTOS_QUERY.format(album.gphoto_id.text)
            if album.title.text == 'Test123':
                photos = self.gdata_client.GetFeed(q)
                for photo in photos.entry:
                    print(photo)
        print('Album count %d' % len(albums.entry))
        return albums

    def connect_photos(self, credentials):
        self.credentials = credentials
        self.auth2token = gdata.gauth.OAuth2TokenFromCredentials(credentials)
        gd_client = gdata.photos.service.PhotosService()
        gd_client = self.auth2token.authorize(gd_client)
        gd_client.additional_headers = {
            'Authorization': 'Bearer %s' % credentials.access_token}
        self.gdata_client = gd_client
