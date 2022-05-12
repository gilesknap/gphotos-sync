import logging
import os
import random
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from psutil import disk_partitions

log = logging.getLogger(__name__)


class Checks:
    # regex for illegal characters in file names and database queries
    fix_linux = re.compile(r"[/]|[\x00-\x1f]|\x7f|\x00")
    fix_windows = re.compile(r'[,<>:"/\\|?*]|[\x00-\x1f]|\x7f|\x00')
    fix_windows_ending = re.compile("([ .]+$)")
    fix_whitespace_ending = re.compile("([ \t]+$)")
    fix_unicode = re.compile(r"[^\x00-\x7F]")

    # these filesystem types will have NTFS style filename restrictions
    windows_fs = ["fat", "ntfs", "9p"]
    WINDOWS_MAX_PATH = 248

    def __init__(self, root_path: Path, max_filename, ntfs):
        self.root_path: Path = root_path
        self._root_str: str = str(root_path).lower()
        if ntfs:
            self.is_linux: bool = False
        else:
            self.is_linux = self._check_linux_filesystem()
        self.is_symlink: bool = self._symlinks_supported()
        self.is_unicode: bool = self._unicode_filenames()
        self.is_case_sensitive: bool = self._check_case_sensitive()
        self.max_path: int = self._get_max_path_length()
        if max_filename > 0:
            self.max_filename: int = max_filename
        else:
            self.max_filename = self._get_max_filename_length()

    def _check_linux_filesystem(self) -> bool:
        filesystem_type = ""
        for part in disk_partitions(True):
            if part.mountpoint == "/":
                filesystem_type = part.fstype
                continue

            if self._root_str.startswith(part.mountpoint.lower()):
                filesystem_type = part.fstype
                break
        filesystem_type = filesystem_type.lower()
        is_linux = not any(fs in filesystem_type for fs in self.windows_fs)
        log.info(f"Target filesystem {self._root_str} is {filesystem_type}")

        return is_linux

    def _symlinks_supported(self) -> bool:
        log.debug("Checking if is filesystem supports symbolic links...")
        dst = "test_dst_%s" % random.getrandbits(32)
        src = "test_src_%s" % random.getrandbits(32)
        dst_file = self.root_path / dst
        src_file = self.root_path / src
        src_file.touch()
        try:
            log.debug("attempting to symlink %s to %s", src_file, dst_file)
            dst_file.symlink_to(src_file)
            dst_file.unlink()
            src_file.unlink()
        except BaseException:
            if src_file.exists():
                src_file.unlink()
            log.error("Symbolic links not supported")
            log.error("Albums are not going to be synced - requires symlinks")
            return False
        return True

    def _unicode_filenames(self) -> bool:
        log.debug("Checking if File system supports unicode filenames...")
        testfile = self.root_path / ".unicode_test.\U0001f604"

        is_unicode = False
        try:
            testfile.touch()
        except BaseException:
            log.info("Filesystem does not support Unicode filenames")
        else:
            log.info("Filesystem supports Unicode filenames")
            is_unicode = True
            testfile.unlink()
        return is_unicode

    def _check_case_sensitive(self) -> bool:
        log.debug("Checking if File system is case insensitive...")

        check_folder = self.root_path / ".gphotos_check"
        case_file = check_folder / "Temp.Test"
        no_case_file = check_folder / "TEMP.TEST"

        is_sensitive = False
        try:
            check_folder.mkdir()
            case_file.touch()
            no_case_file.touch()
            files = list(check_folder.glob("*"))
            if len(files) != 2:
                raise ValueError("separate case files not seen")
            case_file.unlink()
            no_case_file.unlink()
        except (FileExistsError, FileNotFoundError, ValueError):
            log.info("Case insensitive file system found")
        else:
            log.info("Case sensitive file system found")
            is_sensitive = True
        finally:
            shutil.rmtree(check_folder)
        return is_sensitive

    def _get_max_path_length(self) -> int:
        # safe windows length
        max_length = self.WINDOWS_MAX_PATH

        # found this on:
        # https://stackoverflow.com/questions/32807560/how-do-i-get-in-python-the-maximum-filesystem-path-length-in-unix
        try:
            max_length = int(
                subprocess.check_output(["getconf", "PATH_MAX", str(self.root_path)])
            )
        except BaseException:
            # for failures choose a safe size for Windows filesystems
            log.info(
                f"cant determine max filepath length, defaulting to " f"{max_length}"
            )
        log.info("Max Path Length: %d" % max_length)
        return max_length

    def _get_max_filename_length(self) -> int:
        # safe windows length
        max_filename = self.WINDOWS_MAX_PATH
        try:
            info = os.statvfs(str(self.root_path))
            max_filename = info.f_namemax
        except BaseException:
            # for failures choose a safe size for Windows filesystems
            max_filename = 248
            log.info(
                f"cant determine max filename length, " f"defaulting to {max_filename}"
            )
        log.info("Max filename length: %d" % max_filename)
        return max_filename

    def valid_file_name(self, s: str) -> str:
        """
        makes sure a string is valid for creating file names

        :param (str) s: input string
        :return: (str): sanitized string
        """
        s = self.fix_whitespace_ending.sub("", s)

        if self.is_linux:
            s = self.fix_linux.sub("_", s)
        else:
            s = self.fix_windows.sub("_", s)
            s = self.fix_windows_ending.split(s)[0]

        if not self.is_unicode:
            s = self.fix_unicode.sub("_", s)

        return s


# a global for holding the current root folder check results
root_folder: Optional[Checks] = None

# TODO: this approach needs review


# ugly global stuff to avoid passing Checks object everywhere
def do_check(root: Path, max_filename=0, ntfs=None):
    global root_folder
    root_folder = Checks(root, max_filename, ntfs)
    return root_folder


def get_check():
    return root_folder
