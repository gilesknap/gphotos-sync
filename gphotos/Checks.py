#!/usr/bin/env python3
# coding: utf8
from tempfile import NamedTemporaryFile
from pathlib import Path
import logging
import random
import subprocess

log = logging.getLogger(__name__)

MAX_PATH_LENGTH = 4096
MAX_PATH_LENGTH = 255

def symlinks_supported(root_folder: Path) -> bool:
    log.debug('Checking if  is caseystem support symbolic links...')
    dst = 'test_dst_%s' % random.getrandbits(32)
    src = 'test_src_%s' % random.getrandbits(32)
    dst_file = root_folder / dst
    src_file = root_folder / src
    src_file.touch()
    try:
        dst_file.symlink_to(src_file)
    except OSError as e:
        log.error('Symbolic links not supported')
        log.error('Album are not going to be synced')
        return False
    src_file.unlink()
    dst_file.unlink()
    return True

def is_case_sensitive(root_folder: Path) -> bool:
    log.debug('Checking if File system is case insensitive...')
    filename = 'TeMp.TeSt'
    case_file = root_folder / filename
    case_file.touch()
    try:
        case_file.unlink()
    except FileNotFoundError:
        log.warning('Case insensitive file system found')
        case_file = Path(str(case_file).lower())
        case_file.unlink()
        return False
    return True

def get_max_path_length(root_folder: Path) -> int:
    global MAX_PATH_LENGTH
    # found this on: https://stackoverflow.com/questions/32807560/how-do-i-get-in-python-the-maximum-filesystem-path-length-in-unix
    try:
        MAX_PATH_LENGTH = int(subprocess.check_output(['getconf', 'PATH_MAX', '/']))
    except (ValueError, subprocess.CalledProcessError, OSError):
        deprint('calling getconf failed - error:', traceback=True)
    log.debug('MAX_PATH_LENGTH: %d' % MAX_PATH_LENGTH)
    return MAX_PATH_LENGTH

def get_max_filename_length(root_folder: Path) -> int:
    global MAX_FILENAME_LENGTH
    # found this on: https://stackoverflow.com/questions/32807560/how-do-i-get-in-python-the-maximum-filesystem-path-length-in-unix
    try:
        MAX_FILENAME_LENGTH = int(subprocess.check_output(['getconf', 'NAME_MAX', '/']))
    except (ValueError, subprocess.CalledProcessError, OSError):
        deprint('calling getconf failed - error:', traceback=True)
    log.debug('MAX_FILENAME_LENGTH: %d' % MAX_FILENAME_LENGTH)
    return MAX_FILENAME_LENGTH

