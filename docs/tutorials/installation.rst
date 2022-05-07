Initial Setup
=============

Before you run gphotos_sync for the first time you will need to create
your own OAuth client ID. This is a once only operation and the instructions
are here: `Client ID`

Local Installation
==================

To install on your workstation (linux Mac or Windows) follow this section.

Check your version of python
----------------------------

You will need python 3.7 or later. You can check your version of python by
typing into a terminal::

    python3 --version


Create a virtual environment
----------------------------

It is recommended that you install into a “virtual environment” so this
installation will not interfere with any existing Python software::

    python3 -m venv /path/to/venv
    source /path/to/venv/bin/activate


Installing the library
----------------------

You can now use ``pip`` to install the application::

    python3 -m pip install gphotos-sync

If you require a feature that is not currently released you can also install
from github::

    python3 -m pip install git+git://github.com/gilesknap/gphotos-sync.git

The library should now be installed and the commandline interface on your path.
You can check the version that has been installed by typing::

    gphotos-sync --version

Execute using docker
====================

TODO: add info here for the ghcr.io image
