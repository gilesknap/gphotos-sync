====================
 Google Photos Sync
====================

Google Photos Sync is a simple script that will synchronize on a local filesystem
all the photos stored in your Google Photos account.

All the photo filenames are automatically renamed according to the date and camera model 
and are stored in a ``YEAR/MONTH/`` folder hierarchy.


Install and configure
---------------------

Just run ``python setup.py`` from the source directory to install it in your system.

In order to work, ``gphotos-sync`` first needs a valid client id linked to a project
authorized to use the Google Drive API. It is not provided in the distribution.

To do so:

* Create a project on `Google Developer Console`_, following the `Creating a project procedure`_,

* Authorize it to use the Google Drive API, following the `Activating and desactivating APIs procedure`_,

* Create a Client ID by following the `setting up oauth 2.0 procedure`_ with application type set to `Other`,

* Once the client ID is created, download it as ``client_secret.json`` and save it under the application 
  configuration directory:

  - ``~/Library/Application Support/gphotos-sync/`` under Mac OS X,
  - ``~/.config/gphotos-sync/`` under Linux.

.. _`Google Developer Console`: https://developers.google.com/console/
.. _`Creating a project procedure`: https://developers.google.com/console/help/new/#creatingaproject
.. _`Activating and Desactivating APIs procedure`: https://developers.google.com/console/help/new/#activating-and-deactivating-apis
.. _`setting up oauth 2.0 procedure`: https://developers.google.com/console/help/new/#setting-up-oauth-20

Currently photo api relies on a hacked version of gdata: TODO - fork the gdata repo and
point dependency at it.

How to use it
-------------

Once the script is configured, you are now ready to use it using the simple following command line::

    gphotos-sync download TARGET_DIRECTORY

The first time, it will ask you to go to an url and copy back the authorization code in order
to authorize the client to access your Google Photos through Google Drive.

supported commands:-
    download    : copies files down to local disk
    re-upload   : uploads any modified files (TODO un-tested in current version)
    fix-db      : repair meta data store (FUTURE)

usage: gphotos-sync [-h] [--quiet] [--dry-run] [--include-video]
                    [--start-folder START_FOLDER] [--start-date START_DATE]
                    [--end-date END_DATE] [--new-token]
                    COMMAND root_folder

Google Photos simple synchronization tool

positional arguments:
  COMMAND               command to execute
  root_folder           root of the local folders to download into

optional arguments:
  -h, --help            show this help message and exit
  --quiet               quiet (no output)
  --dry-run             show what would have been transferred
  --include-video       include video types in sync
  --start-folder START_FOLDER
                        Google Photos folder to sync e.g. 2017/08, defaults to
                        root
  --start-date START_DATE
                        Set the earliest date of files to sync
  --end-date END_DATE   Set the latest date of files to sync
  --new-token           Request new token

