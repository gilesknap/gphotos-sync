import os.path
import shutil

from appdirs import AppDirs

from gphotos import Main
from gphotos.Main import GooglePhotosSyncMain

import logging
# if we are debugging requests library is too noisy
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s '
                           '%(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filemode='w')


class SetupDbAndCredentials:
    def __init__(self):
        # set up the test account credentials
        Main.APP_NAME = 'gphotos-sync-test'
        app_dirs = AppDirs(Main.APP_NAME)
        self.test_folder = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), 'test_credentials')
        if not os.path.exists(app_dirs.user_data_dir):
            os.makedirs(app_dirs.user_data_dir)
        if not os.path.exists(app_dirs.user_config_dir):
            os.makedirs(app_dirs.user_config_dir)

        secret_file = os.path.join(self.test_folder, "client_secret.json")
        shutil.copy(secret_file, app_dirs.user_config_dir)

        self.gp = GooglePhotosSyncMain()
        self.parsed_args = None
        self.db_file = None
        self.root = None

    def test_setup(self, test_name, init_db=False, args=None, trash_db=False,
                   trash_files=False):
        self.root = u'/tmp/gpTests/{}'.format(test_name)

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
        if not os.path.exists(self.root):
            os.makedirs(self.root)

        all_args = [self.root, '--log-level', 'debug']
        if args:
            all_args += args

        credentials_file = os.path.join(self.test_folder, ".gphotos.token")
        shutil.copy(credentials_file, self.root)

        self.parsed_args = self.gp.parser.parse_args(all_args)
        # self.gp.logging(self.parsed_args, self.root)
        self.gp.setup(self.parsed_args, self.root)

    def test_done(self):
        self.gp.data_store.store()
