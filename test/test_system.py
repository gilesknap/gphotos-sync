import datetime
import glob
import os
from unittest import TestCase
from mock import patch, Mock
from requests.exceptions import HTTPError

from gphotos.BadIds import BadIds
from gphotos.GooglePhotosSync import GooglePhotosSync
import gphotos.Utils as Utils
from gphotos.LocalData import LocalData
import test.test_setup as ts


# todo add a test that reads in Sync Date from the Db
# todo add code coverage tests


class TestSystem(TestCase):
    def test_sys_whole_library(self):
        """Download all images in test library. Check filesystem for correct
        files
        Check DB for correct entries
        Note, if you select --skip-video then we use the search API instead
        of list
        This then misses these 3 files:
            subaru1.jpg|photos/1998/10
            subaru2.jpg|photos/1998/10
            DSCF0030.JPG|photos/2000/02
        todo investigate above
        """
        s = ts.SetupDbAndCredentials()
        s.test_setup('test_sys_whole_library', trash_files=True, trash_db=True)
        s.gp.main([s.root])

        db = LocalData(s.root)

        # Total of 80 media items
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(80, count[0])
        # with 10 videos
        db.cur.execute(
            "SELECT COUNT() FROM SyncFiles where MimeType like 'video%'")
        count = db.cur.fetchone()
        self.assertEqual(10, count[0])
        # and 4 albums
        db.cur.execute("SELECT COUNT() FROM Albums;")
        count = db.cur.fetchone()
        self.assertEqual(4, count[0])

        # downloaded 10 images in each of the years in the test data
        image_years = [2017, 2016, 2015, 2001, 2000, 1998, 1965]
        for y in image_years:
            # looking for .jpg .JPG .png .jfif
            pat = os.path.join(s.root, 'photos', str(y), '*', '*.[JjpP]*')
            self.assertEqual(10, len(glob.glob(pat)))

        # and 10 mp4 for 2017
        pat = os.path.join(s.root, 'photos', '2017', '*', '*.mp4')
        self.assertEqual(10, len(glob.glob(pat)))

        # 4 albums the following item counts
        album_items = [10, 10, 4, 16]
        albums = [r'0101?Album?2001', r'0528?Movies', r'0923?Clones',
                  r'0926?Album?2016']
        for idx, a in enumerate(albums):
            pat = os.path.join(s.root, 'albums', '*', a, '*')
            print('looking for album items at {}'.format(pat))
            self.assertEqual(album_items[idx], len(glob.glob(pat)))

        # check that the most recent scanned file date was recorded
        d_date = db.get_scan_date()
        self.assertEqual(d_date.date(), datetime.date(2017, 9, 26))

    def test_system_date_range(self):
        s = ts.SetupDbAndCredentials()
        args = ['--start-date', '2016-01-01', '--end-date', '2017-01-01',
                '--skip-albums', '--index-only']
        s.test_setup('test_system_date_range', args=args, trash_db=True,
                     trash_files=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        # Total of 10 images
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(10, count[0])

    def test_system_skip_video(self):
        s = ts.SetupDbAndCredentials()
        args = ['--start-date', '2017-01-01', '--end-date', '2018-01-01',
                '--skip-albums', '--index-only']
        s.test_setup('test_system_skip_video', args=args, trash_db=True,
                     trash_files=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)
        # Total of 20 media items
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(20, count[0])
        db.store()
        del db

        s = ts.SetupDbAndCredentials()
        args = ['--start-date', '2017-01-01', '--end-date', '2018-01-01',
                '--skip-albums', '--index-only',
                '--skip-video']
        s.test_setup('test_system_skip_video', args=args, trash_db=True,
                     trash_files=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)
        # Total of 10 media items
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(10, count[0])

    def test_system_retry_download(self):
        s = ts.SetupDbAndCredentials()
        args = ['--start-date', '2017-01-01', '--end-date', '2018-01-01',
                '--skip-video',
                '--skip-albums']
        s.test_setup('test_system_retry_download', args=args, trash_db=True,
                     trash_files=True)
        s.gp.start(s.parsed_args)

        pat = os.path.join(s.root, 'photos', '2017', '??', '*.[JjpP]*')
        files = glob.glob(pat)
        self.assertEqual(10, len(files))

        os.remove(files[0])
        self.assertEqual(9, len(glob.glob(pat)))

        # re-run should not download since file is marked as downloaded
        s = ts.SetupDbAndCredentials()
        s.test_setup('test_system_retry_download', args=args)
        s.gp.start(s.parsed_args)

        self.assertEqual(9, len(glob.glob(pat)))

        # but adding --retry-download should get us back to 10 files
        args.append('--retry-download')
        s = ts.SetupDbAndCredentials()
        s.test_setup('test_system_retry_download', args=args)
        s.gp.start(s.parsed_args)

        self.assertEqual(10, len(glob.glob(pat)))

    def test_do_delete(self):
        s = ts.SetupDbAndCredentials()
        args = ['--start-date', '2017-01-01', '--end-date', '2018-01-01',
                '--skip-video',
                '--skip-albums', '--do-delete']
        s.test_setup('test_do_delete', args=args, trash_db=True,
                     trash_files=True)
        s.gp.start(s.parsed_args)

        pat = os.path.join(s.root, 'photos', '2017', '??', '*.[JjpP]*')
        files = glob.glob(pat)
        self.assertEqual(10, len(files))

        db = LocalData(s.root)
        db.cur.execute("DELETE FROM SyncFiles;")
        db.store()

        args.append('--skip-index')
        s = ts.SetupDbAndCredentials()
        s.test_setup('test_do_delete', args=args)
        s.gp.start(s.parsed_args)

        # should have removed all files
        files = glob.glob(pat)
        self.assertEqual(0, len(files))

    def test_system_incremental(self):
        s = ts.SetupDbAndCredentials()
        args = ['--start-date', '2016-01-01', '--end-date', '2017-01-01',
                '--skip-albums', '--index-only']
        s.test_setup('test_system_incremental', args=args, trash_db=True,
                     trash_files=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(10, count[0])

        # force an update the 'most recently scanned file' record
        # (this is normally only set for complete scans and was tested in
        # test_sys_whole_library)
        db.set_scan_date(Utils.string_to_date("2017-01-01"))
        db.store()

        s = ts.SetupDbAndCredentials()
        args = ['--skip-albums', '--index-only']
        s.test_setup('test_system_incremental', args=args)
        s.gp.start(s.parsed_args)

        # this should add in everything in 2017 (20 files)
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(30, count[0])
        d_date = db.get_scan_date()
        self.assertEqual(d_date.date(), datetime.date(2017, 9, 26))

        s = ts.SetupDbAndCredentials()
        args = ['--skip-albums', '--index-only', '--rescan']
        s.test_setup('test_system_incremental', args=args)
        s.gp.start(s.parsed_args)

        # this should add in everything
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(80, count[0])

    @patch.object(GooglePhotosSync, 'do_download_file')
    def test_bad_ids(self, do_download_file):

        do_download_file.side_effect = HTTPError(Mock(status=500), 'ouch!')
        s = ts.SetupDbAndCredentials()
        args = ['--start-date', '2016-01-01', '--end-date', '2017-01-01',
                '--skip-albums']
        s.test_setup('test_bad_ids', args=args, trash_db=True,
                     trash_files=True)
        s.gp.start(s.parsed_args)
        # check we tried to download 10 times
        self.assertEquals(do_download_file.call_count, 10)

        # this should have created a Bad IDs file
        bad_ids = BadIds(s.root)
        self.assertEquals(len(bad_ids.items), 10)

        s.test_setup('test_bad_ids', args=args)
        s.gp.start(s.parsed_args)
        # this should have skipped the bad ids and not tried to download
        self.assertEquals(do_download_file.call_count, 10)
