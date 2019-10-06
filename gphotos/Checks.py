#!/usr/bin/env python3
# coding: utf8
from tempfile import NamedTemporaryFile
from pathlib import Path
import logging
import random

log = logging.getLogger(__name__)

def symlinks_supported(root_folder: Path) -> bool:
    dst = 'test_dst_%s' % random.getrandbits(32)
    src = 'test_src_%s' % random.getrandbits(32)
    dst_file = root_folder / dst
    src_file = root_folder / src
    try:
        dst_file.symlink_to(src_file)
    except OSError as e:
        log.error('Symbolic links not supported')
        log.error('Album are not going to be synced')
        return False
    src_file.unlink()
    dst_file.unlink()
    return true

