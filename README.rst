====================
 Google Photos Sync
====================

Google Photos Sync downloads your Google Photos to the local file system.
It attempts to backup all the photos as stored in Google Drive, but also
the album information and additional Google Photos 'Creations' (animations, panoramas, movies, effects and collages) that do not appear in Drive. The only API for accessing the latter two is picasa web and this is now severely crippled. Hopefully Google intends to replace it with something like native photos support in Google Drive.

Gphotos-sync currently does not have upload features. Uploading of album info is no
longer possible since Google deprecated most of the picasa API see details
here: https://developers.google.com/picasa-web/docs/3.0/releasenotes. Uploading
of files via the drive API counts against Quota.

If in future a Google Photos API is provided by Google then an two
way sync will be added.

After doing a full sync you will have 3 directories off of the specified root:

* drive - contains all photos and videos from your google drive with original folder hierarchy and file names
* picasa - contains any media that was referenced in an album but not found in drive. This will usually include all google photos creations such as ANIMATIONS, EFFECTS etc. These have the original file names and are organized into folders by date.
* albums - contains a folder hierarchy representing the set of albums in your photos (but not shared ones). All the files are symlinks to content in one of the other folders.

In drive and picasa, folders containing duplicate files names are handled by adding (1) etc to the file name. (as per Google's drive sync tool for windows)

In the root folder a sqlite database holds an index of all media and albums. Useful to find out about the state of your photo store. You can open it with the sqlite3 tool and perform any sql queries.

This has been tested against my photo store of nearly 100,000 photos.

Primary Goals
--------------
* provide a file system backup so it is possible to monitor for accidental deletions (or deletions caused by bugs) in very large photo collections
* make it possible to switch to a different photo management system in future if this ever becomes desirable/necessary
* use the Google Drive API as much as possible and the deprecated picasa web API as little as possible.
  * picasa is only used to get lists of album contents and to download items that are missing from Google Drive.

Known Issues
------------
* Shared folders are not seen, this is a limitation of picasa web api and is not likely to be fixed
* Albums of over 10,000 photos are truncated at 10,000. This is again due to a limitation of the web api. Unfortunately this means you will not automatically retrieve all google photos creations if you have > 10,0000 photos. I suggest creating a 'Creations' album and copying all creations into it, this will then sync (and any future creations will be handled by the gloabl 'Auto Backup' album
* Todo - handle deletes and moves
* Todo - remember last synced date and default to incremental backup
* Todo make python 3 compatible

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


How to use it
-------------

Once the script is configured, you are now ready to use it using the simple following command line::

    gphotos-sync TARGET_DIRECTORY

The first time, it will ask you to go to an url and copy back the authorization code in order
to authorize the client to access your Google Photos through Google Drive.

Description of the cmdline parameters below:-

usage: gphotos-sync [-h] [--quiet] [--include-video] [--start-date START_DATE]
                    [--end-date END_DATE] [--new-token] [--index-only]
                    [--picasa-only] [--all-drive] [--album ALBUM]
                    [--drive-file DRIVE_FILE]
                    root_folder

Google Photos download tool

positional arguments:
  root_folder           root of the local folders to download into

optional arguments:
  -h, --help            show this help message and exit
  --quiet               quiet (no output)
  --include-video       include video types in sync
  --start-date START_DATE
                        Set the earliest date of files to sync
  --end-date END_DATE   Set the latest date of files to sync
  --new-token           Request new token
  --index-only          Only build the index of files in .gphotos.db - no
                        downloads
  --picasa-only         skip drive scan, (assume that the db is up to date
                        with drive files - for testing)
  --all-drive           when True all folders in drive are scanned for media.
                        when False only files in the Google Photos folder are
                        scanned. If you do not use this option then you may
                        find you have albums that reference media outside of
                        the Google Photos folder and these would then get
                        downloaded into the picasa folder. The only downside
                        is that the folder structure is lost.
  --album ALBUM         only index a single album (for testing)
  --drive-file DRIVE_FILE
                        only index a single drive file (for testing)
