from Main import GooglePhotosSyncMain
import sys
from mock import patch
import os.path
import shutil


class SetupDbAndCredentials:
    def __init__(self):
        self.gp = GooglePhotosSyncMain()
        self.parsed_args = None
        self.db_file = None
        self.root = None

    def test_setup(self, test_name, init_db=False, args=None, trash_db=False,
                   trash_files=False):
        self.root = '/tmp/gpTests/{}'.format(test_name)

        self.db_file = os.path.join(self.root, 'gphotos.sqlite')
        if init_db:
            if not os.path.exists(self.root):
                os.makedirs(self.root, 0o700)
            src_folder = os.path.dirname(os.path.abspath(__file__))
            from_file = os.path.join(src_folder, 'testDb1.sqlite')
            shutil.copy(from_file, self.db_file)
        elif trash_files:
            if os.path.exists(self.root):
                shutil.rmtree(self.root)
        elif trash_db:
            if os.path.exists(self.db_file):
                os.remove(self.db_file)

        all_args = [self.root]
        if args:
            all_args += args

        self.parsed_args = self.gp.parser.parse_args(all_args)
        self.gp.setup(self.parsed_args)

    def test_done(self):
        self.gp.data_store.store()
