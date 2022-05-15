# type: ignore
import os
from pathlib import Path
from unittest import TestCase

import pytest
from mock import PropertyMock, patch

import gphotos_sync.authorize as auth
import tests.test_setup as ts
from gphotos_sync.BaseMedia import BaseMedia
from gphotos_sync.Checks import do_check
from gphotos_sync.DatabaseMedia import DatabaseMedia
from gphotos_sync.DbRow import DbRow
from gphotos_sync.GoogleAlbumMedia import GoogleAlbumMedia
from gphotos_sync.GoogleAlbumsRow import GoogleAlbumsRow
from gphotos_sync.LocalData import LocalData

photos_root = Path("photos")
albums_root = Path("albums")
comparison_root = Path("comparison")

# todo I'm using assert here and hence do not really need to use TestCae clasee
# I should probably switch to using a consistent approach as per new Diamond
# guidelines which is pytest only with no unittest classes (throughout all test files)


class TestErrors(TestCase):
    """
    Tests to cover failure paths to complete test coverage.
    Also used to cover other unusual paths such as
      Windows os
      pure virtual classes
      etc.
    """

    @patch(
        "gphotos_sync.authorize.InstalledAppFlow.run_local_server",
        return_value="dummy_response_string",
    )
    @patch(
        "gphotos_sync.authorize.InstalledAppFlow.authorized_session",
        return_value="dummy_seaaion",
    )
    def test_authorize(self, local_server, authorized_session):
        scope = [
            "https://www.googleapis.com/auth/photoslibrary.readonly",
            "https://www.googleapis.com/auth/photoslibrary.sharing",
        ]

        bad_file: Path = (
            Path(__file__).absolute().parent.parent
            / "test_credentials"
            / ".no-token-here"
        )
        secrets_file: Path = (
            Path(__file__).absolute().parent.parent
            / "test_credentials"
            / "client_secret.json"
        )
        # test_data: Path = Path(__file__).absolute().parent.parent / 'test-data'
        # token_file: Path = Path(__file__).absolute().parent.parent / \
        #     'test_credentials' / '.gphotos.token'

        if bad_file.exists():
            bad_file.unlink()
        with pytest.raises(SystemExit) as test_wrapped_e:
            a = auth.Authorize(scope, bad_file, bad_file)
        assert test_wrapped_e.type == SystemExit

        a = auth.Authorize(scope, bad_file, secrets_file)
        res = a.load_token()
        assert res is None

    def test_base_media(self):
        """Download archived images in test library using flat folders (and
        windows file name restrictions)
        """
        b = BaseMedia()

        with pytest.raises(NotImplementedError):
            x = b.size

        with pytest.raises(NotImplementedError):
            x = b.id

        with pytest.raises(NotImplementedError):
            x = b.description

        with pytest.raises(NotImplementedError):
            x = b.orig_name

        with pytest.raises(NotImplementedError):
            x = b.create_date

        with pytest.raises(NotImplementedError):
            x = b.modify_date

        with pytest.raises(NotImplementedError):
            x = b.mime_type

        with pytest.raises(NotImplementedError):
            x = b.url
            print(x)  # for pylint

        with ts.SetupDbAndCredentials() as s:
            args = [
                "--skip-albums",
                "--start-date",
                "2020-01-01",
                "--use-flat-path",
            ]
            s.test_setup("test_base_media", args=args, trash_files=True, trash_db=True)
            s.gp.start(s.parsed_args)

            db = LocalData(s.root)

            # Total of 1 out of media items
            db.cur.execute("SELECT COUNT() FROM SyncFiles")
            count = db.cur.fetchone()
            self.assertEqual(1, count[0])

            pat = str(photos_root / "2020-04" / "*.*")
            files = sorted(s.root.glob(pat))
            self.assertEqual(1, len(files))

    @staticmethod
    def test_checks():
        a_path = Path("/tmp")
        c = do_check(a_path)
        assert c.is_linux

        with patch(
            "gphotos_sync.Checks.Path.symlink_to", side_effect=FileNotFoundError()
        ):
            assert not c._symlinks_supported()

        with patch("gphotos_sync.Checks.Path.unlink", side_effect=FileNotFoundError()):
            assert not c._check_case_sensitive()

        with patch("gphotos_sync.Checks.Path.glob", return_value=["a"]):
            assert not c._check_case_sensitive()

        with patch(
            "gphotos_sync.Checks.subprocess.check_output", side_effect=BaseException()
        ):
            assert c._get_max_path_length() == 248

        if os.name != "nt":
            with patch("gphotos_sync.Checks.os.statvfs", side_effect=BaseException()):
                assert c._get_max_filename_length() == 248

        with patch("gphotos_sync.Checks.Path.touch", side_effect=BaseException()):
            assert not c._unicode_filenames()

    @staticmethod
    def test_database_media():
        d = DatabaseMedia()

        assert d.url == ""
        assert d.location == ""

    @staticmethod
    def test_db_row():
        d = DbRow(None)
        b = BaseMedia()

        with pytest.raises(NotImplementedError):
            x = d.to_media()

        with pytest.raises(NotImplementedError):
            x = d.from_media(b)

        with pytest.raises(ValueError):
            x = d.make(bad_column=1)
            print(x)  # for pylint

        if d:
            assert False, "empty DBRow returns true as Bool"

    @staticmethod
    def test_google_albums_media():
        m = GoogleAlbumMedia("")
        g = GoogleAlbumsRow(None)
        g.from_media(m)

    def download_faves(self, expected=4, no_response=False, trash=True):
        # Download favourite images only in test library.
        with ts.SetupDbAndCredentials() as s:
            args = [
                "--album",
                "Clones😀",
                "--use-flat-path",
                "--omit-album-date",
                "--rescan",
            ]
            s.test_setup(
                "test_google_albums_sync", args=args, trash_files=trash, trash_db=trash
            )
            s.gp.start(s.parsed_args)

            with LocalData(s.root) as db:
                # Total of 1 out of media items
                db.cur.execute("SELECT COUNT() FROM SyncFiles")
                count = db.cur.fetchone()
                self.assertEqual(expected, count[0])

    class DummyResponse:
        @staticmethod
        def json():
            return {}

    @patch(
        "gphotos_sync.GoogleAlbumsSync.PAGE_SIZE",
        new_callable=PropertyMock(return_value=1),
    )
    @patch(
        "gphotos_sync.GoogleAlbumsSync.ALBUM_ITEMS",
        new_callable=PropertyMock(return_value=1),
    )
    def test_google_albums_sync(self, page_size, album_items):
        # next page in responses (set pageSize = 1) fetch_album_contents()
        # blank response.json (empty album - add to test data?)
        # also pagesize = 1 in index_albums_type()
        # self._omit_album_date = True
        # self._use_flat_path = True
        # path > Checks.MAX_PATH_LENGTH
        # skip hardlink on non-downloaded file (line 272)
        # file exists already line 290

        # check that next_page functionality works
        # in fetch_album_contents and index_albums_type
        self.download_faves()

        # test file exists already in create_album_content_links
        with patch("shutil.rmtree"):
            self.download_faves(trash=False)

        # check that empty media_json response works
        with patch(
            "gphotos_sync.restclient.Method.execute", return_value=self.DummyResponse()
        ):
            self.download_faves(expected=0)
