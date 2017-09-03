#!/usr/bin/python
# coding: utf8
import time


def retry(count, func, *arg, **k_arg):
    last_e = None
    for retry_no in range(count):
        try:
            res = func(*arg, **k_arg)
            return res
        except Exception as e:
            last_e = e
            print("\nRETRYING due to".format(e))
            print "Call was:", func, arg, k_arg
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
                print("\nRETRYING iterator due to {}".format(e))
                time.sleep(.1)
        yield last_item
