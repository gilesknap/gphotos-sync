Google Photos Sync (gphotos-sync)
=================================

|code_ci| |docs_ci| |coverage| |pypi_version| |license|

Google Photos Sync is a backup tool for your Google Photos cloud storage.

============== ==============================================================
PyPI           ``pip install gphotos-sync``
Source code    https://github.com/gilesknap/gphotos-sync
Documentation  https://gilesknap.github.io/gphotos-sync
Releases       https://github.com/gilesknap/gphotos-sync/releases
============== ==============================================================

Intro
=====
Google Photos Sync downloads all photos and videos the user has uploaded to 
Google Photos. It also organizes the media in the local file system using 
album information. Additional Google Photos 'Creations' such as 
animations, panoramas, movies, effects and collages are also backed up.

This software is read only and never modifies your cloud library in any way,
so there is no risk of damaging your data. 

Warning: Google API Issues
==========================

There are a number of long standing issues with the Google Photos API that mean it is not possible
to make a true backup of your media. In particular:

- Videos are transcoded to lower quality
- Raw or Original photos are converted to 'High Quality'
- GPS info is removed from photos metadata

For details of the Bugs reported to Google see https://github.com/gilesknap/gphotos-sync/issues/119.

To join in a discussion on this issue see https://github.com/gilesknap/gphotos-sync/discussions/347.


Quick Start
===========

To get started see `Tutorial <https://gilesknap.github.io/gphotos-sync/main/tutorials/installation.html>`_


.. |code_ci| image:: https://github.com/gilesknap/gphotos-sync/workflows/Code%20CI/badge.svg?branch=main
    :target: https://github.com/gilesknap/gphotos-sync/actions?query=workflow%3A%22Code+CI%22
    :alt: Code CI

.. |docs_ci| image:: https://github.com/gilesknap/gphotos-sync/workflows/Docs%20CI/badge.svg?branch=main
    :target: https://github.com/gilesknap/gphotos-sync/actions?query=workflow%3A%22Docs+CI%22
    :alt: Docs CI

.. |coverage| image:: https://codecov.io/gh/gilesknap/gphotos-sync/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/gilesknap/gphotos-sync
    :alt: Test Coverage

.. |pypi_version| image:: https://img.shields.io/pypi/v/gphotos-sync.svg
    :target: https://pypi.org/project/gphotos-sync
    :alt: Latest PyPI version

.. |license| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :target: https://opensource.org/licenses/Apache-2.0
    :alt: Apache License

..
    Anything below this line is used when viewing README.rst and will be replaced
    when included in index.rst

See https://gilesknap.github.io/gphotos-sync for more detailed documentation.


