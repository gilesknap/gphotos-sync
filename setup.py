#!/usr/bin/env python3

from setuptools import setup, find_packages

module_name = "gphotos-sync"

packages = [x for x in find_packages(exclude=['test/*'])]

install_reqs = [
    'python-magic',
    'piexif',
    'urllib3',
    'appdirs',
    'requests',
    'requests_oauthlib',
    'PyYaml',
]

with open("README.rst", "rb") as f:
    long_description = f.read().decode("utf-8")

setup(
    name=module_name,
    version=2.7,
    python_requires='>=3.6',
    packages=packages,
    entry_points={
        "console_scripts": ['gphotos-sync = gphotos.Main:main']
    },
    long_description=long_description,
    install_requires=install_reqs,
    package_data={'': ['gphotos/sql/gphotos_create.sql']},
    include_package_data=True,
    author='Giles Knap',
    author_email='gilesknap@gmail.com',
    url='https://github.com/gilesknap/gphotos-sync'
)
