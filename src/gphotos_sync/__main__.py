# coding: utf8
import logging
import os
import sys
from argparse import ArgumentParser, Namespace
from datetime import datetime
from pathlib import Path
from typing import Optional
from xmlrpc.client import DateTime

from appdirs import AppDirs

from gphotos_sync import Utils, __version__
from gphotos_sync.authorize import Authorize
from gphotos_sync.Checks import do_check, get_check
from gphotos_sync.GoogleAlbumsSync import GoogleAlbumsSync
from gphotos_sync.GooglePhotosDownload import GooglePhotosDownload  # type: ignore
from gphotos_sync.GooglePhotosIndex import GooglePhotosIndex
from gphotos_sync.LocalData import LocalData
from gphotos_sync.LocalFilesScan import LocalFilesScan
from gphotos_sync.Logging import setup_logging
from gphotos_sync.restclient import RestClient
from gphotos_sync.Settings import Settings

if os.name == "nt":
    import subprocess

    orig_Popen = subprocess.Popen

    class Popen_patch(subprocess.Popen):
        def __init__(self, *args, **kargs):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            kargs["startupinfo"] = startupinfo
            super().__init__(*args, **kargs)

    subprocess.Popen = Popen_patch  # type: ignore
else:
    import fcntl

APP_NAME = "gphotos-sync"
log = logging.getLogger(__name__)


class GooglePhotosSyncMain:
    def __init__(self):
        self.data_store: LocalData
        self.google_photos_client: RestClient
        self.google_photos_idx: GooglePhotosIndex
        self.google_photos_down: GooglePhotosDownload
        self.google_albums_sync: GoogleAlbumsSync
        self.local_files_scan: LocalFilesScan
        self._start_date: Optional[DateTime]
        self._end_date = Optional[DateTime]

        self.auth: Authorize

    try:
        version_string = "version: {}, database schema version {}".format(
            __version__, LocalData.VERSION
        )
    except TypeError:
        version_string = "(version not available)"

    parser = ArgumentParser(
        epilog=version_string, description="Google Photos download tool"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="report version and exit",
    )
    parser.add_argument(
        "root_folder",
        help="root of the local folders to download into",
        nargs="?",
    )
    album_group = parser.add_mutually_exclusive_group()
    album_group.add_argument(
        "--album",
        action="store",
        help="only synchronize the contents of a single album. "
        'use quotes e.g. "album name" for album names with spaces',
    )
    album_group.add_argument(
        "--album-regex",
        action="store",
        metavar="REGEX",
        help="""only synchronize albums that match regular expression.
        regex is case insensitive and unanchored. e.g. to select two albums:
        "^(a full album name|another full name)$" """,
    )
    parser.add_argument(
        "--log-level",
        help="Set log level. Options: critical, error, warning, info, debug, trace. "
        "trace logs all Google API calls to a file with suffix .trace",
        default="warning",
    )
    parser.add_argument(
        "--logfile",
        action="store",
        help="full path to debug level logfile, default: <root>/gphotos.log. "
        "If a directory is specified then a unique filename will be "
        "generated.",
    )
    parser.add_argument(
        "--compare-folder",
        action="store",
        help="DEPRECATED: root of the local folders to compare to the Photos Library",
    )
    parser.add_argument(
        "--favourites-only",
        action="store_true",
        help="only download media marked as favourite (star)",
    )
    parser.add_argument(
        "--flush-index",
        action="store_true",
        help="delete the index db, re-scan everything",
    )
    parser.add_argument(
        "--rescan",
        action="store_true",
        help="rescan entire library, ignoring last scan date. Use this if you "
        "have added photos to the library that "
        "predate the last sync, or you have deleted some of the local "
        "files",
    )
    parser.add_argument(
        "--retry-download",
        action="store_true",
        help="check for the existence of files marked as already downloaded "
        "and re-download any missing ones. Use "
        "this if you have deleted some local files",
    )
    parser.add_argument(
        "--skip-video", action="store_true", help="skip video types in sync"
    )
    parser.add_argument(
        "--skip-shared-albums",
        action="store_true",
        help="skip albums that only appear in 'Sharing'",
    )
    parser.add_argument(
        "--album-date-by-first-photo",
        action="store_true",
        help="Make the album date the same as its earliest "
        "photo. The default is its last photo",
    )
    parser.add_argument(
        "--start-date",
        help="Set the earliest date of files to sync" "format YYYY-MM-DD",
        default=None,
    )
    parser.add_argument(
        "--end-date",
        help="Set the latest date of files to sync" "format YYYY-MM-DD",
        default=None,
    )
    parser.add_argument(
        "--db-path",
        help="Specify a pre-existing folder for the index database. "
        "Defaults to the root of the local download folders",
        default=None,
    )
    parser.add_argument(
        "--albums-path",
        help="Specify a folder for the albums "
        "Defaults to the 'albums' in the local download folders",
        default="albums",
    )
    parser.add_argument(
        "--photos-path",
        help="Specify a folder for the photo files. "
        "Defaults to the 'photos' in the local download folders",
        default="photos",
    )
    parser.add_argument(
        "--use-flat-path",
        action="store_true",
        help="Mandate use of a flat directory structure ('YYYY-MMM') and not "
        "a nested one ('YYYY/MM') . ",
    )
    parser.add_argument(
        "--omit-album-date",
        action="store_true",
        help="Don't include year and month in album folder names.",
    )
    parser.add_argument(
        "--album-invert",
        action="store_true",
        help="Inverts the sorting direction of files within an album. "
        "Default sorting is descending from newest to olders. "
        "This causes it to be the other way around.",
    )
    parser.add_argument("--new-token", action="store_true", help="Request new token")
    parser.add_argument(
        "--index-only",
        action="store_true",
        help="Only build the index of files in .gphotos.db - no downloads",
    )
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Use index from previous run and start download immediately",
    )
    parser.add_argument(
        "--do-delete",
        action="store_true",
        help="""Remove local copies of files that were deleted.
        Must be used with --flush-index since the deleted items must be removed
        from the index""",
    )
    parser.add_argument(
        "--skip-files",
        action="store_true",
        help="Dont download files, just refresh the album links (for testing)",
    )
    parser.add_argument(
        "--skip-albums", action="store_true", help="Dont download albums (for testing)"
    )
    parser.add_argument(
        "--use-hardlinks",
        action="store_true",
        help="Use hardlinks instead of symbolic links in albums and comparison"
        " folders",
    )
    parser.add_argument(
        "--no-album-index",
        action="store_true",
        help="only index the photos library - skip indexing of folder contents "
        "(for testing)",
    )
    parser.add_argument(
        "--case-insensitive-fs",
        action="store_true",
        help="add this flag if your filesystem is case insensitive",
    )
    parser.add_argument(
        "--max-retries",
        help="Set the number of retries on network timeout / failures",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--max-threads",
        help="Set the number of concurrent threads to use for parallel "
        "download of media - reduce this number if network load is "
        "excessive",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--secret",
        help="Path to client secret file (by default this is in the "
        "application config directory)",
    )
    parser.add_argument(
        "--archived",
        action="store_true",
        help="Download media items that have been marked as archived",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="show progress of indexing and downloading in warning log",
    )
    parser.add_argument(
        "--max-filename",
        help="Set the maxiumum filename length for target filesystem."
        "This overrides the automatic detection.",
        default=0,
    )
    parser.add_argument(
        "--ntfs",
        action="store_true",
        help="Declare that the target filesystem is ntfs (or ntfs like)."
        "This overrides the automatic detection.",
    )
    parser.add_argument(
        "--month-format",
        action="store",
        metavar="FMT",
        help="Configure the month/day formatting for the album folder/file "
        "path (default: %%m%%d).",
        default="%m%d",
    )
    parser.add_argument(
        "--path-format",
        action="store",
        metavar="FMT",
        help="Configure the formatting for the album folder/file path. The "
        "formatting can include up to 2 positionals arguments; `month` and "
        "`album_name`. The default value is `{0} {1}`."
        "When used with --use-flat-path option, it can include up to 3 "
        "positionals arguments; `year`, `month` and `album_name`. In this case "
        "the default value is `{0}-{1} {2}`",
        default=None,
    )
    parser.add_argument(
        "--port",
        help="Set the port for login flow redirect",
        type=int,
        default=8080,
    )
    parser.add_argument(
        "--image-timeout",
        help="Set the time in seconds to wait for an image to download",
        type=int,
        default=60,
    )
    parser.add_argument(
        "--video-timeout",
        help="Set the time in seconds to wait for a video to download",
        type=int,
        default=2000,
    )
    parser.add_help = True

    def setup(self, args: Namespace, db_path: Path):
        root_folder = Path(args.root_folder).absolute()

        compare_folder = None
        if args.compare_folder:
            compare_folder = Path(args.compare_folder).absolute()
        app_dirs = AppDirs(APP_NAME)

        self.data_store = LocalData(db_path, args.flush_index)

        credentials_file = db_path / ".gphotos.token"
        if args.secret:
            secret_file = Path(args.secret)
        else:
            secret_file = Path(app_dirs.user_config_dir) / "client_secret.json"
        if args.new_token and credentials_file.exists():
            credentials_file.unlink()

        scope = [
            "https://www.googleapis.com/auth/photoslibrary.readonly",
            "https://www.googleapis.com/auth/photoslibrary.sharing",
        ]
        photos_api_url = (
            "https://photoslibrary.googleapis.com/$discovery" "/rest?version=v1"
        )

        self.auth = Authorize(
            scope,
            credentials_file,
            secret_file,
            int(args.max_retries),
            port=args.port,
        )
        self.auth.authorize()

        settings = Settings(
            start_date=Utils.string_to_date(args.start_date),  # type: ignore
            end_date=Utils.string_to_date(args.end_date),  # type: ignore
            shared_albums=not args.skip_shared_albums,
            album_index=not args.no_album_index,
            use_start_date=args.album_date_by_first_photo,
            album=args.album,
            album_regex=args.album_regex,
            favourites_only=args.favourites_only,
            retry_download=args.retry_download,
            case_insensitive_fs=args.case_insensitive_fs,
            include_video=not args.skip_video,
            rescan=args.rescan,
            archived=args.archived,
            photos_path=Path(args.photos_path),
            albums_path=Path(args.albums_path),
            use_flat_path=args.use_flat_path,
            max_retries=int(args.max_retries),
            max_threads=int(args.max_threads),
            omit_album_date=args.omit_album_date,
            album_invert=args.album_invert,
            use_hardlinks=args.use_hardlinks,
            progress=args.progress,
            ntfs_override=args.ntfs,
            month_format=args.month_format,
            path_format=args.path_format,
            image_timeout=args.image_timeout,
            video_timeout=args.video_timeout,
        )

        self.google_photos_client = RestClient(
            photos_api_url,
            self.auth.session,  # type: ignore
        )
        self.google_photos_idx = GooglePhotosIndex(
            self.google_photos_client, root_folder, self.data_store, settings
        )
        self.google_photos_down = GooglePhotosDownload(
            self.google_photos_client, root_folder, self.data_store, settings
        )
        self.google_albums_sync = GoogleAlbumsSync(
            self.google_photos_client,
            root_folder,
            self.data_store,
            args.flush_index or args.retry_download or args.rescan,
            settings,
        )
        if args.compare_folder:
            self.local_files_scan = LocalFilesScan(
                root_folder,
                compare_folder,  # type: ignore
                self.data_store,  # type: ignore
            )

    def do_sync(self, args: Namespace):
        files_downloaded = 0
        with self.data_store:
            if not args.skip_index:
                if not args.skip_files and not args.album and not args.album_regex:
                    self.google_photos_idx.index_photos_media()

            if not args.index_only:
                if not args.skip_files:
                    files_downloaded = self.google_photos_down.download_photo_media()

            if (
                not args.skip_albums
                and not args.skip_index
                and (files_downloaded > 0 or args.skip_files or args.rescan)
            ) or (args.album is not None or args.album_regex is not None):
                self.google_albums_sync.index_album_media()
                # run download again to pick up files indexed in albums only
                if not args.index_only:
                    if not args.skip_files:
                        files_downloaded = (
                            self.google_photos_down.download_photo_media()
                        )

            if not args.index_only:
                if (
                    not args.skip_albums
                    and (files_downloaded > 0 or args.skip_files or args.rescan)
                    or (args.album is not None or args.album_regex is not None)
                ):
                    self.google_albums_sync.create_album_content_links()
                if args.do_delete:
                    self.google_photos_idx.check_for_removed()

            if args.compare_folder:
                if not args.skip_index:
                    self.local_files_scan.scan_local_files()
                    self.google_photos_idx.get_extra_meta()
                self.local_files_scan.find_missing_gphotos()

    def start(self, args: Namespace):
        self.do_sync(args)

    @staticmethod
    def fs_checks(root_folder: Path, args):
        Utils.minimum_date(root_folder)
        # store the root folder filesystem checks globally for all to inspect
        do_check(root_folder, int(args.max_filename), bool(args.ntfs))

        # check if symlinks are supported
        # NTFS supports symlinks, but is_symlink() fails
        if not args.ntfs:
            if not get_check().is_symlink:  # type: ignore
                args.skip_albums = True

        # check if file system is case sensitive
        if not args.case_insensitive_fs:
            if not get_check().is_case_sensitive:  # type: ignore
                args.case_insensitive_fs = True

        return args

    def main(self, test_args: Optional[dict] = None):
        start_time = datetime.now()
        args = self.parser.parse_args(test_args)  # type: ignore

        if args.version:
            print(__version__)
            exit(0)
        else:
            if args.root_folder is None:
                self.parser.print_help()
                print("\nERROR: Please supply root_folder in which to save photos")
                exit(1)

        root_folder = Path(args.root_folder).absolute()
        db_path = Path(args.db_path) if args.db_path else root_folder
        if not root_folder.exists():
            root_folder.mkdir(parents=True, mode=0o700)

        setup_logging(args.log_level, args.logfile, root_folder)
        log.warning(f"gphotos-sync {__version__} {start_time}")

        args = self.fs_checks(root_folder, args)

        lock_file = db_path / "gphotos.lock"
        fp = lock_file.open("w")
        with fp:
            try:
                if os.name != "nt":
                    fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                log.warning("EXITING: database is locked")
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
                exit(1)
            except BaseException:
                log.error("\nProcess failed.", exc_info=True)
                exit(1)
            finally:
                log.warning("Done.")

        elapsed_time = datetime.now() - start_time
        log.info("Elapsed time = %s", elapsed_time)


def main():
    GooglePhotosSyncMain().main()


if __name__ == "__main__":
    main()
