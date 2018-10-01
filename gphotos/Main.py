# coding: utf8
import argparse
import os.path
import traceback
import logging
import sys
import signal
import fcntl

from appdirs import AppDirs
from .GoogleDriveSync import GoogleDriveSync
from .LocalData import LocalData
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
        self.drive_sync = None

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
        "--skip-drive",
        action='store_true',
        help="skip drive scan, (assume that the db is up to date "
             "with drive files - for testing)")
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
        "--all-drive",
        action='store_true',
        help="when True all folders in drive are scanned for media. "
             "when False only files in the Google Photos folder are scanned. "
             "If you do not use this option then you may find you have albums "
             "that reference media outside of the Google Photos folder and "
             "these would then get downloaded into the picasa folder. The "
             "only downside is that the folder structure is lost.")
    parser.add_argument(
        "--album",
        help="only index a single album (for testing)",
        default=None)
    parser.add_argument(
        "--drive-file",
        help="only index a single drive file (for testing)",
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

        self.drive_sync = GoogleDriveSync(args.root_folder, self.data_store,
                                          client_secret_file=secret_file,
                                          credentials_json=credentials_file,
                                          no_browser=args.no_browser)

        self.drive_sync.startDate = args.start_date
        self.drive_sync.endDate = args.end_date
        self.drive_sync.includeVideo = not args.skip_video
        self.drive_sync.driveFileName = args.drive_file
        self.drive_sync.allDrive = args.all_drive

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
                    if not args.skip_drive:
                        self.drive_sync.scan_folder_hierarchy()
                        self.drive_sync.index_drive_media()
                        self.data_store.store()
                if not args.index_only:
                    if not args.skip_drive:
                        self.drive_sync.download_drive_media()
                        if args.do_delete:
                            self.drive_sync.check_for_removed()

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
