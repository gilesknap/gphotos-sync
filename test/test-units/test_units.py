from _datetime import datetime
from pathlib import Path
from requests import exceptions as exc
from unittest import TestCase
from gphotos.GoogleAlbumMedia import GoogleAlbumMedia
import json

import gphotos.authorize as auth
from gphotos.LocalFilesMedia import LocalFilesMedia

scope = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",
    "https://www.googleapis.com/auth/photoslibrary.sharing",
]

token_file = (
    Path(__file__).absolute().parent.parent / "test_credentials" / ".gphotos.token"
)
secrets_file = (
    Path(__file__).absolute().parent.parent / "test_credentials" / "client_secret.json"
)
test_data = Path(__file__).absolute().parent.parent / "test-data"


class TestUnits(TestCase):
    def test_http_500_retries(self):
        a = auth.Authorize(scope, token_file, secrets_file)
        a.authorize()

        start = datetime.now()

        result = a.session.get("https://httpbin.org/status/500", timeout=10)
        self.assertEqual(result.status_code, 500)
        elapsed = datetime.now() - start
        # timeout should not affect the 5 retries
        self.assertLess(elapsed.seconds, 10)

    def test_download_timeout(self):
        a = auth.Authorize(scope, token_file, secrets_file)
        a.authorize()
        retry_error = False
        start = datetime.now()

        try:
            _ = a.session.get("https://httpbin.org//delay/5", stream=True, timeout=0.2)
        except exc.ConnectionError as e:
            retry_error = True
            print(e)

        elapsed = datetime.now() - start
        self.assertEqual(retry_error, True)
        # .2 timeout by 5 retries = 1 sec
        self.assertGreater(elapsed.seconds, 1)

    def test_jpg_description(self):
        p = test_data / "IMG_20190102_112832.jpg"
        lfm = LocalFilesMedia(p)
        self.assertEqual(lfm.description, "")

        p = test_data / "20180126_185832.jpg"
        lfm = LocalFilesMedia(p)
        self.assertEqual(lfm.description, "")

        p = test_data / "1987-JohnWoodAndGiles.jpg"
        lfm = LocalFilesMedia(p)
        self.assertEqual(lfm.description, "")

    def test_jpg_description2(self):
        p = test_data / "IMG_20180908_132733-gphotos.jpg"
        lfm = LocalFilesMedia(p)
        self.assertEqual(lfm.description, "")

        p = test_data / "IMG_20180908_132733-insync.jpg"
        lfm = LocalFilesMedia(p)
        self.assertEqual(lfm.description, "")

    def test_empty_media(self):
        g = GoogleAlbumMedia(json.loads('{"emptyJson":"0"}'))
        self.assertEqual(0, g.size)
        self.assertEqual("none", g.mime_type)
        self.assertEqual("none", g.description)
        self.assertEqual(None, g.create_date)
        self.assertEqual(None, g.modify_date)
        # noinspection PyBroadException
        try:
            _ = g.url
            assert False, "empty album url should throw"
        except Exception:
            pass
        self.assertEqual(Path("") / "", g.full_folder)
        g.duplicate_number = 1
        self.assertEqual("none (2)", g.filename)
