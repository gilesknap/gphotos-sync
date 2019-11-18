import os

import logging
import random
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

MAX_PATH_LENGTH = 4096
MAX_FILENAME_LENGTH = 255


def symlinks_supported(root_folder: Path) -> bool:
    log.debug('Checking if is filesystem supports symbolic links...')
    dst = 'test_dst_%s' % random.getrandbits(32)
    src = 'test_src_%s' % random.getrandbits(32)
    dst_file = root_folder / dst
    src_file = root_folder / src
    src_file.touch()
    try:
        dst_file.symlink_to(src_file)
    except OSError:
        log.error('Symbolic links not supported')
        log.error('Albums are not going to be synced - requires symlinks')
        return False
    src_file.unlink()
    dst_file.unlink()
    return True


def is_case_sensitive(root_folder: Path) -> bool:
    log.debug('Checking if File system is case insensitive...')
    filename1 = 'TeMp.TeSt'
    filename2 = 'TEMP.TEST'
    case_file = root_folder / filename1
    no_case_file = root_folder / filename2
    case_file.touch()
    try:
        no_case_file.unlink()
    except FileNotFoundError:
        case_file.unlink()
        return True
    else:
        log.warning('Case insensitive file system found')
        return False


# noinspection PyBroadException
def get_max_path_length(root_folder: Path) -> int:
    global MAX_PATH_LENGTH
    # found this on:
    # https://stackoverflow.com/questions/32807560/how-do-i-get-in-python-the-maximum-filesystem-path-length-in-unix
    try:
        MAX_PATH_LENGTH = int(subprocess.check_output(
            ['getconf', 'PATH_MAX', str(root_folder)])
        )
    except BaseException:
        # for failures choose a safe size for Windows filesystems
        MAX_PATH_LENGTH = 248
        log.warning(f'cant determine max filepath length, defaulting to '
                    f'{MAX_PATH_LENGTH}')
    log.debug('MAX_PATH_LENGTH: %d' % MAX_PATH_LENGTH)
    return MAX_PATH_LENGTH


# noinspection PyBroadException
def get_max_filename_length(root_folder: Path) -> int:
    global MAX_FILENAME_LENGTH
    try:
        info = os.statvfs(str(root_folder))
        MAX_FILENAME_LENGTH = info.f_namemax
    except BaseException:
        # for failures choose a safe size for Windows filesystems
        MAX_FILENAME_LENGTH = 248
        log.warning(f'cant determine max filename length, defaulting to {MAX_FILENAME_LENGTH}')
    log.debug('MAX_FILENAME_LENGTH: %d' % MAX_FILENAME_LENGTH)
    return MAX_FILENAME_LENGTH
