import shutil
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, Mock, PropertyMock

from gphotos.GooglePhotosIndex import GooglePhotosIndex
from gphotos.LocalData import LocalData
import test.test_setup as ts
from test.test_account import TestAccount


class TestSystem(TestCase):
    def test_no_album_index(self):
        """for issue #89 - photos directly uploaded into albums dont 'list'"""
        s = ts.SetupDbAndCredentials()
        args = ['--no-album-index', '--skip-shared-albums', '--index-only']
        s.test_setup('test_no_album_index', trash_files=True,
                     trash_db=True, args=args)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        # There are 95 items but 10 were uploaded direct into a folder
        # so --no-album-index may affect them (but does not)
        # Also 5 are shared from another account (skipped due to
        # --skip-shared-albums AND --no-album-index)
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        # this was an attempt to prove that creating a folder and uploading
        # directly to it in google photos web would reproduce
        # https://github.com/gilesknap/gphotos-sync/issues/89
        # if it had done so then we would only get 80 files
        t = TestAccount.image_count + TestAccount.video_count
        self.assertEqual(
            t, count[0],
            "expected {} files with album index off".format(t)
        )

    @patch.object(GooglePhotosIndex, 'PAGE_SIZE', new_callable=PropertyMock)
    def test_zero_items_in_response(self, page_size):
        """
        for issue https://github.com/gilesknap/gphotos-sync/issues/112
        """
        # note this fails with page size below 5 and that might be another API
        # bug
        # to emulate issue #112 remove the date range and set page_size = 2
        # this then does download everything via media_items.list but sometimes
        # gets zero items with a next_page token (too expensive on quota to
        # always leave it like this.)
        page_size.return_value = 6

        s = ts.SetupDbAndCredentials()
        args = ['--skip-albums', '--index-only',
                '--start-date', '1965-01-01',
                '--end-date', '1965-12-31']
        s.test_setup('test_zero_items_in_response', trash_files=True,
                     trash_db=True, args=args)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(
            10, count[0],
            "expected 10 images 1965"
        )

    def test_folder_not_writeable(self):
        # make sure we get permissions error and not 'database is locked'
        s = ts.SetupDbAndCredentials()
        s.test_setup('test_folder_not_writeable', trash_files=True,
                     trash_db=True)
        try:
            s.root.chmod(0o444)
            with self.assertRaises(PermissionError):
                s.gp.main([str(s.root), '--skip-shared-albums'])
        finally:
            s.root.chmod(0o777)
            shutil.rmtree(str(s.root))
