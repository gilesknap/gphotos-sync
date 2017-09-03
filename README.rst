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

After doing a full sync you will have 3 directories off of the specified root:
* currently relies on a patch to gdata-python-client see open issue for details of how to patch
* drive - contains all photos and videos from your google drive with original folder hierarchy and file names
* picasa - contains any media that was referenced in an album but not found in drive. This will usually include all google photos creations such as ANIMATIONS, EFFECTS etc. These have the original file names and organized into folders by date.
* albums - contains a folder hierarchy representing the set of albums in your photos (but not shared ones). All the files are symlinks to content in one of the other folders.

In drive and picasa folders duplicate files names are handled by adding (1) etc. (as per Google's drive sync tool for windows)

in the root folder a sqlite database holds an index of all media and albums. Useful to find out about the state of your photo store.

This has been tested against my photo store of nearly 100,000 photos.

Primary Goals
--------------
* provide a file system backup so it is possible to monitor for accidental deletions (or deletions caused by bugs) in very large photo collections
* make it possible to switch to a different photo management system in future if this ever becomes desirable/necessary
* use the Google Drive API as much as possible and the deprecated picasa web API as little as possible.
*   picasa is only used to get lists of album contents and to download items that are missing from Google Drive.

Known Issues
------------
* Shared folders are not seen, this is a limitation of picasa web api and is not likely to be fixed
* Albums of over 10,000 photos are truncated at 10,000 again due to a limitation of the web api. Unfortunately this means you will not automatically retrieve all google photos creations if you have > 10,0000 photos. I suggest creating a 'Creations'
* To investigate - Download of video files seems slower than it should be
* Todo - handle deletes and moves
* Todo - remember last synced date and default to incremental backup

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
  --start-date START_DATE
                        Set the earliest date of files to sync
  --end-date END_DATE   Set the latest date of files to sync
  --new-token           Request new token
  --index-only          Only build the index of files in .gphotos.db - no
                        downloads


