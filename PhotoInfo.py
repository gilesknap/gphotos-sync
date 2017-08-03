import gdata.photos.service
import gdata.media
import gdata.geo
from oauth2client.client import AccessTokenCredentials
from httplib2 import Http


class PhotoInfo():
    def __init__(self):
        self.gdata_client = None
        self.credentials = None

    def get_albums(self):
        albums = self.gdata_client.GetUserFeed(user='xxx@gmail.com')
        for album in albums.entry:
            print('title: %s, number of photos:"'
                  ' %s, id: %s' % (album.title.text,
                                   album.numphotos.text,
                                   album.gphoto_id.text))
        return albums

    def connect_photos(self, credentials):
        self.credentials = AccessTokenCredentials(credentials.access_token,
                                             "MyAgent/1.0", None)

        http = Http()
        http = self.credentials.authorize(http)
        auth2token = gdata.gauth.OAuth2TokenFromCredentials(self.credentials)
        gd_client = gdata.photos.service.PhotosService()
        gd_client = auth2token.authorize(gd_client)
        self.gdata_client = gd_client

# https://stackoverflow.com/questions/16026286/using-oauth2-with-service
# -account-on-gdata-in-python
