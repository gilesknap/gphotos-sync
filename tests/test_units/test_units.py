import json
from datetime import datetime
from os import environ
from os import name as os_name
from pathlib import Path
from unittest import TestCase

import pytest
from requests import exceptions as exc
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import gphotos_sync.authorize as auth
import tests.test_setup as ts
from gphotos_sync.Checks import do_check, get_check
from gphotos_sync.GoogleAlbumMedia import GoogleAlbumMedia
from gphotos_sync.LocalFilesMedia import LocalFilesMedia

is_travis = "TRAVIS" in environ

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

        # speed up error checking by reducing backoff factor
        retry = Retry(
            total=5,
            backoff_factor=0.01,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=frozenset(["GET", "POST"]),
            raise_on_status=False,
            respect_retry_after_header=True,
        )

        a.session.mount("https://", HTTPAdapter(max_retries=retry))

        start = datetime.now()

        result = a.session.get("https://httpbin.org/status/500", timeout=30)
        self.assertEqual(result.status_code, 500)
        elapsed = datetime.now() - start
        # timeout should not affect the 5 retries
        # but backoff_factor=0.001 will (a little)
        self.assertLess(elapsed.seconds, 5)
        a.session.close()

    def test_download_timeout(self):
        a = auth.Authorize(scope, token_file, secrets_file)
        a.authorize()
        retry_error = False
        start = datetime.now()

        # speed up error checking by reducing backoff factor
        retry = Retry(
            total=5,
            backoff_factor=0.2,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=frozenset(["GET", "POST"]),
            raise_on_status=False,
            respect_retry_after_header=True,
        )

        a.session.mount("https://", HTTPAdapter(max_retries=retry))
        try:
            _ = a.session.get("https://httpbin.org//delay/5", stream=True, timeout=0.2)
        except exc.ConnectionError as e:
            retry_error = True
            print(e)

        a.session.close()
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
        do_check(test_data)
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

    def test_bad_filenames(self):
        folder = do_check(test_data)

        filename = folder.valid_file_name("hello.   ")

        if os_name == "nt":
            self.assertEqual(filename, "hello")
        else:
            self.assertEqual(filename, "hello.")
        filename = folder.valid_file_name("hello.😀")
        self.assertEqual(filename, "hello.😀")
        filename = folder.valid_file_name("hello./")
        self.assertEqual(filename, "hello._")

        # patch the checks
        folder.is_linux = False
        folder.is_unicode = False

        filename = folder.valid_file_name("hello.   ")

        self.assertEqual(filename, "hello")
        filename = folder.valid_file_name("hello.😀")
        self.assertEqual(filename, "hello._")
        filename = folder.valid_file_name("hello..")
        self.assertEqual(filename, "hello")

    def test_os_filesystem(self):
        if is_travis:
            pytest.skip(
                "skipping windows filesystem test since travis has no NTFS",
                allow_module_level=True,
            )
        if os_name == "nt":
            # assume there is a c:\ on the test machine (which is likely)
            do_check(Path("C:\\"))
            self.assertFalse(get_check().is_linux)
        else:
            do_check(test_data)
            self.assertTrue(get_check().is_linux)

    def test_fs_overrides(self):
        with ts.SetupDbAndCredentials() as s:
            args = ["--ntfs", "--max-filename", "30"]
            s.test_setup(
                "test_fs_overrides", args=args, trash_db=True, trash_files=True
            )
            s.gp.fs_checks(s.root, s.parsed_args)
            self.assertFalse(get_check().is_linux)
            self.assertEqual(get_check().max_filename, 30)

            if os_name != "nt":
                args = []
                s.test_setup(
                    "test_fs_overrides", args=args, trash_db=True, trash_files=True
                )
                s.gp.fs_checks(s.root, s.parsed_args)
                self.assertTrue(get_check().is_linux)
                self.assertEqual(get_check().max_filename, 255)
