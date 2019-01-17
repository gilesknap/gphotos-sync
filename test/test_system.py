import datetime
import glob
import os
from unittest import TestCase

from mock import patch

import gphotos.Utils as Utils
from gphotos.LocalData import LocalData
import test.test_setup as ts


# todo add a test that reads in Sync Date from the Db
# todo add code coverage tests
# todo tidy up the test account and make these tests match a neater set of files

class TestSystem(TestCase):
    def test_sys_whole_library(self):
        """Download all images in test library. Check filesystem for correct files
        Check DB for correct entries
        Note, if you select --skip-video then we use the search API instead of list
        This then misses these 3 files:
            subaru1.jpg|photos/1998/10
            subaru2.jpg|photos/1998/10
            DSCF0030.JPG|photos/2000/02
        todo investigate above
        """
        s = ts.SetupDbAndCredentials()
        s.test_setup('test_sys_whole_library', trash_db=True, trash_files=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        # Total of 80 media items
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(80, count[0])
        # with 10 videos
        db.cur.execute("SELECT COUNT() FROM SyncFiles where MimeType like 'video%'")
        count = db.cur.fetchone()
        self.assertEqual(10, count[0])

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
        albums = [r'0101?Album?2001', r'0528?Movies', r'0923?Clones', r'0926?Album?2016']
        for idx, a in enumerate(albums):
            pat = os.path.join(s.root, 'albums', '*', a, '*')
            print('looking for album items at {}'.format(pat))
            self.assertEqual(album_items[idx], len(glob.glob(pat)))

    def test_system_index_albums(self):
        s = ts.SetupDbAndCredentials()
        # todo fix for more useful dates when search by create date available
        args = ['--start-date', '2016-01-01',
                '--end-date', '2017-09-19',
                '--index-only', '--skip-video']
        s.test_setup('test_system_index_albums', args=args, trash_db=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        # album files: 4 albums with 26 files, 6 overlap and 10 are videos = 10
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(31, count[0])

        # album files includes the overlaps = 16
        db.cur.execute("SELECT COUNT() FROM AlbumFiles;")
        count = db.cur.fetchone()
        self.assertEqual(52, count[0])

    def test_system_index(self):
        s = ts.SetupDbAndCredentials()
        args = ['--start-date', '2016-01-01',
                '--end-date', '2017-09-19',
                '--index-only', '--skip-video']
        s.test_setup('system_index', args=args, trash_db=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        # 70 items but 10 are videos = 60
        db.cur.execute("SELECT COUNT() FROM SyncFiles WHERE MediaType = 0;")
        count = db.cur.fetchone()
        self.assertEqual(31, count[0])

        # 4 albums with 26 files 10 are videos = 16
        db.cur.execute("SELECT COUNT() FROM AlbumFiles;")
        count = db.cur.fetchone()
        self.assertEqual(52, count[0])

        db.cur.execute("SELECT COUNT() FROM Albums;")
        count = db.cur.fetchone()
        self.assertEqual(7, count[0])

    def test_system_incremental(self):
        s = ts.SetupDbAndCredentials()
        args = ['--end-date', '1970-01-01',
                '--index-only',
                '--skip-video']
        s.test_setup('system_incremental', args=args, trash_db=True)
        s.gp.start(s.parsed_args)

        db = LocalData(s.root)

        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(10, count[0])

        d_date = db.get_scan_date()
        self.assertEqual(d_date.date(), datetime.date(1965, 1, 1))

        args = [
            '--end-date', '2017-09-19',
            '--index-only', '--skip-video'
        ]
        s.test_setup('system_incremental', args=args)
        s.gp.start(s.parsed_args)

        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        self.assertEqual(268, count[0])

        d_date = db.get_scan_date()
        self.assertEqual(d_date.date(), datetime.date(2017, 9, 19))

    # # noinspection PyUnresolvedReferences
    # @patch.object(LocalData, 'get_album')
    # def test_system_inc_picasa(self, get_album):
    #     s = SetupDbAndCredentials()
    #
    #     # mock get album to pretend a full scan has occurred on 2020-08-28
    #     get_album.return_value = LocalData.AlbumsRow.make(
    #         SyncDate=Utils.string_to_date('2020-08-28 00:00:00'))
    #     args = ['--end-date', '2000-01-01',
    #             '--skip-drive',
    #             '--index-only']
    #     s.test_setup('system_inc_picasa', args=args, trash_files=True)
    #     s.gp.start(s.parsed_args)
    #
    #     db = LocalData(s.root)
    #
    #     db.cur.execute("SELECT COUNT() FROM SyncFiles")
    #     count = db.cur.fetchone()
    #     self.assertEqual(count[0], 0)
    #
    #     # TODO need to add some photos to the test account that make this more
    #     # meaningful. Currently they all have the same modified date 2017-09-18
    #
    #     # mock get album to pretend a full scan has occurred on 2017-09-17
    #     get_album.return_value = LocalData.AlbumsRow.make(
    #         SyncDate=Utils.string_to_date('2017-09-17 00:00:00'))
    #     args = ['--skip-drive', '--end-date', '2017-09-19',
    #             '--index-only', '--skip-video']
    #     s.test_setup('system_inc_picasa', args=args)
    #     s.gp.start(s.parsed_args)
    #
    #     db.cur.execute("SELECT COUNT() FROM SyncFiles")
    #     count = db.cur.fetchone()
    #
    #     # 4 albums with 26 entries, 10 are videos and 6 overlap = 10
    #     self.assertEqual(count[0], 10)
    #     db.cur.execute("SELECT COUNT() FROM Albums;")
    #     count = db.cur.fetchone()
    #     self.assertEqual(count[0], 4)
    #
    # def test_picasa_delete(self):
    #     s = SetupDbAndCredentials()
    #     args = ['--album', '2Photos',
    #             '--skip-drive', '--do-delete']
    #     s.test_setup('test_picasa_delete', args=args, trash_files=True)
    #     s.gp.start(s.parsed_args)
    #
    #     pat = os.path.join(s.root, 'picasa', '2016', '01', '*.*')
    #     self.assertEqual(2, len(glob.glob(pat)))
    #
    #     s.test_setup('test_picasa_delete', args=args)
    #     s.gp.picasa_sync.check_for_removed()
    #     self.assertEqual(2, len(glob.glob(pat)))
    #
    #     db = LocalData(s.root)
    #     db.cur.execute("DELETE FROM SyncFiles WHERE MediaType = 1;")
    #     db.store()
    #
    #     s.gp.picasa_sync.check_for_removed()
    #     self.assertEqual(0, len(glob.glob(pat)))
    #
    # # todo really need to get drive api v3 working and use create date for
    # # date filtering. at present the indexing filters by modify date and then
    # # the download filters by create date - not good
    # def test_drive_delete(self):
    #     s = SetupDbAndCredentials()
    #     args = ['--start-date', '2017-01-01', '--end-date', '2017-09-19',
    #             '--skip-picasa', '--do-delete', '--skip-video']
    #     s.test_setup('test_drive_delete', args=args, trash_files=True)
    #
    #     pat = os.path.join(s.root, 'drive', 'Google Photos', '2017', '*.*')
    #     print(pat)
    #
    #     s.gp.start(s.parsed_args)
    #     self.assertEqual(10, len(glob.glob(pat)))
    #
    #     s.test_setup('test_drive_delete', args=args)
    #     s.gp.drive_sync.check_for_removed()
    #     self.assertEqual(10, len(glob.glob(pat)))
    #
    #     db = LocalData(s.root)
    #     db.cur.execute("DELETE FROM SyncFiles WHERE MediaType = 0 "
    #                    "AND Filename LIKE '%201701%';")
    #     db.store()
    #
    #     s.gp.drive_sync.check_for_removed()
    #     self.assertEqual(0, len(glob.glob(pat)))
