# coding: utf8
from argparse import Namespace, ArgumentParser
import logging
import sys
import os
from pathlib import Path

from pkg_resources import DistributionNotFound
from datetime import datetime
from appdirs import AppDirs
from gphotos.GooglePhotosIndex import GooglePhotosIndex
from gphotos.GooglePhotosDownload import GooglePhotosDownload
from gphotos.GoogleAlbumsSync import GoogleAlbumsSync
from gphotos.LocalData import LocalData
from gphotos.authorize import Authorize
from gphotos.restclient import RestClient
from gphotos.LocalFilesScan import LocalFilesScan
from gphotos.LocationUpdate import LocationUpdate
from gphotos import Utils
import pkg_resources

__version__ = pkg_resources.require("gphotos-sync")[0].version

if os.name != 'nt':
    import fcntl

APP_NAME = "gphotos-sync"
log = logging.getLogger(__name__)


class GooglePhotosSyncMain:
    def __init__(self):
        self.data_store: LocalData = None
        self.google_photos_client: RestClient = None
        self.google_photos_idx: GooglePhotosIndex = None
        self.google_photos_down: GooglePhotosDownload = None
        self.google_albums_sync: GoogleAlbumsSync = None
        self.local_files_scan: LocalFilesScan = None
        self.location_update: LocationUpdate = None
        self._start_date = None
        self._end_date = None

        self.auth: Authorize = None

    try:
        version_string = 'version: {}, database schema version {}'.format(
            __version__, LocalData.VERSION)
    except TypeError:
        version_string = '(version not available)'
    except DistributionNotFound:
        version_string = '(version not available under unit tests)'

    parser = ArgumentParser(
        epilog=version_string,
        description="Google Photos download tool")
    parser.add_argument(
        "root_folder",
        help="root of the local folders to download into")
    parser.add_argument(
        "--album",
        action='store',
        help="only synchronize the contents of a single album."
             "use quotes e.g. \"album name\" for album names with spaces")
    parser.add_argument(
        "--logfile",
        action='store',
        help="full path to debug level logfile, default: <root>/gphotos.log."
             "If a directory is specified then a unique filename will be"
             "generated.")
    parser.add_argument(
        "--compare-folder",
        action='store',
        help="root of the local folders to compare to the Photos Library")
    parser.add_argument(
        "--favourites-only",
        action='store_true',
        help="only download media marked as favourite (star)")
    parser.add_argument(
        "--flush-index",
        action='store_true',
        help="delete the index db, re-scan everything")
    parser.add_argument(
        "--rescan",
        action='store_true',
        help="rescan entire library, ignoring last scan date. Use this if you "
             "have added photos to the library that "
             "predate the last sync, or you have deleted some of the local "
             "files")
    parser.add_argument(
        "--retry-download",
        action='store_true',
        help="check for the existence of files marked as already downloaded "
             "and re-download any missing ones. Use "
             "this if you have deleted some local files")
    parser.add_argument(
        "--skip-video",
        action='store_true',
        help="skip video types in sync")
    parser.add_argument(
        "--skip-shared-albums",
        action='store_true',
        help="skip albums that only appear in 'Sharing'")
    parser.add_argument(
        "--start-date",
        help="Set the earliest date of files to sync"
             "format YYYY-MM-DD",
        default=None)
    parser.add_argument(
        "--end-date",
        help="Set the latest date of files to sync"
             "format YYYY-MM-DD",
        default=None)
    parser.add_argument(
        "--log-level",
        help="Set log level. Options: critical, error, warning, info, debug",
        default='warning')
    parser.add_argument(
        "--db-path",
        help="Specify a pre-existing folder for the index database. "
             "Defaults to the root of the local download folders",
        default=None)
    parser.add_argument(
        "--albums-path",
        help="Specify a folder for the albums "
             "Defaults to the 'albums' in the local download folders",
        default='albums')
    parser.add_argument(
        "--photos-path",
        help="Specify a folder for the photo files. "
             "Defaults to the 'photos' in the local download folders",
        default='photos')
    parser.add_argument(
        "--use-flat-path",
        action='store_true',
        help="mandate use of a flat directory structure ('YYYY-MMM') and not "
             "a nested one ('YYYY/MM') . ")
    parser.add_argument(
        "--new-token",
        action='store_true',
        help="Request new token")
    parser.add_argument(
        "--index-only",
        action='store_true',
        help="Only build the index of files in .gphotos.db - no downloads")
    parser.add_argument(
        "--skip-index",
        action='store_true',
        help="Use index from previous run and start download immediately")
    parser.add_argument(
        "--do-delete",
        action='store_true',
        help="""Remove local copies of files that were deleted.
        Must be used with --flush-index since the deleted items must be removed 
        from the index""")
    parser.add_argument(
        "--skip-files",
        action='store_true',
        help="Dont download files, just refresh the album links (for testing)")
    parser.add_argument(
        "--skip-albums",
        action='store_true',
        help="Dont download albums (for testing)")
    parser.add_argument(
        "--get-locations",
        action='store_true',
        help="Scrape the Google Photos website for location metadata"
             " and add it to the local files' EXIF metadata")
    parser.add_argument(
        "--use-hardlinks",
        action='store_true',
        help="Use hardlinks instead of symbolic links in albums and comparison"
             " folders")
    parser.add_argument(
        "--no-album-index",
        action='store_true',
        help="only index the photos library - skip indexing of folder contents "
             "(for testing)")
    parser.add_help = True

    def setup(self, args: Namespace, db_path: Path):
        root_folder = Path(args.root_folder).absolute()
        photos_folder = Path(args.photos_path)
        albums_folder = Path(args.albums_path)

        compare_folder = None
        if args.compare_folder:
            compare_folder = Path(args.compare_folder).absolute()
        app_dirs = AppDirs(APP_NAME)

        self.data_store = LocalData(db_path, args.flush_index)

        credentials_file = db_path / ".gphotos.token"
        secret_file = Path(app_dirs.user_config_dir) / "client_secret.json"
        if args.new_token and credentials_file.exists():
            credentials_file.unlink()

        scope = [
            'https://www.googleapis.com/auth/photoslibrary.readonly',
            'https://www.googleapis.com/auth/photoslibrary.sharing',
        ]
        photos_api_url = 'https://photoslibrary.googleapis.com/$discovery' \
                         '/rest?version=v1'

        self.auth = Authorize(scope, credentials_file, secret_file)
        self.auth.authorize()

        self.google_photos_client = RestClient(
            photos_api_url, self.auth.session)
        self.google_photos_idx = GooglePhotosIndex(
            self.google_photos_client, root_folder, self.data_store,
            args.photos_path, args.use_flat_path)
        self.google_photos_down = GooglePhotosDownload(
            self.google_photos_client, root_folder, self.data_store)
        self.google_albums_sync = GoogleAlbumsSync(
            self.google_photos_client, root_folder, self.data_store,
            args.flush_index or args.retry_download or args.rescan,
            photos_folder, albums_folder, args.use_flat_path,
            args.use_hardlinks)
        self.location_update = LocationUpdate(root_folder, self.data_store,
                                              args.photos_path)
        if args.compare_folder:
            self.local_files_scan = LocalFilesScan(
                root_folder, compare_folder, self.data_store)

        self._start_date = Utils.string_to_date(args.start_date)
        self._end_date = Utils.string_to_date(args.end_date)

        self.google_photos_idx.start_date = self._start_date
        self.google_photos_idx.end_date = self._end_date
        self.google_albums_sync.shared_albums = not args.skip_shared_albums
        self.google_albums_sync.album_index = not args.no_album_index
        self.google_photos_down.start_date = self._start_date
        self.google_photos_down.end_date = self._end_date
        self.location_update.start_date = self._start_date
        self.location_update.end_date = self._end_date

        self.google_photos_idx.include_video = not args.skip_video
        self.google_photos_idx.rescan = args.rescan
        self.google_photos_idx.favourites = args.favourites_only
        self.google_photos_down.retry_download = args.retry_download
        self.google_albums_sync.album = args.album

    @classmethod
    def logging(cls, args: Namespace, folder: Path):
        # if we are debugging requests library is too noisy
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("requests_oauthlib").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        numeric_level = getattr(logging, args.log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % args.log_level)

        if args.logfile:
            log_file = folder / args.logfile
            if log_file.is_dir():
                log_file = log_file / 'gphotos{}.log'.format(
                    datetime.now().strftime("%y%m%d_%H%M%S")
                )
        else:
            log_file = folder / 'gphotos.log'
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-12s %(levelname)-8s '
                                   '%(message)s',
                            datefmt='%m-%d %H:%M:%S',
                            filename=log_file,
                            filemode='w')
        # define a Handler which writes INFO messages or higher to the
        # sys.stderr
        console = logging.StreamHandler()
        console.setLevel(numeric_level)
        # set a format which is simpler for console use
        formatter = logging.Formatter('%(asctime)s %(message)s',
                                      datefmt='%m-%d %H:%M:%S')
        # tell the handler to use this format
        console.setFormatter(formatter)
        # add the handler to the root logger
        logging.getLogger('').addHandler(console)

    def do_location(self, args: Namespace):
        with self.data_store:
            if not args.skip_index:
                self.location_update.index_locations()
            if not args.index_only:
                self.location_update.set_locations()

    def do_sync(self, args: Namespace):
        new_files = True
        with self.data_store:
            if not args.skip_index:
                if not args.skip_files and not args.album:
                    new_files = self.google_photos_idx.index_photos_media()
            # if there are no new files and no arguments that specify specific
            # scan requirements, then we have done all we need to do
            if new_files or args.rescan or args.retry_download or \
                    args.start_date or args.album:
                if not args.skip_albums and not args.skip_index:
                    self.google_albums_sync.index_album_media()
                if not args.index_only:
                    if not args.skip_files:
                        self.google_photos_down.download_photo_media()
                    if not args.skip_albums:
                        self.google_albums_sync.create_album_content_links()
                    if args.do_delete:
                        self.google_photos_idx.check_for_removed()

            if args.compare_folder:
                if not args.skip_index:
                    self.local_files_scan.scan_local_files()
                    self.google_photos_idx.get_extra_meta()
                self.local_files_scan.find_missing_gphotos()

    def start(self, args: Namespace):
        if args.get_locations:
            self.do_location(args)
        else:
            self.do_sync(args)

    def main(self, test_args: dict = None):
        start_time = datetime.now()
        args = self.parser.parse_args(test_args)

        root_folder = Path(args.root_folder).absolute()
        db_path = Path(args.db_path) if args.db_path else root_folder
        if not root_folder.exists():
            root_folder.mkdir(parents=True, mode=0o700)
        self.logging(args, root_folder)

        lock_file = db_path / 'gphotos.lock'
        fp = lock_file.open('w')
        with fp:
            try:
                if os.name != 'nt':
                    fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                log.warning('EXITING: database is locked')
                sys.exit(0)

            log.info(self.version_string)

            # configure and launch
            # noinspection PyBroadException
            try:
                self.setup(args, db_path)
                self.start(args)
            except KeyboardInterrupt:
                log.error("User cancelled download")
                log.debug("Traceback", exc_info=True)
            except BaseException:
                log.error("\nProcess failed.", exc_info=True)
            finally:
                log.warning("Done.")

        elapsed_time = datetime.now() - start_time
        log.info('Elapsed time = %s', elapsed_time)


def main():
    GooglePhotosSyncMain().main()
