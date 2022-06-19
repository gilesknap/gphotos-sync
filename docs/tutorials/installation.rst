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

.. _Container:

Execute in a container
======================

This project now automatically releases a container image with each release.
The latest image will be here ``ghcr.io/gilesknap/gphotos-sync``.

Your container has two volumes ``/config`` for the client_secret.json file and 
``/storage`` for the backup data. You should map these to host folders if you
want to see them outside of the container.

Hence the typical way to launch the container with docker runtime would be::

    $ CONFIG=$HOME/.config/gphotos-sync
    $ STORAGE=$HOME/My_photos_backup
    $ docker run --rm -v $CONFIG:/config -v $STORAGE:/storage -p 8080:8080 -it ghcr.io/gilesknap/gphotos-sync /storage

The options ``-p 8080:8080 -it`` are required for the first invocation only, 
so that the browser can find authentication service. 

Note that the authentication flow uses a redirect url that sends authentication 
token back to the process. The default redirect is localhost:8080 and you can 
adjust the port with ``--port<PORT_NUMBER>``. 

Headless gphotos-sync Servers
-----------------------------
 
The authentication 
flow only allows localhost for security reasons so the first run must always
be done on a machine with a browser.

If you are running on a NAS or other headless server you will first 
need to run locally so that you can do initial login flow with a browser.
Then copy <TARGET>/.gphotos.token to the server. For this
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

Running gphotos-sync
====================

To begin a backup with default settings create a new empty TARGET DIRECTORY 
in which your backups will go and type::

    gphotos-sync <TARGET_DIRECTORY>

For the first invocation you will need login the user whose files you
are backing up, see `Login`.

Once this process has started it will first index all of your library and then
start a download of the files. The download is multithreaded and will use
most of your internet bandwidth, you can throttle it if needed using the 
``--threads`` option.

For a description of additional command line parameters type::

    gphotos-sync --help

As the download progresses it will create folders and files in your target 
directory. The layout of these is described in `Folders`.

Next time you run gphotos-sync it will incrementally download all new files
since the previous. It is OK to abort gphotos-sync and restart it, this will
just cause it to continue from where the abort happened.
