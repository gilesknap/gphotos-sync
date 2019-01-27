#!/usr/bin/env python3
# coding: utf8
import re
from datetime import datetime
import logging

log = logging.getLogger(__name__)

DATE_NORMALIZE = re.compile(r'(\d\d\d\d).(\d\d).(\d\d).(\d\d).(\d\d).(\d\d)')
SHORT_DATE_NORMALIZE = re.compile(r'(\d\d\d\d).(\d\d).(\d\d)')
PatType = type(DATE_NORMALIZE)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_ONLY = "%Y-%m-%d"
MINIMUM_DATE = None


# incredibly windows cannot handle dates below 1980
def safe_str_time(date_time: datetime, date_format: str) -> str:
    if date_time < minimum_date():
        date_time = minimum_date()
    return date_time.strftime(date_format)


def safe_timestamp(d: datetime) -> float:
    if d < minimum_date():
        d = minimum_date()
    return d.timestamp()


def date_to_string(date_t: datetime):
    return date_t.strftime(DATE_FORMAT)


def maximum_date() -> datetime:
    return datetime.max


def minimum_date() -> datetime:
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


def date_string_normalize(date_in: str,
                          pattern_in: PatType,
                          pattern_out: str) -> datetime:
    result = None
    matches = pattern_in.match(date_in)
    if matches:
        normalized = pattern_out.format(*matches.groups())
        result = datetime.strptime(normalized, DATE_FORMAT)
    return result


def string_to_date(date_string: str) -> datetime:
    result = None
    if date_string:
        result = date_string_normalize(date_string, DATE_NORMALIZE,
                                       '{}-{}-{} {}:{}:{}')
        if result is None:
            result = date_string_normalize(date_string, SHORT_DATE_NORMALIZE,
                                           '{}-{}-{} 00:00:00')
        if result is None:
            log.warning('WARNING: time string %s illegal', date_string)

    return result
