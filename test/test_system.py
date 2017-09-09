from unittest import TestCase
from test_setup import SetupDbAndCredentials
from LocalData import LocalData
import os


# todo currently the system tests work against my personal google drive
# todo will try to provide a standalone account and credentials
class System(TestCase):

    def test_system_download_name(self):
        s = SetupDbAndCredentials()
        # get a single file
        args = [
            '--drive-file', '20170102_094337.jpg',
            '--skip-picasa'
        ]
        s.test_setup('test_system_download_name', args=args, trash_files=True)
        s.gp.start(s.parsed_args)

        # verify db contents
        db = LocalData(s.root)
        results = db.get_files_by_search(media_type=0)
        count = 0
        for _ in results:
            count += 1
        self.assertEqual(count, 1)

        results = db.get_album_files()
        count = 0
        for _ in results:
            count += 1
        self.assertEqual(count, 0)
        expected_file = os.path.join(
            s.root, 'drive/2017/01/20170102_094337.jpg')
        self.assertEqual(True, os.path.exists(expected_file))

    def test_system_index(self):
        # this will get a few files and two albums which include some of those
        s = SetupDbAndCredentials()
        args = [
            '--start-date', '2017-08-30',
            '--end-date', '2017-09-04',
            '--index-only'
        ]
        s.test_setup('system_index', args=args, trash_db=True)
        s.gp.start(s.parsed_args)

        # verify db contents
        db = LocalData(s.root)
        results = db.get_files_by_search(media_type=0)
        count = 0
        for _ in results:
            count += 1
        self.assertEqual(count, 39)

        results = db.get_album_files()
        count = 0
        for _ in results:
            count += 1
        self.assertEqual(count, 22)
        # todo also count 2 albums

    def test_system_index_picasa(self):
        s = SetupDbAndCredentials()
        # this date range includes two above albums but excludes the photos
        # so they will go in the picasa folder
        args = [
            '--start-date', '2017-09-03',
            '--end-date', '2017-09-04',
            '--index-only'
        ]
        s.test_setup('system_index_picasa', args=args, trash_db=True)
        s.gp.start(s.parsed_args)

        # verify db contents
        db = LocalData(s.root)
        results = db.get_files_by_search(media_type=1)
        count = 0
        for _ in results:
            count += 1
        self.assertEqual(count, 22)

        results = db.get_album_files()
        count = 0
        for _ in results:
            count += 1
        self.assertEqual(count, 22)

    def test_system_index_movies(self):
        s = SetupDbAndCredentials()
        # this query gets some 'creations' Movies and a folder containing them
        args = [
            '--album', 'TestMovies',
            '--include-video',
            '--index-only',
            '--skip-drive'
        ]
        s.test_setup('test_system_index_movies', args=args, trash_db=True)
        s.gp.start(s.parsed_args)

        # verify db contents
        db = LocalData(s.root)
        results = db.get_files_by_search(media_type=1)
        count = 0
        for _ in results:
            count += 1
        self.assertEqual(count, 20)

        results = db.get_album_files()
        count = 0
        for _ in results:
            count += 1
        self.assertEqual(count, 20)
        # todo also count  1 albums

    def test_system_incremental(self):
        s = SetupDbAndCredentials()
        args = [
            '--end-date', '2015-10-11',
            '--skip-picasa',
            '--index-only'
        ]
        s.test_setup('test_system_incremental', args=args, trash_db=True)
        s.gp.start(s.parsed_args)

        # verify db contents
        db = LocalData(s.root)
        with db:
            results = db.get_files_by_search(media_type=0)
            count = 0
            for _ in results:
                count += 1
            self.assertEqual(count, 680)

            (d_date, _) = db.get_scan_dates()
            self.assertEqual(d_date.year, 2015)
            self.assertEqual(d_date.month, 10)
            self.assertEqual(d_date.day, 10)

        args = [
            '--end-date', '2015-10-12',
            '--skip-picasa',
            '--index-only'
        ]
        s.test_setup('test_system_incremental', args=args)
        s.gp.start(s.parsed_args)

        # verify db contents
        db = LocalData(s.root)
        with db:
            results = db.get_files_by_search(media_type=0)
            count = 0
            for _ in results:
                count += 1
            self.assertEqual(count, 680 + 2229)

            (d_date, _) = db.get_scan_dates()
            self.assertEqual(d_date.year, 2015)
            self.assertEqual(d_date.month, 10)
            self.assertEqual(d_date.day, 11)
