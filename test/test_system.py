from unittest import TestCase
from test_setup import SetupDbAndCredentials
from LocalData import LocalData
import os
import datetime
from mock import patch


# todo currently the system tests work against my personal google drive
# todo will try to provide a standalone account and credentials for CI
class TestSystem(TestCase):
    def test_system_download_name(self):
        s = SetupDbAndCredentials()
        # get a single file
        args = ['--drive-file', '20170102_094337.jpg',
                '--skip-picasa', '--skip-video']
        s.test_setup('system_download_name', args=args, trash_files=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        db.cur.execute("SELECT COUNT() FROM SyncFiles WHERE MediaType = 0;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 1)

        db.cur.execute("SELECT FileName FROM SyncFiles WHERE MediaType = 0;")
        name = db.cur.fetchone()
        self.assertEqual(name[0], '20170102_094337.jpg')

        expected_file = os.path.join(
            s.root, 'drive/2017/01/20170102_094337.jpg')
        self.assertEqual(True, os.path.exists(expected_file))

        args = ['--drive-file', '20170102_094337.jpg', '--skip-video',
                '--skip-picasa', '--all-drive', '--flush-index']
        s.test_setup('system_download_name', args=args, trash_files=True)
        s.gp.start(s.parsed_args)

        expected_file = os.path.join(
            s.root, 'drive/Google Photos/2017/01/20170102_094337.jpg')
        self.assertEqual(True, os.path.exists(expected_file))

    def test_system_index(self):
        # this will get a few files and two albums which include some of those
        s = SetupDbAndCredentials()
        args = ['--start-date', '2017-08-30',
                '--end-date', '2017-09-04',
                '--index-only', '--skip-video']
        s.test_setup('system_index', args=args, trash_db=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        db.cur.execute("SELECT COUNT() FROM SyncFiles WHERE MediaType = 0;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 39)

        db.cur.execute("SELECT COUNT() FROM AlbumFiles;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 22)

        db.cur.execute("SELECT COUNT() FROM Albums;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 2)

    def test_system_index_picasa(self):
        s = SetupDbAndCredentials()
        # this date range includes two above albums but excludes the photos
        # so they will go in the picasa folder
        args = ['--start-date', '2017-09-03',
                '--end-date', '2017-09-04',
                '--index-only', '--skip-video']
        s.test_setup('system_index_picasa', args=args, trash_db=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        db.cur.execute("SELECT COUNT() FROM SyncFiles WHERE MediaType = 1;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 22)

        db.cur.execute("SELECT COUNT() FROM AlbumFiles;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 22)

    def test_system_index_movies(self):
        s = SetupDbAndCredentials()
        # this query gets some 'creations' Movies and a folder containing them
        args = ['--album', 'TestMovies',
                '--index-only',
                '--skip-drive']
        s.test_setup('system_index_movies', args=args, trash_db=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        db.cur.execute("SELECT COUNT() FROM SyncFiles WHERE MediaType = 1;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 20)

        db.cur.execute("SELECT COUNT() FROM AlbumFiles;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 20)

    def test_system_incremental(self):
        s = SetupDbAndCredentials()
        args = ['--end-date', '2015-10-11',
                '--skip-picasa',
                '--index-only',
                '--skip-video']
        s.test_setup('system_incremental', args=args, trash_db=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        db.cur.execute("SELECT COUNT() FROM SyncFiles WHERE MediaType = 0;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 680)

        (d_date, _) = db.get_scan_dates()
        self.assertEqual(d_date.date(), datetime.date(2015, 10, 10))

        args = [
            '--end-date', '2015-10-12',
            '--skip-picasa',
            '--index-only', '--skip-video'
        ]
        s.test_setup('system_incremental', args=args)
        s.gp.start(s.parsed_args)

        db.cur.execute("SELECT COUNT() FROM SyncFiles WHERE MediaType = 0;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 680 + 2229)

        (d_date, _) = db.get_scan_dates()
        self.assertEqual(d_date.date(), datetime.date(2015, 10, 11))

    # noinspection PyUnresolvedReferences
    @patch.object(LocalData, 'get_album')
    def test_system_inc_picasa(self, get_album):
        s = SetupDbAndCredentials()

        # mock get album to pretend a full scan has occurred on 2020-08-28
        get_album.return_value = (None, None, None, "2020-08-28 00:00:00")
        args = ['--end-date', '2000-01-01',
                '--skip-drive',
                '--index-only']
        s.test_setup('system_inc_picasa', args=args, trash_files=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 0)

        # mock get album to pretend a full scan has occurred on 2017-08-28
        get_album.return_value = (None, None, None, "2017-08-28 00:00:00")
        args = ['--skip-drive', '--end-date', '2017-09-12',
                '--index-only', '--skip-video']
        s.test_setup('system_inc_picasa', args=args)
        s.gp.start(s.parsed_args)

        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 82)
        db.cur.execute("SELECT COUNT() FROM Albums;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 4)
