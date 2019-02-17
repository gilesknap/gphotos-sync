from _datetime import datetime
from pathlib import Path
from requests import exceptions as exc
import piexif
from unittest import TestCase

import gphotos.authorize as auth
from gphotos.LocalFilesMedia import LocalFilesMedia

scope = [
    'https://www.googleapis.com/auth/photoslibrary.readonly',
    'https://www.googleapis.com/auth/photoslibrary.sharing',
]

token_file = Path(__file__).absolute().parent \
             / 'test_credentials' / '.gphotos.token'
secrets_file = Path(__file__).absolute().parent \
               / 'test_credentials' / 'client_secret.json'
test_data = Path(__file__).absolute().parent / 'test-data'


class TestUnits(TestCase):
    def test_http_500_retries(self):
        a = auth.Authorize(scope, token_file, secrets_file)
        a.authorize()

        start = datetime.now()

        result = a.session.get('https://httpbin.org/status/500',
                               timeout=10)
        self.assertEquals(result.status_code, 500)
        elapsed = datetime.now() - start
        # timeout should not affect the 5 retries
        self.assertLess(elapsed.seconds, 10)

    def test_download_timeout(self):
        a = auth.Authorize(scope, token_file, secrets_file)
        a.authorize()
        retry_error = False
        start = datetime.now()

        try:
            _ = a.session.get('https://httpbin.org//delay/5',
                              stream=True,
                              timeout=.2)
        except exc.ConnectionError as e:
            retry_error = True
            print(e)

        elapsed = datetime.now() - start
        self.assertEquals(retry_error, True)
        # .2 timeout by 5 retries = 1 sec
        self.assertGreater(elapsed.seconds, 1)

    @classmethod
    def dump_exif(cls, p: Path):
        # use this for analysis if struggling to find relevant EXIF tags
        try:
            exif_dict = piexif.load(str(p))
            for ifd in ("0th", "Exif", "GPS", "1st"):
                print('--------', ifd)
                for tag in exif_dict[ifd]:
                    print(piexif.TAGS[ifd][tag], tag,
                          exif_dict[ifd][tag])
        except piexif.InvalidImageDataError:
            print("no EXIF")

    def test_jpg_description(self):
        p = test_data / 'IMG_20190102_112832.jpg'
        lfm = LocalFilesMedia(p)
        self.dump_exif(p)
        self.assertEqual(lfm.description, '')

        p = test_data / '20180126_185832.jpg'
        lfm = LocalFilesMedia(p)
        self.dump_exif(p)
        self.assertEqual(lfm.description, '')

        p = test_data / '1987-JohnWoodAndGiles.jpg'
        lfm = LocalFilesMedia(p)
        self.dump_exif(p)
        self.assertEqual(lfm.description, '')

    def test_jpg_description2(self):
        p = test_data / 'IMG_20180908_132733-gphotos.jpg'
        lfm = LocalFilesMedia(p)
        self.dump_exif(p)
        self.assertEqual(lfm.description, '')

        p = test_data / 'IMG_20180908_132733-insync.jpg'
        lfm = LocalFilesMedia(p)
        self.dump_exif(p)
        self.assertEqual(lfm.description, '')
