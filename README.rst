.. |build_status| image:: https://travis-ci.org/gilesknap/gphotos-sync.svg?branch=rc1&style=flat
    :target: https://travis-ci.org/dls-controls/pymalcolm
    :alt: Build Status

.. |coverage| image:: https://coveralls.io/repos/gilesknap/gphotos-sync.svg?branch=rc1&service=github
    :target: https://coveralls.io/github/dls-controls/pymalcolm?branch=master
    :alt: Test coverage


==================
Google Photos Sync
==================

Quick Warning
"""""""""""""
This software does work as advertised but currently has the
following limitations:

* If you edit a photo using Google Photos the modified version pf the photo will not be synchronised
* if you edit a photo in Google Drive it will be synchronized but you wont see the change in Google Photos
* The date filtering features are not yet timezone aware and only work on modified date (not photo taken date)
* if you have moved or deleted photos they will not be deleted locally unless you specify --flush-index --do-delete
* if you are using the new 'Backup and Sync for Google Photos and Google Drive' I suggest using --all-drive option as this will preserve the folder structure of photos uploaded from your Windows PCs
* shared albums will not be synchronized

The intention of this project was to be able to back up everything
in my 100,000 photo collection in Google Photos. I assumed that all I needed was
a backup of the Google Photos folder in Drive and then get the album info
from the picasa API. However this is not adequate for the following reasons:-

* Your photo files in drive will diverge from those in Google Photos itself
* edits in google photos are not reflected in the drive folder
* edits in the drive folder are not reflected in Google Photos
* you are at liberty to delete subfolders of Drive's Google Photos folder and this does not affect Google Photos itself
* all 'creations' that Google Photos makes are not seen in Drive (Movies, Animations, Panoramas etc.)
* about 0.01% of my Google Photos photos are not seen in Drive for no apparent reason

A good discussion on the issue is here https://productforums.google.com/forum/#!topic/photos/8FWyZhdIFNU

I am going to try and resolve the above but it will most likely involve
downloading two copies of a photo which has diverged between Google Photos and
Drive. The shared folders issue cannot be fixed at all.

I persist with this project because it looks likely that the picasa API will go
away completely at some point and hopefully be replaced an alternative that integrates well with
Drive. Otherwise I might as well capitulate and just use the old mostly
deprecated picasa API.

TODO: to avoid all 'Drive confusion' I have provided the --skip-drive option.
BUT at present this only accesses photos that are referenced in an album. I will
fix this soon.

Description
===========
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
-------------
* provide a file system backup so it is possible to monitor for accidental deletions (or deletions caused by bugs) in very large photo collections
* make it possible to switch to a different photo management system in future if this ever becomes desirable/necessary
* use the Google Drive API as much as possible and the deprecated picasa web API as little as possible.
  (picasa is only used to get lists of album contents and to download items that are missing from Google Drive)

Known Issues
------------
* Shared folders are not seen, this is a limitation of picasa web api and is not likely to be fixed
* Albums of over 10,000 photos are truncated at 10,000. This is again due to a limitation of the web api. Unfortunately this means you will not automatically retrieve all google photos creations if you have > 10,0000 photos. I suggest creating a 'Creations' album and copying all creations into it, this will then sync (and any future creations will be handled by the global 'Auto Backup' album
* Todo - handle deletes and moves -DONE (but requires --flush-index)
* Todo - remember last synced date and default to incremental backup - DONE
* Todo make python 3 compatible

Install and configure
---------------------
 run ``python setup.py`` from the source directory to install it in your system.

In order to work, ``gphotos-sync`` first needs a valid client id linked to a project
authorized to use the Google Drive API. It is not provided in the distribution.

To do so:

* Create a project on `Google Developer Console`_, following the `Creating a project procedure`_,

* Authorize it to use the Google Drive API, following the `Activating and deactivating APIs procedure`_,

* Create a Client ID by following the `setting up oauth 2.0 procedure`_ with application type set to `Other`,

* Once the client ID is created, download it as ``client_secret.json`` and save it under the application
  configuration directory:

  - ``~/Library/Application Support/gphotos-sync/`` under Mac OS X,
  - ``~/.config/gphotos-sync/`` under Linux.

.. _`Google Developer Console`: https://developers.google.com/console/
.. _`Creating a project procedure`: https://developers.google.com/console/help/new/#creatingaproject
.. _`Activating and Deactivating APIs procedure`: https://developers.google.com/console/help/new/#activating-and-deactivating-apis
.. _`setting up oauth 2.0 procedure`: https://developers.google.com/console/help/new/#setting-up-oauth-20


How to use it
-------------

Once the script is configured, you are now ready to use it using the simple following command line::

    gphotos-sync TARGET_DIRECTORY

The first time, it will send your browser to an authorization page in order
to authorize the client to access your Google Photos and Google Drive.

Description of the cmdline parameters below:-

usage: gphotos-sync [-h] [--quiet] [--skip-video] [--start-date START_DATE]
                    [--end-date END_DATE] [--new-token] [--index-only]
                    [--do-delete] [--skip-index] [--skip-picasa]
                    [--skip-drive] [--flush-index] [--all-drive]
                    [--album ALBUM] [--drive-file DRIVE_FILE]
                    root_folder

Google Photos download tool

positional arguments:
  root_folder           root of the local folders to download into

optional arguments:
  -h, --help            show this help message and exit
  --quiet               quiet (no output)
  --skip-video          skip video types in sync
  --start-date START_DATE
                        Set the earliest date of files to sync
  --end-date END_DATE   Set the latest date of files to sync
  --new-token           Request new token
  --index-only          Only build the index of files in .gphotos.db - no
                        downloads
  --do-delete           remove local copies of files that were deleted from
                        drive/picasa
  --skip-index          Use index from previous run and start download
                        immediately
  --skip-picasa         skip picasa scan, albums will not be scanned
  --skip-drive          skip drive scan, (assume that the db is up to date
                        with drive files - for testing)
  --flush-index         delete the index db, re-scan everything
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