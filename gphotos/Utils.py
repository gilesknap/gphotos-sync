#!/usr/bin/env python2
# coding: utf8
from __future__ import division

import ctypes
import os
import re
import time
from datetime import datetime
import logging

log = logging.getLogger('gphotos.utils')

DATE_NORMALIZE = re.compile('(\d\d\d\d).(\d\d).(\d\d).(\d\d).(\d\d).(\d\d)')
SHORT_DATE_NORMALIZE = re.compile('(\d\d\d\d).(\d\d).(\d\d)')
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


def retry(count, func, *arg, **k_arg):
    last_e = None
    for retry_no in range(count):
        try:
            res = func(*arg, **k_arg)
            return res
        except Exception as e:
            last_e = e
            log.warning(u"RETRYING due to: %s", repr(e))
            log.warning(u"Call was: %s (%s, %s)", repr(func), arg, k_arg)
            time.sleep(.1)
    raise last_e


# does not work (why?), using verbose one below
def retry_i_x(count, iterator):
    for n in retry(count, iterator.next):
        yield n


def retry_i(count, iterator):
    last_item = None
    more_data = True
    while more_data:
        for retry_no in range(count):
            try:
                last_item = iterator.next()
                break
            except StopIteration:
                more_data = False
                break
            except Exception as e:
                log.warning(u"RETRYING iterator due to: %s", repr(e))
                time.sleep(.1)
        yield last_item


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
    # this is the minimum acceptable date for drive queries and surprisingly
    # datetime.strptime on some platforms
    if os.name == 'nt':
        return datetime.min.replace(year=1970)
    else:
        # google drive search does not like 1900 but strptime is OK
        # this is annoying for my 1964 dated files - will v3 API fix this?
        return datetime.min.replace(year=1970)


def to_timestamp(dt, epoch=datetime(1970, 1, 1)):
    td = dt - epoch
    return td.total_seconds()


def string_to_date(date_string):
    m = DATE_NORMALIZE.match(date_string)
    if m:
        normalized = '{}-{}-{} {}:{}:{}'.format(*m.groups())
    else:
        m = SHORT_DATE_NORMALIZE.match(date_string)
        if m:
            normalized = '{}-{}-{} 00:00:00'.format(*m.groups())
        else:
            log.warning(u'WARNING: time string {} illegal', date_string)
            return minimum_date()

    return datetime.strptime(normalized, DATE_FORMAT)


def timestamp_to_date(time_secs, hour_offset=0):
    try:
        date = datetime.fromtimestamp(
            int(time_secs) / 1000 + 3600 * hour_offset)
    except ValueError:
        log.warning(u'WARNING: time stamp %d illegal', time_secs)
        date = minimum_date()
    return date


# gdata patches the http client to handle token refresh for oauth2
# but the signature is out of date for the current http_client.request.
# Here we patch over their patch to fix
# error 'TypeError: new_request() takes exactly 1 argument (4 given)'
# noinspection SpellCheckingInspection
def patch_http_client(oauth, client, request_orig2):
    """
    :param (gdata.gauth.OAuth2TokenFromCredentials) oauth:
    :param (gdata.photos.service.PhotoService) client:
    :param (instancemethod) request_orig2:
    :return:
    """
    client.auth_token = oauth

    # noinspection PyProtectedMember
    def new_request2(*args, **k_args):
        response = request_orig2(*args, **k_args)
        if response.status == 401 or response.status == 403:
            refresh_response = oauth._refresh(request_orig2)
            if oauth._invalid:
                return refresh_response
            else:
                log.info('token refresh: %s', oauth.access_token)
                new_h = '{}{}'.format('Bearer ', oauth.access_token)
                client.additional_headers['Authorization'] = new_h
                k_args['headers']['Authorization'] = new_h
            return request_orig2(*args, **k_args)
        else:
            return response

    client.http_client.request = new_request2
    return client
