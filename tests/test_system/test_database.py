from unittest import TestCase

from gphotos_sync.LocalData import LocalData
from tests.test_setup import SetupDbAndCredentials


class DatabaseTest(TestCase):
    def test_new_schema(self):
        """
        check that the database initialization errors if the version of the
        data store is newer than the code version
        UPDATE: use --fave so that we do download a photo. A previous bug
        was only picked up when this replaced --skip-files"""
        with SetupDbAndCredentials() as s:
            # get a single file
            args = ["--favourites-only", "--skip-albums"]
            s.test_setup("new_schema", args=args, trash_files=True)
            s.gp.start(s.parsed_args)

            db = LocalData(s.root)
            db.cur.execute("UPDATE Globals SET Version = 1.0 WHERE Id IS 1")
            db.store()
            db.con.close()

            s.__exit__()
            s.test_setup("new_schema", args=args)
            s.gp.start(s.parsed_args)

            db = LocalData(s.root)
            db.cur.execute("SELECT Version From Globals WHERE Id IS 1")
            version = float(db.cur.fetchone()[0])
            self.assertEqual(version, LocalData.VERSION)

            db.cur.execute("UPDATE Globals SET Version = 100.0 WHERE Id IS 1")
            db.store()

            with self.assertRaises(ValueError):
                s.__exit__()
                s.test_setup("new_schema", args=args)
