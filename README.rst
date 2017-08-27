====================
 Google Photos Sync
====================

Google Photos Sync downloads your Google Photos to the local file system.
It attempts to backup all the photos as stored in Google Drive, but also
the album information and additional Google Photos generated content that does
not appear in Drive. The only API for accessing the latter two is picasa web and
this is now severely crippled by (Google) design.

It currently does not have upload features. Uploading of album info is no
longer possible since Google deprecated most of the picasa API see details
here: https://developers.google.com/picasa-web/docs/3.0/releasenotes. Uploading
of files via the drive API counts against Quota.

If in future a Google Photos API is provided by Google then an update to two
way sync is possible.

Primary Goals
--------------
* provide a file system backup so it is possible to monitor for accidental deletions (or deletions caused by bugs) in very large photo collections
* make it possible to switch to a different photo management system in future if this ever becomes desirable/necessary

Known Issues
------------

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

    gphotos-sync TARGET_DIRECTORY

The first time, it will ask you to go to an url and copy back the authorization code in order
to authorize the client to access your Google Photos through Google Drive.

usage: gphotos-sync [-h] [--quiet] [--include-video]
                    [--start-folder START_FOLDER] [--start-date START_DATE]
                    [--end-date END_DATE] [--new-token] [--index-only]
                    root_folder

Google Photos download tool

positional arguments:
  root_folder           root of the local folders to download into

optional arguments:
  -h, --help            show this help message and exit
  --quiet               quiet (no output)
  --include-video       include video types in sync
  --start-folder START_FOLDER
                        Google Photos folder to sync e.g. "Google
                        Photos/2017/08", defaults to root
  --start-date START_DATE
                        Set the earliest date of files to sync
  --end-date END_DATE   Set the latest date of files to sync
  --new-token           Request new token
  --index-only          Only build the index of files in .gphotos.db - no
                        downloads


