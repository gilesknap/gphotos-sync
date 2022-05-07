import warnings
from pathlib import Path
from unittest import TestCase

import tests.test_setup as ts
from gphotos_sync.LocalData import LocalData
from tests.test_account import TestAccount

photos_root = Path("photos")
albums_root = Path("albums")
comparison_root = Path("comparison")


class TestSystem(TestCase):
    def test_sys_whole_library(self):
        warnings.filterwarnings(
            action="ignore", message="unclosed", category=ResourceWarning
        )
        """Download all images in test library. Check filesystem for correct
        files
        Check DB for correct entries
        Note, if you select --skip-video then we use the search API instead
        of list
        This then misses these 2 files:
            subaru1.jpg|photos/1998/10
            subaru2.jpg|photos/1998/10
        todo investigate above
        """
        with ts.SetupDbAndCredentials() as s:
            s.test_setup("test_sys_whole_library", trash_files=True, trash_db=True)
            s.gp.main([str(s.root), "--skip-shared-albums", "--progress"])

            db = LocalData(s.root)

            db.cur.execute("SELECT COUNT() FROM SyncFiles")
            count = db.cur.fetchone()
            t = (
                TestAccount.image_count
                + TestAccount.video_count
                + TestAccount.shared_image_count
            )
            self.assertEqual(
                t, count[0], "expected {} items excluding shared albums".format(t)
            )

            db.cur.execute("SELECT COUNT() FROM SyncFiles where MimeType like 'video%'")
            count = db.cur.fetchone()
            self.assertEqual(TestAccount.video_count, count[0])

            db.cur.execute("SELECT COUNT() FROM Albums;")
            count = db.cur.fetchone()
            t = TestAccount.album_count
            self.assertEqual(t, count[0], "expected {} total album count".format(t))

            for year, images, shared, videos in zip(
                TestAccount.image_years,
                TestAccount.images_per_year,
                TestAccount.shared_images_per_year,
                TestAccount.videos_per_year,
            ):
                # looking for .jpg .JPG .png .jfif
                pat = str(photos_root / str(year) / "*" / "*.[JjpP]*")
                self.assertEqual(
                    images + shared,
                    len(sorted(s.root.glob(pat))),
                    "mismatch on image file count for year {}".format(year),
                )
                # looking for *.mp4
                pat = str(photos_root / str(year) / "*" / "*.mp4")
                self.assertEqual(
                    videos,
                    len(sorted(s.root.glob(pat))),
                    "mismatch on video file count for year {}".format(year),
                )

            for idx, a in enumerate(TestAccount.album_names):
                pat = str(albums_root / "*" / a / "*")
                t = TestAccount.album_images[idx] + TestAccount.album_shared_images[idx]
                self.assertEqual(
                    t,
                    len(sorted(s.root.glob(pat))),
                    "album {} does not contain {} images".format(
                        a, TestAccount.album_images[idx]
                    ),
                )

            # check that the most recent scanned file date was recorded
            d_date = db.get_scan_date()
            self.assertEqual(d_date.date(), TestAccount.latest_date)

            # check that re-running does not get any db constraint violations etc.
            # also test the comparison feature, by comparing the library with its
            # own gphotos-sync output
            s.__exit__()
            s.test_setup(
                "test_sys_whole_library", args=["--compare-folder", str(s.root)]
            )
            s.gp.start(s.parsed_args)

            # There is one pair of files that are copies of the same image with
            # same UID. This looks like one pair of duplicates and one extra file
            # in the comparison folder. (also the gphotos database etc appear
            # as missing files)
            pat = str(comparison_root / "missing_files" / "*")
            files = sorted(s.root.glob(pat))
            self.assertEqual(0, len(files), "expected 0 missing files")
            pat = str(comparison_root / "extra_files" / "*" / "*" / "*" / "*")
            files = sorted(s.root.glob(pat))
            self.assertEqual(0, len(files), "expected 0 extra files")
            pat = str(comparison_root / "duplicates" / "*")
            files = sorted(s.root.glob(pat))
            self.assertEqual(0, len(files), "expected 0 duplicate files")
