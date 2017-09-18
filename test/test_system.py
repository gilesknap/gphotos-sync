import datetime
import glob
import os
from unittest import TestCase

from mock import patch

from LocalData import LocalData
from test_setup import SetupDbAndCredentials
import Utils


# todo add a test that reads in Sync Date from the Db
# todo add code coverage tests

# todo currently the system tests work against my personal google drive
# todo will try to provide a standalone account and credentials for CI
class TestSystem(TestCase):
    def test_system_download_album(self):
        s = SetupDbAndCredentials()
        # get a small Album
        args = ['--album', 'Bats!',
                '--skip-drive']
        s.test_setup('system_download_album', args=args, trash_files=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)
        db.cur.execute("SELECT COUNT() FROM SyncFiles WHERE MediaType = 1;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 2)

        expected_file = os.path.join(s.root, 'albums', '2017', '0901 Bats!')
        print(expected_file)
        self.assertEqual(True, os.path.exists(expected_file))

        pat = os.path.join(s.root, 'picasa', '2017', '09', '*.*')
        self.assertEqual(2, len(glob.glob(pat)))

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
        db.con.close()

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
        self.assertEqual(count[0], 20)

        db.cur.execute("SELECT COUNT() FROM Albums;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 1)

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
        self.assertEqual(count[0], 20)

        db.cur.execute("SELECT COUNT() FROM AlbumFiles;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 20)

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
        self.assertEqual(count[0], 19)

        db.cur.execute("SELECT COUNT() FROM AlbumFiles;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 19)

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
        get_album.return_value = LocalData.AlbumsRow.make(
            SyncDate=Utils.string_to_date('2020-08-28 00:00:00'))
        args = ['--end-date', '2000-01-01',
                '--skip-drive',
                '--index-only']
        s.test_setup('system_inc_picasa', args=args, trash_files=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 0)

        # mock get album to pretend a full scan has occurred on
        get_album.return_value = LocalData.AlbumsRow.make(
            SyncDate=Utils.string_to_date('2017-08-28 00:00:00'))
        args = ['--skip-drive', '--end-date', '2017-09-12',
                '--index-only', '--skip-video']
        s.test_setup('system_inc_picasa', args=args)
        s.gp.start(s.parsed_args)

        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 80)
        db.cur.execute("SELECT COUNT() FROM Albums;")
        count = db.cur.fetchone()
        self.assertEqual(count[0], 2)

    def test_picasa_delete(self):
        s = SetupDbAndCredentials()
        args = ['--album', 'Bats!',
                '--skip-drive', '--do-delete']
        s.test_setup('test_picasa_delete', args=args, trash_files=True)
        s.gp.start(s.parsed_args)

        pat = os.path.join(s.root, 'picasa', '2017', '09', '*.*')
        self.assertEqual(2, len(glob.glob(pat)))

        s.test_setup('test_picasa_delete', args=args)
        s.gp.picasa_sync.check_for_removed()
        self.assertEqual(2, len(glob.glob(pat)))

        db = LocalData(s.root)
        db.cur.execute("DELETE FROM SyncFiles WHERE MediaType = 1;")
        db.store()

        s.gp.picasa_sync.check_for_removed()
        self.assertEqual(0, len(glob.glob(pat)))

    def test_drive_delete(self):
        s = SetupDbAndCredentials()
        args = ['--start-date', '2017-09-13', '--end-date', '2017-09-15',
                '--skip-picasa', '--do-delete']
        s.test_setup('test_drive_delete', args=args, trash_files=True)
        s.gp.start(s.parsed_args)

        pat = os.path.join(s.root, 'drive', '2017', '09', '*.*')
        self.assertEqual(6, len(glob.glob(pat)))

        s.test_setup('test_drive_delete', args=args)
        s.gp.drive_sync.check_for_removed()
        self.assertEqual(6, len(glob.glob(pat)))

        db = LocalData(s.root)
        db.cur.execute("DELETE FROM SyncFiles WHERE MediaType = 0 "
                       "AND Filename LIKE 'IMG_20170914_08%';")
        db.store()

        s.gp.drive_sync.check_for_removed()
        self.assertEqual(2, len(glob.glob(pat)))
