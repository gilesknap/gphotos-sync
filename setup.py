#!/usr/bin/env python2

from setuptools import setup, find_packages
module_name = "gphotos-sync"

packages = [x for x in find_packages()]
setup(
    name=module_name,
    setup_requires=['pbr'],
    pbr=True,
    packages=packages,
    package_data={'': ['gphotos/sql/gphotos_create.sql']},
    include_package_data=True)

