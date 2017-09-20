#!/usr/bin/python
# coding: utf8
import argparse
import os.path
import traceback

from appdirs import AppDirs

from GoogleDriveSync import GoogleDriveSync
from LocalData import LocalData
from PicasaSync import PicasaSync

APP_NAME = "gphotos-sync"


class GooglePhotosSyncMain:
    def __init__(self):
        self.data_store = None
        self.drive_sync = None
        self.picasa_sync = None

    parser = argparse.ArgumentParser(
        description="Google Photos download tool")
    parser.add_argument(
        "--quiet",
        action='store_true',
        help="quiet (no output)")
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
        help="remove local copies of files that were deleted from drive/picasa")
    parser.add_argument(
        "--skip-index",
        action='store_true',
        help="Use index from previous run and start download immediately")
    parser.add_argument(
        "--skip-picasa",
        action='store_true',
        help="skip picasa scan, albums will not be scanned")
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

    def setup(self, args):
        app_dirs = AppDirs(APP_NAME)

        self.data_store = LocalData(args.root_folder, args.flush_index)

        credentials_file = os.path.join(
            app_dirs.user_data_dir, "credentials.json")
        secret_file = os.path.join(
            app_dirs.user_config_dir, "client_secret.json")
        if args.new_token:
            os.remove(credentials_file)

        if not os.path.exists(app_dirs.user_data_dir):
            os.makedirs(app_dirs.user_data_dir)

        self.drive_sync = GoogleDriveSync(args.root_folder, self.data_store,
                                          client_secret_file=secret_file,
                                          credentials_json=credentials_file)

        self.picasa_sync = PicasaSync(self.drive_sync.credentials,
                                      args.root_folder, self.data_store)

        # quiet will be replaced by log level
        self.drive_sync.quiet = self.picasa_sync.quiet = args.quiet
        self.drive_sync.startDate = self.picasa_sync.startDate = args.start_date
        self.drive_sync.endDate = self.picasa_sync.endDate = args.end_date
        self.drive_sync.includeVideo = self.picasa_sync.includeVideo = \
            not args.skip_video
        self.drive_sync.driveFileName = args.drive_file
        self.drive_sync.allDrive = args.all_drive
        self.picasa_sync.album_name = args.album

    def start(self, args):
        with self.data_store:
            try:
                if not args.skip_index:
                    if not args.skip_drive:
                        self.drive_sync.scan_folder_hierarchy()
                        self.drive_sync.index_drive_media()
                    if not args.skip_picasa:
                        self.picasa_sync.index_album_media()
                if not args.index_only:
                    if not args.skip_picasa:
                        self.picasa_sync.download_picasa_media()
                    if not args.skip_drive:
                        self.drive_sync.download_drive_media()
                        if args.do_delete:
                            self.drive_sync.check_for_removed()
                    if not args.skip_picasa:
                        self.picasa_sync.create_album_content_links()
                        if args.do_delete:
                            self.picasa_sync.check_for_removed()

            except KeyboardInterrupt:
                print("\nUser cancelled download")
                # save the traceback so we can diagnose lockups
                except_file_name = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "etc", ".gphoto-terminated")
                with open(except_file_name, "w") as text_file:
                    text_file.write(traceback.format_exc())
            finally:
                print("\nDone.")

    def main(self):
        args = self.parser.parse_args()
        self.setup(args)
        self.start(args)
