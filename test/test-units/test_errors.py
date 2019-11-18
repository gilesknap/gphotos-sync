import os

import pytest
from mock import patch, PropertyMock
from pathlib import Path
from unittest import TestCase

import gphotos.authorize as auth
from gphotos.DbRow import DbRow
from gphotos.DatabaseMedia import DatabaseMedia
from gphotos.BaseMedia import BaseMedia
import test.test_setup as ts
from gphotos.LocalData import LocalData
from gphotos.Checks import (
    symlinks_supported,
    is_case_sensitive,
    get_max_path_length, get_max_filename_length)

photos_root = Path('photos')
albums_root = Path('albums')
comparison_root = Path('comparison')


class TestErrors(TestCase):
    """
    Tests to cover failure paths to complete test coverage
    Also used to cover unusual paths such as Windows os, pure virtual classes
    etc.
    """

    @patch(
        'gphotos.authorize.OAuth2Session.fetch_token',
        return_value='dummy_token_string'
    )
    @patch(
        'gphotos.authorize.input',
        return_value='dummy_response_string'
    )
    def test_authorize(self, fetch_patched, input_patched):
        scope = [
            'https://www.googleapis.com/auth/photoslibrary.readonly',
            'https://www.googleapis.com/auth/photoslibrary.sharing',
        ]

        bad_file: Path = Path(__file__).absolute().parent.parent / \
            'test_credentials' / '.no-token-here'
        token_file: Path = Path(__file__).absolute().parent.parent / \
            'test_credentials' / '.gphotos.token'
        secrets_file: Path = Path(__file__).absolute().parent.parent / \
            'test_credentials' / 'client_secret.json'
        test_data: Path = Path(__file__).absolute().parent.parent / 'test-data'

        if bad_file.exists():
            bad_file.unlink()
        with pytest.raises(SystemExit) as test_wrapped_e:
            a = auth.Authorize(scope, bad_file, bad_file)
        assert test_wrapped_e.type == SystemExit

        a = auth.Authorize(scope, bad_file, secrets_file)
        res = a.load_token()
        assert res is None

        a.authorize()
        assert a.token == 'dummy_token_string'

    def test_base_media(self):
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

        with patch(
                'gphotos.BaseMedia.os_name',
                new_callable=PropertyMock(return_value='nt')
        ):
            assert b.validate_encoding('hello.txt') == 'hello.txt'

        """Download archived images in test library using flat folders (and
        windows file name restrictions)
        """
        s = ts.SetupDbAndCredentials()
        args = [
            '--archived', '--skip-albums',
            '--start-date', '2019-10-01', '--use-flat-path'
        ]
        s.test_setup('test_base_media', args=args,
                     trash_files=True, trash_db=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        # Total of 1 out of media items
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(1, count[0])

        pat = str(photos_root / '2019-11' / '*.*')
        files = sorted(s.root.glob(pat))
        self.assertEqual(1, len(files))

    def test_checks(self):
        a_path = Path('/tmp')
        with patch(
                'gphotos.Checks.Path.symlink_to',
                side_effect=FileNotFoundError()
        ):
            assert symlinks_supported(a_path) is False

        with patch(
                'gphotos.Checks.Path.unlink',
                return_value=True
        ):
            assert is_case_sensitive(a_path) is False

        with patch(
                'gphotos.Checks.subprocess.check_output',
                side_effect=BaseException()
        ):
            assert get_max_path_length(a_path) == 248

        if os.name != 'nt':
            with patch(
                    'gphotos.Checks.os.statvfs',
                    side_effect=BaseException()
            ):
                assert get_max_filename_length(a_path) == 248

    def test_database_media(self):
        d = DatabaseMedia()

        assert d.url is None
        assert d.location is None

    def test_db_row(self):
        d = DbRow(None)
        b = BaseMedia()

        with pytest.raises(NotImplementedError):
            x = d.to_media()

        with pytest.raises(NotImplementedError):
            x = d.from_media(b)

        with pytest.raises(ValueError):
            x = d.make(bad_column=1)


