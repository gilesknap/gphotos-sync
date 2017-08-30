#!/usr/bin/python
# coding: utf8
import time


def retry(count, func, *arg, **k_arg):
    for retry_no in range(count):
        try:
            res = func(*arg, **k_arg)
        except Exception as e:
            print("\nRETRYING due to", e)
            print "Call was:", func, arg, k_arg
            time.sleep(.1)
            continue
        return res
