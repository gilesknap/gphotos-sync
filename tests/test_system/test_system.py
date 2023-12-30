import os
from datetime import datetime
from pathlib import Path
from typing import List
from unittest import TestCase
from unittest.mock import Mock, patch

from requests.exceptions import HTTPError

import gphotos_sync.Utils as Utils
import tests.test_setup as ts
from gphotos_sync.BadIds import BadIds
from gphotos_sync.GooglePhotosDownload import GooglePhotosDownload  # type: ignore
from gphotos_sync.LocalData import LocalData
from tests.test_account import TestAccount

photos_root = Path("photos")
albums_root = Path("albums")
comparison_root = Path("comparison")


class TestSystem(TestCase):
    def test_sys_favourites_and_dates(self):
        """Download favourite images in test library.
        Also Check that dates are set correctly
        """

        with ts.SetupDbAndCredentials() as s:
            args = ["--favourites-only", "--max-retries", "6", "--max-threads", "2"]
            s.test_setup(
                "test_sys_favourites", args=args, trash_files=True, trash_db=True
            )
            s.gp.start(s.parsed_args)

            db = LocalData(s.root)

            # Total of 1 out of media items
            db.cur.execute("SELECT COUNT() FROM SyncFiles")
            count = db.cur.fetchone()
            self.assertEqual(1, count[0])

            name = s.root / "photos/2017/09/IMG_2117.JPG"
            date = datetime.fromtimestamp(os.path.getmtime(str(name)))
            expected = datetime(2017, 9, 26, 15, 29, 44)
            self.assertEqual(
                expected, date.replace(microsecond=0), "Modify date not set correctly"
            )
            # TODO: this fails on Github Actions - probably its the filesystem
            # rather than the OS
            #
            # if os.name == "nt":
            #     date = datetime.fromtimestamp(os.path.getctime(name))
            #     expected = datetime(2017, 9, 26, 15, 29, 44)
            #     self.assertEqual(
            #         expected,
            #         date.replace(microsecond=0),
            #         "Create date not set correctly",
            #     )

    def ____test_sys_archived(self):
        # TODO archinging not working
        """Download archived images in test library."""
        with ts.SetupDbAndCredentials() as s:
            args = ["--archived", "--skip-albums", "--start-date", "2017-01-01"]
            s.test_setup(
                "test_sys_archived", args=args, trash_files=True, trash_db=True
            )
            s.gp.start(s.parsed_args)

            db = LocalData(s.root)

            # Total of 1 out of media items
            db.cur.execute("SELECT COUNT() FROM SyncFiles")
            count = db.cur.fetchone()
            self.assertEqual(1, count[0])

    def test_shared_albums(self):
        """Download favourite images in test library."""
        with ts.SetupDbAndCredentials() as s:
            args = ["--skip-files"]
            s.test_setup(
                "test_shared_albums", args=args, trash_files=True, trash_db=True
            )
            s.gp.start(s.parsed_args)

            t = (
                TestAccount.album_image_count
                + TestAccount.album_shared_image_count
                + TestAccount.shared_album_image_count
                + TestAccount.shared_album_shared_image_count
            )

            with LocalData(s.root) as db:
                db.cur.execute("SELECT COUNT() FROM AlbumFiles")
                count = db.cur.fetchone()
                self.assertEqual(
                    t,
                    count[0],
                    "expected {} files in all albums including shared".format(t),
                )

        with ts.SetupDbAndCredentials() as s:
            args = ["--skip-files", "--skip-shared-albums"]
            s.test_setup(
                "test_shared_albums", args=args, trash_files=True, trash_db=True
            )
            s.gp.start(s.parsed_args)

            # note that unless we use --no-album-index the shared files in the
            # visible album will show up here
            t = (
                TestAccount.album_image_count + TestAccount.album_shared_image_count
            )  # see above
            with LocalData(s.root) as db:
                db.cur.execute("SELECT COUNT() FROM AlbumFiles")
                count = db.cur.fetchone()
                self.assertEqual(
                    t,
                    count[0],
                    "expected {} files in all albums excluding shared".format(t),
                )

    def test_sys_album_add_file(self):
        """tests that the album links get re-created in a new folder with
        a new last-date prefix when a recent photo is added to an album,
         also that the old folder is removed"""
        with ts.SetupDbAndCredentials() as s:
            args = ["--start-date", "2017-09-19", "--end-date", "2017-09-20"]
            s.test_setup(
                "test_sys_album_add_file", args=args, trash_db=True, trash_files=True
            )
            s.gp.start(s.parsed_args)

            pat = str(albums_root / "2017" / "0923 Clones😀" / "*.*")
            files = sorted(s.root.glob(pat))
            self.assertEqual(4, len(files))

            # spoof the album to pretend it only got 3 files up to 2017-09-20
            db = LocalData(s.root)
            db.cur.execute(
                "UPDATE Albums SET EndDate='2017-09-20',"
                "Size=3 WHERE "
                "AlbumName='Clones😀'"
            )
            db.store()

            args = [
                "--start-date",
                "2017-09-19",
                "--end-date",
                "2017-09-23",
                "--index-only",
            ]
            s.__exit__()
            s.test_setup("test_sys_album_add_file", args=args)
            s.gp.start(s.parsed_args)

            # the rescan will reset the date so set it back
            db = LocalData(s.root)
            db.cur.execute(
                "UPDATE Albums SET EndDate='2017-09-20' " "WHERE AlbumName='Clones😀'"
            )
            db.store()

            args = ["--skip-index", "--skip-files"]
            s.__exit__()
            s.test_setup("test_sys_album_add_file", args=args)
            s.gp.start(s.parsed_args)

            pat = str(albums_root / "2017" / "0920 Clones😀" / "*.*")
            files = sorted(s.root.glob(pat))
            self.assertEqual(4, len(files))
            should_be_gone = s.root / albums_root / "2017" / "0923 Clones😀"
            self.assertFalse(should_be_gone.exists())

            # test --album-date-by-first-photo

            # force re-download of the album
            db.cur.execute(
                "UPDATE Albums SET Downloaded=0 " "WHERE AlbumName='Clones😀'"
            )
            db.store()
            args = ["--skip-index", "--skip-files", "--album-date-by-first-photo"]
            s.__exit__()
            s.test_setup("test_sys_album_add_file", args=args)
            s.gp.start(s.parsed_args)

            pat = str(albums_root / "2017" / "0919 Clones😀" / "*.*")
            files = sorted(s.root.glob(pat))
            self.assertEqual(4, len(files))

            should_be_gone = s.root / albums_root.absolute() / "2017" / "0920 Clones😀"
            self.assertFalse(should_be_gone.exists())

    def test_system_date_range(self):
        with ts.SetupDbAndCredentials() as s:
            args = [
                "--start-date",
                "2016-01-01",
                "--end-date",
                "2017-01-01",
                "--skip-albums",
                "--index-only",
            ]
            s.test_setup(
                "test_system_date_range", args=args, trash_db=True, trash_files=True
            )
            s.gp.start(s.parsed_args)

            db = LocalData(s.root)

            # Total of 10 images
            db.cur.execute("SELECT COUNT() FROM SyncFiles")
            count = db.cur.fetchone()
            self.assertEqual(10, count[0])

        with ts.SetupDbAndCredentials() as s:
            args = [
                "--start-date",
                "2016-01-01",
                "--end-date",
                "2017-01-01",
                "--use-hardlinks",
                "--album",
                "Clones😀",
            ]
            s.test_setup(
                "test_system_hard_link", args=args, trash_db=True, trash_files=True
            )
            s.gp.start(s.parsed_args)

            with LocalData(s.root) as db:
                # Total of 4 images
                db.cur.execute("SELECT COUNT() FROM AlbumFiles")
                count = db.cur.fetchone()
                self.assertEqual(4, count[0])

            pat = str(albums_root / "*" / "*Clones😀" / "*")
            links: List[Path] = sorted(s.root.glob(pat))
            self.assertEqual(4, len(links))
            for link in links:
                self.assertTrue(not link.is_symlink())

            # verify that switching to soft links in the same folder
            # overwrites all hard links
            args = [
                "--start-date",
                "2016-01-01",
                "--end-date",
                "2017-01-01",
                "--album",
                "Clones😀",
                "--flush-index",
            ]
            s.__exit__(self)
            s.test_setup(
                "test_system_hard_link", args=args, trash_db=False, trash_files=False
            )
            s.gp.start(s.parsed_args)

            with LocalData(s.root) as db:
                # Total of 4 images
                db.cur.execute("SELECT COUNT() FROM AlbumFiles")
                count = db.cur.fetchone()
                self.assertEqual(4, count[0])

                pat = str(albums_root / "*" / "*Clones😀" / "*")
                links = sorted(s.root.glob(pat))
                self.assertEqual(4, len(links))
                for link in links:
                    self.assertTrue(link.is_symlink())

    def test_system_skip_video(self):
        with ts.SetupDbAndCredentials() as s:
            args = [
                "--start-date",
                "2017-01-01",
                "--end-date",
                "2018-01-01",
                "--skip-albums",
                "--index-only",
            ]
            s.test_setup(
                "test_system_skip_video", args=args, trash_db=True, trash_files=True
            )
            s.gp.start(s.parsed_args)

            db = LocalData(s.root)
            # Total of 20 media items
            db.cur.execute("SELECT COUNT() FROM SyncFiles")
            count = db.cur.fetchone()
            self.assertEqual(20, count[0])
            db.store()
            del db

        with ts.SetupDbAndCredentials() as s:
            args = [
                "--start-date",
                "2017-01-01",
                "--end-date",
                "2018-01-01",
                "--skip-albums",
                "--index-only",
                "--skip-video",
            ]
            s.test_setup(
                "test_system_skip_video", args=args, trash_db=True, trash_files=True
            )
            s.gp.start(s.parsed_args)

            db = LocalData(s.root)
            # Total of 10 media items
            db.cur.execute("SELECT COUNT() FROM SyncFiles")
            count = db.cur.fetchone()
            self.assertEqual(10, count[0])

    def test_system_retry_download(self):
        with ts.SetupDbAndCredentials() as s:
            # note we do index albums because there was a bug on retrying
            # downloads with albums enabled
            args = [
                "--start-date",
                "2017-01-01",
                "--end-date",
                "2018-01-01",
                "--skip-video",
            ]
            s.test_setup(
                "test_system_retry_download", args=args, trash_db=True, trash_files=True
            )
            s.gp.start(s.parsed_args)

            pat = str(photos_root / "2017" / "??" / "*.[JjpP]*")
            files = sorted(s.root.glob(pat))
            self.assertEqual(15, len(files))

            files[0].unlink()
            files = sorted(s.root.glob(pat))
            self.assertEqual(14, len(files))

        # re-run should not download since file is marked as downloaded
        with ts.SetupDbAndCredentials() as s:
            s.test_setup("test_system_retry_download", args=args)
            s.gp.start(s.parsed_args)

            files = sorted(s.root.glob(pat))
            self.assertEqual(14, len(files))

            # but adding --retry-download should get us back to 10 files
            args.append("--retry-download")
        with ts.SetupDbAndCredentials() as s:
            s.test_setup("test_system_retry_download", args=args)
            s.gp.start(s.parsed_args)

            files = sorted(s.root.glob(pat))

        with ts.SetupDbAndCredentials() as s:
            args = [
                "--start-date",
                "2017-01-01",
                "--end-date",
                "2018-01-01",
                "--skip-video",
                "--skip-albums",
                "--do-delete",
            ]
            s.test_setup("test_do_delete", args=args, trash_db=True, trash_files=True)
            s.gp.start(s.parsed_args)

            pat = str(photos_root / "2017" / "??" / "*.[JjpP]*")
            files = sorted(s.root.glob(pat))
            self.assertEqual(10, len(files))

            db = LocalData(s.root)
            # noinspection SqlWithoutWhere
            db.cur.execute("DELETE FROM SyncFiles;")
            db.store()

            args.append("--skip-index")
        with ts.SetupDbAndCredentials() as s:
            s.test_setup("test_do_delete", args=args)
            s.gp.start(s.parsed_args)

            # should have removed all files
            files = sorted(s.root.glob(pat))
            self.assertEqual(0, len(files))

    def test_system_incremental(self):
        with ts.SetupDbAndCredentials() as s:
            args = [
                "--start-date",
                TestAccount.start,
                "--end-date",
                TestAccount.end,
                "--skip-albums",
                "--index-only",
            ]
            s.test_setup(
                "test_system_incremental", args=args, trash_db=True, trash_files=True
            )
            s.gp.start(s.parsed_args)

            db = LocalData(s.root)
            db.cur.execute("SELECT COUNT() FROM SyncFiles")
            count = db.cur.fetchone()
            self.assertEqual(
                TestAccount.image_count_2016,
                count[0],
                "expected {} items in 2016".format(TestAccount.image_count_2016),
            )

            # force an update to the 'most recently scanned file' record
            # (this is normally only set for complete scans and was tested in
            # test_sys_whole_library)
            db.set_scan_date(Utils.string_to_date("2017-01-01"))
            db.store()

        with ts.SetupDbAndCredentials() as s:
            args = ["--skip-albums", "--index-only"]
            s.test_setup("test_system_incremental", args=args)
            s.gp.start(s.parsed_args)

            # this should add in everything in 2017 onwards (21 files)
            db.cur.execute("SELECT COUNT() FROM SyncFiles")
            count = db.cur.fetchone()
            t = (
                TestAccount.image_count_2016
                + TestAccount.item_count_2017
                + TestAccount.item_count_2020
            )
            self.assertEqual(
                t, count[0], "expected file count from 2016 and 2017 to be {}".format(t)
            )

            d_date = db.get_scan_date()
            self.assertEqual(d_date.date(), TestAccount.latest_date)

        with ts.SetupDbAndCredentials() as s:
            args = ["--skip-albums", "--index-only", "--rescan"]
            s.test_setup("test_system_incremental", args=args)
            s.gp.start(s.parsed_args)

            # this should add in everything
            db.cur.execute("SELECT COUNT() FROM SyncFiles")
            count = db.cur.fetchone()
            t = TestAccount.image_count + TestAccount.video_count
            self.assertEqual(
                t, count[0], "expected a total of {} items after full sync".format(t)
            )

    def test_skip_video_on_album(self):
        """verify that skip video works when syncing a specific folder"""
        with ts.SetupDbAndCredentials() as s:
            args = ["--skip-video", "--album", "Movies"]
            s.test_setup(
                "test_skip_video_on_album", args=args, trash_files=True, trash_db=True
            )
            s.gp.start(s.parsed_args)

            with LocalData(s.root) as db:
                db.cur.execute("SELECT COUNT() FROM AlbumFiles")
                count = db.cur.fetchone()
                self.assertEqual(0, count[0], "expected 0 video files in album Movies")

    @patch.object(GooglePhotosDownload, "do_download_file")
    def test_bad_ids(self, do_download_file):
        do_download_file.side_effect = HTTPError(Mock(status=500), "ouch!")
        with ts.SetupDbAndCredentials() as s:
            args = [
                "--start-date",
                TestAccount.start,
                "--end-date",
                TestAccount.end,
                "--skip-albums",
            ]
            s.test_setup("test_bad_ids", args=args, trash_db=True, trash_files=True)
            s.gp.start(s.parsed_args)
            # check we tried to download 10 times
            self.assertEqual(
                do_download_file.call_count,
                TestAccount.image_count_2016,
                "Expected {} downloads".format(TestAccount.image_count_2016),
            )

            # this should have created a Bad IDs file
            bad_ids = BadIds(s.root)
            self.assertEqual(
                len(bad_ids.items),
                TestAccount.image_count_2016,
                "Expected {} Bad IDs entries".format(TestAccount.image_count_2016),
            )

            do_download_file.reset_mock()

            s.__exit__()
            s.test_setup("test_bad_ids", args=args)
            s.gp.start(s.parsed_args)
            # this should have skipped the bad ids and not tried to download
            self.assertEqual(
                do_download_file.call_count, 0, "Expected 0 calls to do_download"
            )
