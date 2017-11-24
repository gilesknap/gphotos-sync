|build_status| |coverage|


==================
Google Photos Sync
==================

Description
===========

Google Photos Sync downloads your Google Photos to the local file system. It attempts to backup all the photos as stored in Google Drive, but also
the album information and additional Google Photos 'Creations' (animations, panoramas, movies, effects and collages) that do not appear in Drive.

Note that this primarily works with Google drive and requires that you have ticked the option "Automatically put your Google Photos into a folder in My Drive" in Google Drive settings.

After doing a full sync you will have 3 directories off of the specified root:

* **drive** - contains all photos and videos from your google drive with original folder hierarchy and file names

* **picasa** - contains any media that was referenced in an album but not found in drive. This will usually include all google photos creations such as ANIMATIONS, EFFECTS etc. These have the original file names and are organized into folders by date.

* **albums** - contains a folder hierarchy representing the set of albums in your photos (but not shared ones). All the files are symlinks to content in one of the other folders.

In drive and picasa, folders containing duplicate files names are handled by adding (1) etc to the file name. (as per Google's drive sync tool for windows). If you have used the official Backup tool on Windows your **drive** folder should match that backup (but the order of duplicate files may vary occasionaly).

In the root folder a sqlite database holds an index of all media and albums. Useful to find out about the state of your photo store. You can open it with the sqlite3 tool and perform any sql queries.

This has been tested against my photo store of nearly 100,000 photos.


Currently Download Only
-----------------------
The only API for accessing Album info and Google Photos Creations is picasa web and this is now severely crippled. Hopefully Google intends to replace it with something like native photos support in Google Drive at some point. In the mean time this places some restrictions on what this project can achieve.

``gphotos-sync`` currently does not have upload features. Uploading of album info is no
longer possible since Google deprecated most of the picasa API see details
here: https://developers.google.com/picasa-web/docs/3.0/releasenotes. Uploading
of files via the drive API counts against Quota. 


Primary Goals
-------------
* provide a file system backup so it is possible to monitor for accidental deletions (or deletions caused by bugs) in very large photo collections

* make it possible to switch to a different photo management system in future if this ever becomes desirable/necessary

* use the Google Drive API as much as possible and the deprecated picasa web API as little as possible.
  (picasa is only used to get lists of album contents and to download items that are missing from Google Drive)


Stretch Goal
------------
I would like to provide a linux replacement for the official Google Drive Backup and Sync product (only available for Windows). This means adding two way sync, running as a service and using a reverse engineered Google Photos upload interface in order to upload quota-free photos and videos (this is not an officially supported API).


Known Issues
------------
* Shared folders are not seen, this is a limitation of picasa web api and is not likely to be fixed
* Albums of over 10,000 photos are truncated at 10,000. This is again due to a limitation of the web api. Unfortunately this means you will not automatically retrieve all google photos creations if you have > 10,0000 photos. I suggest creating a 'Creations' album and copying all creations into it, this will then sync (and any future creations will be handled by the global 'Auto Backup' album
* Todo - handle deletes and moves -DONE (but requires --flush-index)
* Todo - remember last synced date and default to incremental backup - DONE
* Todo make python 3 compatible


Install and configure
---------------------
Clone the git repository and run the following from the source directory to install it in your system::

  python setup.py build
  python setup.py install
  pip install -r requirements.txt

In order to work, ``gphotos-sync`` first needs a valid client id linked to a project
authorized to use the Google Drive API. It is not provided in the distribution.

To do so:

- Create a project on `Google Developer Console`_, following the `Creating a project procedure`_,

- Authorize it to use the Google Drive API, following the `Activating and deactivating APIs procedure`_,

- Create a Client ID by following the `setting up oauth 2.0 procedure`_ with application type set to **Other**

- Once the client ID is created, download it as ``client_secret.json`` and save it under the application configuration directory:

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

For a description of additional command line parameters type::

  gphotos-sync --help


Caveats
-------
This software does work as advertised but currently has the
following limitations:

1. If you edit a photo metadata using Google Photos the modified version of the photo will not be synchronised

#. if you edit a photo in Google Drive it will be synchronized but you wont see the change in Google Photos

#. if you have moved or deleted photos they will not be deleted locally unless you specify --flush-index --do-delete

#. shared albums will not be synchronized

The intention of this project was to be able to back up everything
in my 100,000 photo collection in Google Photos. I assumed that all I needed was
a backup of the Google Photos folder in Drive and then get the album info
from the picasa API. However there are a number of issues with this idea:-

- Your photo files in drive will diverge from those in Google Photos itself because:-

  - edits in google photos are not reflected in the drive folder
  - edits in the drive folder are not reflected in Google Photos
  - you are at liberty to delete subfolders of Drive's Google Photos folder and this does not affect Google Photos itself
- all 'creations' that Google Photos makes are not seen in Drive (Movies, Animations, Panoramas etc.)
- about 0.01% of my Google Photos photos are not seen in Drive for no apparent reason

A good discussion on the issues with divergance of Drive/Photos stores is here https://productforums.google.com/forum/#!topic/photos/8FWyZhdIFNU

I have tried to use a comparison of modified date to determine if the Google Photos or Drive held the latest version of a file. However, when uploading a new photo the modified date in Photos/Drive differ in either direction by up to a day or so! Also picasa API reports random modified dates for video files. 

My approach to dealing with these issues is as follows:-

- If the file is seen in both Picasa and Drive, only the Drive version is downloaded

  - This means that the **drive** folder looks exactly the same as the result of the official Windows Google Backup and Sync.

  - Just like the official sync, edits to metadata in Google Photos do not get seen in the local synchroized files

- However because I use file size in the matching algorithm
- 
 - if you edit the photo/video itself it will be seen as a different file
 - and this results in a copy both in Picasa and Google
 - In this case the Picasa file will be referenced by any containing album links

The above represents the best that can be done with the APIs available. It is a little better than the results from using the official Backup and Sync, but still not ideal.

To avoid all this 'Drive confusion' I have provided the --skip-drive option. This uses only the picasa API and therefore gets the most recent versions of Google Photos contents only.
**HOWEVER** this only accesses photos that are referenced in an album AND the most recent 10,000 items. This is a hard limitation of the Deprecated Picasa API and is not going to be fixed.


.. |build_status| image:: https://travis-ci.org/gilesknap/gphotos-sync.svg?style=flat
    :target: https://travis-ci.org/gilesknap/gphotos-sync
    :alt: Build Status

.. |coverage| image:: https://coveralls.io/repos/gilesknap/gphotos-sync/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/gilesknap/gphotos-sync?branch=master
    :alt: Test coverage
