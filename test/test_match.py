from unittest import TestCase
from test_setup import SetupDbAndCredentials
from LocalData import LocalData
import os


# todo currently the system tests work against my personal google drive
# todo will try to provide a standalone account and credentials
class SystemMatch(TestCase):

    def test_system_match(self):
        s = SetupDbAndCredentials()
        # this date range includes two above albums but excludes the photos
        # so they will go in the picasa folder
        args = [
            '--start-date', '1998-10-07',
            '--end-date', '1998-10-08',
            '--drive-file', 'f1.jpg'
            '--'
        ]
        s.test_setup('test_system_index_names', args=args, trash_files=True)
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
