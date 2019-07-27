import datetime
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, Mock
from requests.exceptions import HTTPError
from typing import List

from gphotos.BadIds import BadIds
from gphotos.GooglePhotosDownload import GooglePhotosDownload
import gphotos.Utils as Utils
from gphotos.LocalData import LocalData
import test.test_setup as ts


class TestSystem(TestCase):
    def test_sys_whole_library2(self):
        """Download all images in test library. Check DB for correct entries
        Note, if you select --start-date then we use the search API instead
        of list
        This then misses these 3 files:
            subaru1.jpg|photos/1998/10
            subaru2.jpg|photos/1998/10
        """
        index = ['--index-only']
        s = ts.SetupDbAndCredentials()
        s.test_setup('test_sys_whole_library2_noparam', trash_files=True,
                     trash_db=True)
        # no parameters downloads everything
        s.gp.main([str(s.root)])

        db = LocalData(s.root)

        # Total of 80 media items
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        print("no params = {} media items".format(count[0]))
        #self.assertEqual(85, count[0])

        s.test_setup('test_sys_whole_library2_datesearch', trash_files=True,
                     trash_db=True)
        # this date SHOULD download everything
        s.gp.main([str(s.root), "--end-date", "2090-01-01"])

        db = LocalData(s.root)

        # Total of 80 media items
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        print("Search with date = {} media items".format(count[0]))
        #self.assertEqual(85, count[0])

        s.test_setup('test_sys_whole_library2_skipshared_noparam',
                     trash_files=True, trash_db=True)
        # this date SHOULD download everything
        s.gp.main([str(s.root), "--skip-shared-albums"])

        db = LocalData(s.root)

        # Total of 80 media items
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        print("Search with date skip shared = {} media items".format(count[0]))
        #self.assertEqual(85, count[0])

        # Total of 80 media items
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        print("Search with date = {} media items".format(count[0]))
        #self.assertEqual(85, count[0])

        s.test_setup('test_sys_whole_library2_skipshared_datesearch',
                     trash_files=True, trash_db=True)
        # this date SHOULD download everything
        s.gp.main([str(s.root), "--end-date", "2090-01-01",
                   "--skip-shared-albums"])

        db = LocalData(s.root)

        # Total of 80 media items
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        print("Search with date skip shared = {} media items".format(count[0]))
        #self.assertEqual(85, count[0])


    def test_temp(self):
        """Download all images in test library. Check DB for correct entries
        Note, if you select --start-date then we use the search API instead
        of list
        This then misses these 3 files:
            subaru1.jpg|photos/1998/10
            subaru2.jpg|photos/1998/10
        """
        s = ts.SetupDbAndCredentials()
        s.test_setup('test_sys_whole_temp2_skipshared_noparam',
                     trash_files=True, trash_db=True)
        # this date SHOULD download everything
        s.gp.main([str(s.root), "--skip-shared-albums"])

        db = LocalData(s.root)

        # Total of 80 media items
        db.cur.execute("SELECT COUNT() FROM SyncFiles")
        count = db.cur.fetchone()
        print("Search with date = {} media items".format(count[0]))
        #self.assertEqual(85, count[0])