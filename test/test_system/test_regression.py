from unittest import TestCase

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
