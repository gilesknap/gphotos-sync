.. _Tutorial:

Initial Setup
=============

Before you run gphotos_sync for the first time you will need to create
your own OAuth client ID. This is a once only operation and the instructions
are here: `Client ID`. 

- Once the client ID is created, download it as ``client_secret.json`` and save 
  it under the application configuration directory:

  - ``~/Library/Application Support/gphotos-sync/`` under Mac OS X,
  - ``~/.config/gphotos-sync/`` under Linux,
  - ``C:\Users\<username>\AppData\Local\gphotos-sync\gphotos-sync\`` under Windows.

If you are running Windows, also see `Windows`.

You are ready to run gphotos-sync for the first time, either locally or 
inside of a container. The first run will require a user login see
`Login`


Execute in a container
======================

This project now automatically releases a container image with each release to
Pypi. The latest image will be here ``ghcr.io/gilesknap/gphotos-sync``.

Your container will need access to two host filesystem items. (You could
use container volumes if you prefer but would need to bootstrap the 
client_secret.json)

    - The hosts client_secret.json filepath denoted <SECRET>
    - The host (or shared) folder for your backup denoted <ROOT>

Hence you can run the container with the docker runtime like this:

    ``docker run -v <SECRET>/.config/gphotos-sync -v <ROOT>:/photos --net=host -it ghcr.io/gilesknap/gphotos-sync /photos``

Note that if you are running on a NAS or other headless server you will first 
need to run locally so that you can do initial login flow.
Then copy the .gphotos.token to the server. For this
first run you could use the following options so that no backup is performed:

    ``--skip-files --skip-albums --skip-index``


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


Install gphotos-sync
--------------------

You can now use ``pip`` to install the application::

    python3 -m pip install gphotos-sync

If you require a feature that is not currently released you can also install
directly from github::

    python3 -m pip install git+git://github.com/gilesknap/gphotos-sync.git

The application should now be installed and the commandline interface on your path.
You can check the version that has been installed by typing::

    gphotos-sync --version

