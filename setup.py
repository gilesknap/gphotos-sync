#!/usr/bin/env python3

from setuptools import setup, find_packages

module_name = "gphotos-sync"

install_reqs = [
    'exif',
    'appdirs',
    'requests_oauthlib',
    'PyYaml',
    'selenium',
]

with open("README.rst", "rb") as f:
    long_description = f.read().decode("utf-8")

setup(
    name=module_name,
    version='2.9.1',
    python_requires='>=3.6',
    license='MIT',
    platforms=['Linux', 'Windows', 'Mac'],
    description='Google Photos and Albums backup tool',
    packages=find_packages(exclude=("tests.*", "tests", "etc.*", "etc")),
    entry_points={
        "console_scripts": ['gphotos-sync = gphotos.Main:main']
    },
    long_description=long_description,
    install_requires=install_reqs,
    package_data={'': ['gphotos/sql/gphotos_create.sql', 'LICENSE']},
    include_package_data=True,
    author='Giles Knap',
    author_email='gilesknap@gmail.com',
    url='https://github.com/gilesknap/gphotos-sync'
)
