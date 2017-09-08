from unittest import TestCase
from test_setup import SetupDbAndCredentials
from LocalData import LocalData
import os
import glob


class SystemMatch(TestCase):

    def test_system_match(self):
        s = SetupDbAndCredentials()
        # attempting to select files that have issues with matching in album
        # references
        args = [
            '--drive-file', 'subaru',
            '--all-drive',
            '--skip-picasa'
        ]
        s.test_setup('test_system_match', args=args, trash_files=True)
        s.gp.start(s.parsed_args)

        # verify db contents
        db = LocalData(s.root)
        results = db.get_files_by_search(media_type=0)
        count = 0
        for _ in results:
            count += 1
        self.assertEqual(count, 2)

        expected_files = os.path.join(
            s.root, 'drive/Google Photos/9999/Cars/subaru?.jpg')
        count = len(glob.glob(expected_files))
        self.assertEqual(count, 2)

        # interestingly this test works and these files are not selected when
        # not using --all-drive so appearing under Google Photos does not mean
        # you are in the photos 'space'. I may have dropped this folder into
        # google photos using drive web but I think I uploaded them using
        # google photos uploader in which case this is odd.
        # todo Will try re-upload in the new drive backup tool
