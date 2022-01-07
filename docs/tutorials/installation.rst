Installation
============

.. note::

    For installation inside DLS, please see the internal documentation on
    ``dls-python3`` and ``pipenv``. Although these instructions will work
    inside DLS, they are intended for external use.

    If you want to contribute to the library itself, please follow
    the `../reference/contributing` instructions.


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

You can now use ``pip`` to install the library::

    python3 -m pip install dls_python3_skeleton

If you require a feature that is not currently released you can also install
from github::

    python3 -m pip install git+git://github.com/dls-controls/dls-python3-skeleton.git

The library should now be installed and the commandline interface on your path.
You can check the version that has been installed by typing::

    dls-python3-skeleton --version
