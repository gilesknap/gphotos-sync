|build_status|
|coverage|
|codacy|
|pypi|


Google Photos Sync
==================

Google Photos Sync downloads your Google Photos to the local file system. It will backup all the photos the
user uploaded to
Google Photos, but also the album information and additional Google Photos 'Creations' (animations, panoramas,
movies, effects and collages).

After doing a full sync you will have 2 directories off of the specified root:

* **photos** - contains all photos and videos from your Google Photos Library organized into folders with the
  structure 'photos/YYYY/MM' where 'YYYY/MM' is the date the photo/video was taken. The filenames within a folder
  will be as per the original upload except that duplicate names will have a suffix ' (n)' where n is the duplicate number
  of the file (this matches the approach used in the official Google tool for Windows).

* **albums** - contains a folder hierarchy representing the set of albums  and shared albums in your library. All
  the files are symlinks to content in the photos folder. The folder names  will be
  'albums/YYYY/MM Original Album Name'.

In addition there will be further folders when using the --compare-folder option.  The option is used to make a
comparison of the contents of your library with a local folder such as a previous backup. The comparison does not require
that the files are arranged in the same folders, it uses meta-data in the files such as create date and
exif UID to match pairs of items. The additional folders after a comparison will be:

* **comparison** a new folder off of the specified root containing the following:

* **missing_files** - contains symlinks to the files in the comparison folder that were not found in the Google
  Photos Library. The folder structure is the same as that in the comparison folder. These are the
  files that you would upload to Google Photos via the Web interface to restore from backup.

* **extra_files** - contains symlinks into to the files in photos folder which appear in the Library but not in the
  comparison folder. The folder structure is the same as the photos folder.

* **duplicates** - contains symlinks to any duplicate files found in the comparison folder. This is a flat structure
  and the symlink filenames have a numeric prefix to make them unique and group the duplicates together.

NOTES:

* the comparison code uses an external tool 'ffprobe'. It will run without it but will not be able to
  extract metadata from video files and revert to relying on Google Photos meta data and file modified date (this is
  a much less reliable way to match video files, but the results should be OK if the backup folder
  was originally created using gphotos-sync).
* If you have shared albums and have clicked 'add to library' on items from others' libraries then you will have two
  copies of those items and they will show as duplicates too.

Known Issues
------------
A few outstanding limitations of the Google API restrict what can be achieved. All these issues have been reported
to Google and this project will be updated once they are resolved.

* There is no way to discover modified date of library media items. Currently ``gphotos-sync`` will refresh your local
  copy with any new photos added since the last scan but will not update any photos that have been modified in Google
  Photos. A feature request has been submitted to Google see https://issuetracker.google.com/issues/122737849.
* Some types of video will not download using the new API. This mostly is restricted to old formats of video file (in
  my library it is a subset of videos shot before 2010). Google is looking at this problem see
  https://issuetracker.google.com/issues/116842164
* The API strips GPS data from images see https://issuetracker.google.com/issues/80379228.
* Video download transcodes the videos even if you ask for the original file (=vd parameter) see
  https://issuetracker.google.com/issues/80149160. My experience is that the result is looks similar to the original
  but the compression is more clearly visible. It is a smaller file with approximately 60% bitrate (same resolution).
* Burst shots are not supported. You will only see the first file of a burst shot. See 
  https://issuetracker.google.com/issues/124656564


Install and configure
---------------------
To install the latest published version from PyPi, simply::

   pipenv install gphotos-sync

Or if you don't want to use pipenv::

   sudo pip install gphotos-sync

To work from the source code, clone the git repository and use pipenv to create a virtual environment and run
the code. (if you don't have pipenv, then I recommend getting it - but you can use
'sudo python setup.py install' instead) ::

  git clone https://github.com/gilesknap/gphotos-sync.git
  cd gphotos-sync
  pipenv install .
  pipenv run gphotos-sync

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
  - ``~/.config/gphotos-sync/`` under Linux,
  - ``C:\Users\<username>\AppData\Local\gphotos-sync\gphotos-sync\`` under Windows.

Also note that for Windows you will need to enable symbolic links permission for the account that gphoto-sync
will run under. See `Enabling SymLinks on Windows`_.
 

.. _`Google Developer Console`: https://developers.google.com/console/
.. _`Creating a project procedure`: https://cloud.google.com/resource-manager/docs/creating-managing-projects
.. _`Activating and Deactivating APIs procedure`: https://cloud.google.com/apis/docs/enable-disable-apis
.. _`setting up oauth 2.0 procedure`: https://support.google.com/cloud/answer/6158849?hl=en
.. _`Enabling SymLinks on Windows`: https://community.perforce.com/s/article/3472


How to use it
-------------

Once the script is configured, you are now ready to use it using the simple following command line::

  cd <installed directory>
  pipenv run gphotos-sync TARGET_DIRECTORY

Or if you used sudo pip instead of pipenv::

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

.. |codacy| image:: https://api.codacy.com/project/badge/Grade/5a5b8c359800462e90ee2ba21a969f87
   :alt: Codacy Badge
   :target: https://app.codacy.com/app/giles.knap/gphotos-sync?utm_source=github.com&utm_medium=referral&utm_content=gilesknap/gphotos-sync&utm_campaign=Badge_Grade_Dashboard

.. |pypi| image:: https://badge.fury.io/py/gphotos-sync.svg
   :target: https://badge.fury.io/py/gphotos-sync
