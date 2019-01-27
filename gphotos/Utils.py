#!/usr/bin/env python3
# coding: utf8
import re
from datetime import datetime
import logging

log = logging.getLogger(__name__)

DATE_NORMALIZE = re.compile(r'(\d\d\d\d).(\d\d).(\d\d).(\d\d).(\d\d).(\d\d)')
SHORT_DATE_NORMALIZE = re.compile(r'(\d\d\d\d).(\d\d).(\d\d)')
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_ONLY = "%Y-%m-%d"
MINIMUM_DATE = None


# incredibly windows cannot handle dates below 1980
def safe_str_time(date_time, date_format):
    if date_time < minimum_date():
        date_time = minimum_date()
    return date_time.strftime(date_format)


def safe_timestamp(d: datetime) -> float:
    if d < minimum_date():
        d = minimum_date()
    return d.timestamp()


def date_to_string(date_t):
    """
    :param (int) date_only:
    :param (datetime) date_t:
    :return (str):
    """
    return date_t.strftime(DATE_FORMAT)


def maximum_date():
    return datetime.max


def minimum_date():
    global MINIMUM_DATE
    if MINIMUM_DATE is None:
        # determine the minimum date that is usable on the
        # current platform (is there a better way to do this?)
        d = datetime.min.replace(year=1900)
        try:
            _ = d.timestamp()
        except (ValueError, OverflowError, OSError):
            d = datetime.min.replace(year=1970)
            try:
                _ = d.timestamp()
            except (ValueError, OverflowError, OSError):
                d = datetime.min.replace(year=1980)  # crikey MS Windows!
        MINIMUM_DATE = d
    return MINIMUM_DATE


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
