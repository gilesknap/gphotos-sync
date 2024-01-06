import logging
import shutil
from pathlib import Path

from appdirs import AppDirs

from gphotos_sync import __main__
from gphotos_sync.__main__ import GooglePhotosSyncMain
from gphotos_sync.Checks import do_check

# if we are debugging requests library is too noisy
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)-12s %(levelname)-8s " "%(message)s",
    datefmt="%m-%d %H:%M:%S",
    filemode="w",
)


class SetupDbAndCredentials:
    def __init__(self):
        # set up the test account credentials
        __main__.APP_NAME = "gphotos-sync-test"
        app_dirs = AppDirs(__main__.APP_NAME)
        self.test_folder = Path(__file__).absolute().parent / "test_credentials"
        user_data = Path(app_dirs.user_data_dir)
        if not user_data.exists():
            user_data.mkdir(parents=True)
        user_config = Path(app_dirs.user_config_dir)
        if not user_config.exists():
            user_config.mkdir(parents=True)

        secret_file = self.test_folder / "client_secret.json"
        shutil.copy(secret_file, app_dirs.user_config_dir)

        self.gp = GooglePhotosSyncMain()
        self.parsed_args = None
        self.db_file = None
        self.root = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        self.gp.google_photos_down.close()

    def test_setup(self, test_name, args=None, trash_db=False, trash_files=False):
        self.root = Path("/tmp/gpTests/{}".format(test_name))

        self.db_file = self.root / "gphotos.sqlite"
        if trash_files:
            if self.root.exists():
                shutil.rmtree(self.root)
        elif trash_db:
            self.db_file.unlink()
        if not self.root.exists():
            self.root.mkdir(parents=True)

        do_check(self.root)
        # make retries big so that CI can get past
        #      HTTPError: 429 Client Error: Too Many Requests for url
        # on the google API URLS (when re-running CI frequently)
        all_args = [str(self.root), "--log-level", "error", "--max-retries", "200"]
        if args:
            all_args += args

        credentials_file = self.test_folder / ".gphotos.token"
        shutil.copy(credentials_file, self.root)

        self.parsed_args = self.gp.parser.parse_args(all_args)
        self.parsed_args.root_folder = Path(self.parsed_args.root_folder)
        self.gp.setup(self.parsed_args, Path(self.root))

    def test_done(self):
        self.gp.data_store.store()
