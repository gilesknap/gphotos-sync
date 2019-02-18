#!/usr/bin/env python3

from setuptools import setup, find_packages
module_name = "gphotos-sync"

packages = [x for x in find_packages()]
setup(
    name=module_name,
    python_requires='>=3.6',
    setup_requires=['pbr'],
    pbr=True,
    packages=packages,
    package_data={'': ['gphotos/sql/gphotos_create.sql']},
    include_package_data=True)

