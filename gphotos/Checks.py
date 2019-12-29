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
    check_folder = root_folder / '.gphotos_check'
    check_folder.mkdir()
    case_file = check_folder / 'Temp.Test'
    no_case_file = check_folder / 'TEMP.TEST'
    try:
        case_file.touch()
        no_case_file.touch()
        files = list(check_folder.glob('*'))
        if len(files) != 2:
            raise ValueError("separate case files not seen")
        case_file.unlink()
        no_case_file.unlink()
    except (FileNotFoundError, ValueError):
        log.warning('Case insensitive file system found')
        return False
    else:
        log.warning('Case sensitive file system found')
        return True
    finally:
        if case_file.exists():
            case_file.unlink()
        if no_case_file.exists():
            no_case_file.unlink()
        check_folder.rmdir()


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
        log.warning(f'cant determine max filename length, '
                    f'defaulting to {MAX_FILENAME_LENGTH}')
    log.debug('MAX_FILENAME_LENGTH: %d' % MAX_FILENAME_LENGTH)
    return MAX_FILENAME_LENGTH
