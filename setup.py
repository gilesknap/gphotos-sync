#!/usr/bin/env python

from setuptools import setup, find_packages
module_name = "gphotos-sync"

packages = [x for x in find_packages()]
setup(
    setup_requires=['pbr'],
    pbr=True,
    packages=packages)

