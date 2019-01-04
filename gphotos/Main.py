# coding: utf8
import argparse
import os.path
import traceback
import logging
import sys
import signal
import fcntl

from appdirs import AppDirs
from .GooglePhotosMediaSync import GooglePhotosMediaSync
from .LocalData import LocalData
from .authorize import Authorize
from .restclient import RestClient
import pkg_resources

APP_NAME = "gphotos-sync"
log = logging.getLogger('gphotos')


def sigterm_handler(_signo, _stack_frame):
    log.warning("\nProcess killed "
                "(stacktrace in .gphotos-terminated).")
    # save the traceback so we can diagnose lockups
    with open(".gphotos-terminated", "w") as text_file:
        text_file.write(traceback.format_exc())
    sys.exit(0)


class GooglePhotosSyncMain:
    def __init__(self):
        self.data_store = None
        self.google_photos_client = None
        self.google_photos_sync = None
        self.auth = None

    parser = argparse.ArgumentParser(
        description="Google Photos download tool")
    parser.add_argument(
        "--skip-video",
        action='store_true',
        help="skip video types in sync")
    parser.add_argument(
        "root_folder",
        help="root of the local folders to download into")
    parser.add_argument(
        "--start-date",
        help="Set the earliest date of files to sync",
        default=None)
    parser.add_argument(
        "--log-level",
        help="Set log level. Options: critical, error, warning, info, debug",
        default='info')
    parser.add_argument(
        "--db-path",
        help="Specify a pre-existing folder for the index database. "
             "Defaults to the root of the local download folders",
        default=None)
    parser.add_argument(
        "--end-date",
        help="Set the latest date of files to sync",
        default=None)
    parser.add_argument(
        "--new-token",
        action='store_true',
        help="Request new token")
    parser.add_argument(
        "--index-only",
        action='store_true',
        help="Only build the index of files in .gphotos.db - no downloads")
    parser.add_argument(
        "--do-delete",
        action='store_true',
        help="remove local copies of files that were deleted")
    parser.add_argument(
        "--skip-index",
        action='store_true',
        help="Use index from previous run and start download immediately")
    parser.add_argument(
        "--flush-index",
        action='store_true',
        help="delete the index db, re-scan everything")
    parser.add_argument(
        "--no-browser",
        action='store_true',
        help="use cut and paste for auth instead of invoking a browser")
    parser.add_argument(
        "--refresh-albums",
        action='store_true',
        help="force a refresh of the album links")
    parser.add_argument(
        "--brief",
        action='store_true',
        help="don't print time and module in logging")
    parser.add_argument(
        "--album",
        help="only index a single album (for testing)",
        default=None)

    def setup(self, args, db_path):
        app_dirs = AppDirs(APP_NAME)

        self.data_store = LocalData(db_path, args.flush_index)

        credentials_file = os.path.join(
            app_dirs.user_data_dir, "credentials.json")
        secret_file = os.path.join(
            app_dirs.user_config_dir, "client_secret.json")
        if args.new_token and os.path.exists(credentials_file):
            os.remove(credentials_file)

        if not os.path.exists(app_dirs.user_data_dir):
            os.makedirs(app_dirs.user_data_dir)

        scope = [
            'https://www.googleapis.com/auth/photos',
            'https://www.googleapis.com/auth/drive.photos.readonly',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/photoslibrary.readonly',
            'https://www.googleapis.com/auth/photoslibrary.sharing',
        ]

        # drive_api_url = 'https://www.googleapis.com/discovery/v1/apis/drive/v3/rest'
        photos_api_url = 'https://www.googleapis.com/discovery/v1/apis/photoslibrary/v1/rest'
        # NEW photos_api_url = 'https://photoslibrary.googleapis.com/$discovery/rest?version=v1''

        self.auth = Authorize(scope, credentials_file, secret_file)
        self.auth.authorize()

        self.google_photos_client = RestClient(photos_api_url, self.auth.session)

        #
        # count = 0
        # r = self.google_photos.albums.list.execute(pageSize=50)
        # while r:
        #     results = r.json()
        #     for a in results['albums']:
        #         count += 1
        #         title_text = a.get('title') or ' --- No Title ---'
        #         print(count, title_text)
        #
        #     next_page = results.get('nextPageToken')
        #     if next_page:
        #         r = self.google_photos.albums.list.execute(pageSize=50, pageToken=next_page)
        #     else:
        #         break

        self.google_photos_sync = GooglePhotosMediaSync(args.root_folder, self.data_store,
                                                        api=self.google_photos_client)

        self.google_photos_sync.startDate = args.start_date
        self.google_photos_sync.endDate = args.end_date
        self.google_photos_sync.includeVideo = not args.skip_video

    @classmethod
    def logging(cls, args):
        numeric_level = getattr(logging, args.log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % args.log_level)

        # create logger
        log.setLevel(numeric_level)

        # create console handler and set level to debug
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)

        # create formatter
        if args.brief:
            format_string = u'%(message)s'
        else:
            format_string = u'%(asctime)s %(name)s: %(message)s'

        # avoid encoding issues on ssh and file redirect
        ##  Is this an issue ?? formatter = logging.Formatter(format_string.encode('utf-8'))
        # add formatter to ch
        ## ch.setFormatter(formatter)

        if not len(log.handlers):
            # add ch to logger
            log.addHandler(ch)

    def start(self, args):
        with self.data_store:
            try:
                if not args.skip_index:
                    self.google_photos_sync.index_photos_media()
                    self.data_store.store()
                # if not args.index_only:
                #     if not args.skip_drive:
                #         self.google_photos_sync.download_drive_media()
                #         if args.do_delete:
                #             self.google_photos_sync.check_for_removed()

            except KeyboardInterrupt:
                log.warning("\nUser cancelled download "
                            "(stacktrace in .gphotos-terminated).")
                # save the traceback so we can diagnose lockups
                with open(".gphotos-terminated", "w") as text_file:
                    text_file.write(traceback.format_exc())
            finally:
                # save the traceback so we can diagnose lockups
                with open(".gphotos-terminated", "w") as text_file:
                    text_file.write(traceback.format_exc())
                log.info("Done.")

    def main(self):
        args = self.parser.parse_args()
        self.logging(args)
        signal.signal(signal.SIGTERM, sigterm_handler)

        db_path = args.db_path if args.db_path else args.root_folder
        if not os.path.exists(args.root_folder):
            os.makedirs(args.root_folder, 0o700)

        lock_file = os.path.join(db_path, 'gphotos.lock')
        fp = open(lock_file, 'w')
        with fp:
            try:
                fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                log.warning(u'EXITING: database is locked')
                sys.exit(0)

            # noinspection PyBroadException
            try:
                log.info('version: {}'.format(
                    pkg_resources.get_distribution("gphotos-sync").version))
            except Exception:
                log.info('version not available')

            # configure and launch
            self.setup(args, db_path)
            self.start(args)
