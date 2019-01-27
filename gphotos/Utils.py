#!/usr/bin/env python3
# coding: utf8
from __future__ import division

import ctypes
import os
import re
from datetime import datetime
import logging

log = logging.getLogger(__name__)

DATE_NORMALIZE = re.compile(r'(\d\d\d\d).(\d\d).(\d\d).(\d\d).(\d\d).(\d\d)')
SHORT_DATE_NORMALIZE = re.compile(r'(\d\d\d\d).(\d\d).(\d\d)')
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_ONLY = "%Y-%m-%d"

__CSL = None

# patch os.symlink for windows
# NOTE: your process will need the correct permissions to use this
# run 'Local Security Policy' choose
# "Local Policies->User Rights Assignment->create symbolic links" and add
# the account that will run this process
if os.name == 'nt':
    # noinspection SpellCheckingInspection
    def symlink(source, link_name):
        """
        symlink(source, link_name)
        Creates a symbolic link pointing to source named link_name
        """
        global __CSL
        if __CSL is None:
            csl = ctypes.windll.kernel32.CreateSymbolicLinkW
            csl.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
            csl.restype = ctypes.c_ubyte
            __CSL = csl
        flags = 0
        if source is not None and os.path.isdir(source):
            flags = 1
        log.debug('link %s %s', source, link_name)
        if __CSL(link_name, source, flags) == 0:
            raise ctypes.WinError()


    os.symlink = symlink


# incredibly windows cannot handle dates below 1970
def safe_str_time(date_time, date_format):
    if os.name == 'nt':
        if date_time < minimum_date():
            date_time = minimum_date()
    return date_time.strftime(date_format)


def date_to_string(date_t, date_only=False):
    """
    :param (int) date_only:
    :param (datetime) date_t:
    :return (str):
    """
    if date_only:
        return date_t.strftime(DATE_ONLY)
    else:
        return date_t.strftime(DATE_FORMAT)


def maximum_date():
    return datetime.max


def minimum_date():
    # determine the minimum date that is usable on the
    # current platform (is there a better way to do this?)
    d = datetime.min.replace(year=1900)

    try:
        _ = d.timestamp()
    except (ValueError, OverflowError):
        d = datetime.min.replace(year=1970)
    return d


def string_to_date(date_string):
    m = DATE_NORMALIZE.match(date_string)
    if m:
        normalized = '{}-{}-{} {}:{}:{}'.format(*m.groups())
    else:
        m = SHORT_DATE_NORMALIZE.match(date_string)
        if m:
            normalized = '{}-{}-{} 00:00:00'.format(*m.groups())
        else:
            log.warning('WARNING: time string %s illegal', date_string)
            return minimum_date()

    return datetime.strptime(normalized, DATE_FORMAT)
