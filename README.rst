|build_status|
|coverage|


==================
Google Photos Sync
==================

Version 2.0 Major Upgrade
==============================
Google has released a new Google Photos API and this project is now based on that API. The myriad issues with the
previous approach using Drive API and Picasa API are now resolved. However, see new known issues below.

In addition to this, the new code uses parallel processing to speed up downloads considerably.

Description
===========

Google Photos Sync downloads your Google Photos to the local file system. It will backup all the photos the
user uploaded to
Google Photos, but also the album information and additional Google Photos 'Creations' (animations, panoramas,
movies, effects and collages).

After doing a full sync you will have 2 directories off of the specified root:

* **photos** - contains all photos and videos from your Google Photos Library organized into folders with the
  structure 'photos/YYYY/MM' where 'YYYY/MM' is the date the photo/video was taken. The filenames within a folder
  will be as per the original upload except that duplicate names will have a suffix ' (n)' where n is the duplicate number
  of the file (this matched the approach used in the official Google tool for Windows).

* **albums** - contains a folder hierarchy representing the set of albums  and shared albums in your library. All
  the files are symlinks to content in one of the other folders. The folder names  will be
  'albums/YYYY/MM Original Album Name'.

In the root folder a sqlite database holds an index of all media and albums. Useful to find out about the state of your
photo store. You can open it with the sqlite3 tool and perform any sql queries.

This has been tested against my photo store of nearly 100,000 photos.


Currently Download Only
-----------------------
``gphotos-sync`` currently does not have upload features. I do intend to provide an upload facility so that it would
be possible to download your library and upload it to another account, or to upload new photos. Full two way
synchronization capability is a much bigger challenge and at present I've not come up with a robust enough approach
for this.


Primary Goals
-------------
* Provide a file system backup so it is easy to monitor for accidental deletions (or deletions caused by bugs)
  in very large photo collections.

* Make it feasible to switch to a different photo management system in future if this ever becomes desirable/necessary

Known Issues
------------
* There is no way to discover modified date of library media items. Currently ``gphotos-sync`` will refresh your local
  copy with any new photos added since the last scan but will not update any photos that have been modified in Google
  Photos. A feature request has been submitted to Google see https://issuetracker.google.com/issues/122737849.
* Some types of video will not download using the new API. This mostly is restricted to old formats of video file (in
  my library it is a subset of videos shot before 2010). Google is looking at this problem see
  https://issuetracker.google.com/issues/116842164
* The API strips GPS data from images see https://issuetracker.google.com/issues/80379228.
* Video download transcodes the videos even if you ask for the original file (=vd parameter) see https://issuetracker.google.com/issues/80149160. My experience is that the result is indistinguishable visually but it is a smaller file with approximately 60% bitrate (same resolution).



Install and configure
---------------------
Clone the git repository and run the following from the source directory to install it in your system ::

  python setup.py build
  sudo pip install -r requirements.txt
  sudo python setup.py install

In order to work, ``gphotos-sync`` first needs a valid client id linked to a project
authorized to use the 'Photos Library API'. It is not provided in the distribution. Each client id
is given a (large) limited number of free API calls to Google Services. If this distribution shared the client id,
all users would share this resource limit. This is a little fiddly but only needs to be done once.

To do this:

- Create a project on `Google Developer Console`_, following the `Creating a project procedure`_,

- Authorize it to use the 'Photos Library API', following the `Activating and deactivating APIs procedure`_,

- Create a Client ID by following the `setting up oauth 2.0 procedure`_ with application type set to **Other**

- Once the client ID is created, download it as ``client_secret.json`` and save it under the application
  configuration directory:

  - ``~/Library/Application Support/gphotos-sync/`` under Mac OS X,
  - ``~/.config/gphotos-sync/`` under Linux.
 

.. _`Google Developer Console`: https://developers.google.com/console/
.. _`Creating a project procedure`: https://cloud.google.com/resource-manager/docs/creating-managing-projects
.. _`Activating and Deactivating APIs procedure`: https://cloud.google.com/apis/docs/enable-disable-apis
.. _`setting up oauth 2.0 procedure`: https://support.google.com/cloud/answer/6158849?hl=en


How to use it
-------------

Once the script is configured, you are now ready to use it using the simple following command line::

  gphotos-sync TARGET_DIRECTORY

The first time, it will give you a link to an authorization page in order to authorize the client to access your
Google Photos.

For a description of additional command line parameters type::

  gphotos-sync --help




.. |build_status| image:: https://travis-ci.org/gilesknap/gphotos-sync.svg?style=flat
    :target: https://travis-ci.org/gilesknap/gphotos-sync
    :alt: Build Status

.. |coverage| image:: https://codecov.io/gh/gilesknap/gphotos-sync/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/gilesknap/gphotos-sync
    :alt: Test coverage

