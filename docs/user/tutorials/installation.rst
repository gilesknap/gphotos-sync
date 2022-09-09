Installation
============

Check your version of python
----------------------------

You will need python 3.8 or later. You can check your version of python by
typing into a terminal::

    $ python3 --version


Create a virtual environment
----------------------------

It is recommended that you install into a “virtual environment” so this
installation will not interfere with any existing Python software::

    $ python3 -m venv /path/to/venv
    $ source /path/to/venv/bin/activate


Installing the library
----------------------

You can now use ``pip`` to install the library and its dependencies::

    $ python3 -m pip install python3-pip-skeleton

If you require a feature that is not currently released you can also install
from github::

    $ python3 -m pip install git+https://github.com/DiamondLightSource/python3-pip-skeleton.git

The library should now be installed and the commandline interface on your path.
You can check the version that has been installed by typing::

    $ python3-pip-skeleton --version
