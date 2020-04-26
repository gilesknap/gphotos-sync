|build_status|
|coverage|
|codacy|
|pypi|


Google Photos Sync
==================

Introduction
------------
For a very good description and detailed instructions see `Logix's Article at Linux Uprising`_

.. _`Logix's Article at Linux Uprising`: https://www.linuxuprising.com/2019/06/how-to-backup-google-photos-to-your.html

Google Photos Sync downloads your Google Photos to the local file system. It will backup all the photos the
user uploaded to
Google Photos, but also the album information and additional Google Photos 'Creations' (animations, panoramas,
movies, effects and collages).

This project uses the new Google Photos API see https://developers.google.com/photos/.

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

- Installing on a slow machine (like old Raspberry Pi) or network may cause timeouts in pipenv. 

  - This can be resolved by setting an environment variable `export PIPENV_TIMEOUT=240`
  
- Some mounted filesystems including NFS, CIFS and AFP do not support file locks and database access will fail on them.

  - To fix, use the paramter --db-path to sepcify a location for your DB on the local disk. This will perform better anyway.

Known Issues with Google API
----------------------------
A few outstanding limitations of the Google API restrict what can be achieved. All these issues have been reported
to Google and this project will be updated once they are resolved.

- There is no way to discover modified date of library media items. Currently ``gphotos-sync`` will refresh your local
  copy with any new photos added since the last scan but will not update any photos that have been modified in Google
  a. Photos. A feature request has been submitted to Google.
  
  - https://issuetracker.google.com/issues/122737849.
  
- FIXED BY GOOGLE. Some types of video will not download using the new API. 

  - https://issuetracker.google.com/issues/116842164.
  - https://issuetracker.google.com/issues/141255600
  
- The API strips GPS data from images.

  - https://issuetracker.google.com/issues/80379228.
  
- Video download transcodes the videos even if you ask for the original file (=vd parameter).
  My experience is that the result is looks similar to the original
  but the compression is more clearly visible. It is a smaller file with approximately 60% bitrate (same resolution).
  
  - https://issuetracker.google.com/issues/80149160
  
- Burst shots are not supported. You will only see the first file of a burst shot.

  - https://issuetracker.google.com/issues/124656564


Install and configure
---------------------
For an easy option which does not require the install of Python and Pipenv you can use the Snap Store version, see https://ubuntu.com/blog/safely-backup-google-photos.

For some help on getting python working on Windows see https://github.com/gilesknap/gphotos-sync/issues/63.

On linux, you can install pipenv using ``pip3 install --user pipenv`` and then make sure that ``~/.local/bin/`` is in your path.

To install the latest published version from PyPi, simply::

   mkdir gphotos-sync
   cd gphotos-sync
   pipenv install gphotos-sync

Or if you don't want to use pipenv, create a virtual environment and::

   pip install gphotos-sync

(see https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/ if you are not familiar with virtualenv)

To work from the source code, clone the git repository and use pipenv to create a virtual environment and run
the code. (if you don't have pipenv, then I recommend getting it - but you can manually create a virtualenv and use
'python setup.py install' instead) ::

  git clone https://github.com/gilesknap/gphotos-sync.git
  cd gphotos-sync
  pipenv install .
  pipenv run gphotos-sync

In order to work, ``gphotos-sync`` first needs a valid client id linked to a project
authorized to use the 'Photos Library API'. It is not provided in the distribution. Each client id
is given a (large) limited number of free API calls to Google Services. If this distribution shared the client id,
all users would share this resource limit. This is a little fiddly but only needs to be done once.

- Create a client id using these instructions `Oauth2 for gphotos-sync`_
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
.. _`Oauth2 for gphotos-sync`: https://docs.google.com/document/d/1ck1679H8ifmZ_4eVbDeD_-jezIcZ-j6MlaNaeQiz7y0/edit?usp=sharing


How to use it
-------------

Once the script is configured, you are now ready to use it using the simple following command line::

  cd <installed directory>
  pipenv run gphotos-sync TARGET_DIRECTORY

Or, if you used virtualenv and pip instead of pipenv, activate the virtualenv and::

  gphotos-sync TARGET_DIRECTORY
  
The first time, it will give you a link to an authorization page in order to authorize the client to access your
Google Photos.

For a description of additional command line parameters type::

  gphotos-sync --help

Running with docker
-------------------
You can run the tool from the container using |docker|_. The container has 2 mount points:

.. |docker| replace:: prebuilt Docker image
.. _docker: https://hub.docker.com/r/gilesknap/gphotos-sync

-  ``/storage`` this is where your photos will be stored. You can mount single directory, or multiple subdirectories in case you want to backup multiple accounts
-  ``/config`` the directory that contains `client_secret.json` file
  
To run ::

    docker run \
       -ti \
       --name gphotos-sync \
       -v /YOUR_LOCAL/PATH/TO_PHOTOS:/storage \
       -v /YOUR_LOCAL/PATH/TO_CONFIG:/config \
       gilesknap/gphotos-sync \
      /storage

To remove the container (for instance if you want to run it on scheduled basis and do a cleanup)::

    docker rm -f $(docker ps --filter name=gphotos-sync -qa) 2> /dev/null
    
To run then remove the container::

    docker run \
      --rm \
      -it \
      --name gphotos-sync \
      -v /YOUR_LOCAL/PATH/TO_PHOTOS:/storage \
      -v /YOUR_LOCAL/PATH/TO_CONFIG/client_id.json:/config/client_secret.json:ro \
      gilesknap/gphotos-sync \
      --log-level INFO \
      /storage

Appendix
========

Rescans
-------
I have just experienced an issue with duplication of files when doing a rescan
(--rescan or --flush-index). It looks like some items have changed in the
library and this can result in the same file downloading
twice. I would guess this has something to do with Google removing the
Drive link to Photos.

UPDATE: I now know that this was caused by subtle changes in the metadata.
It seems Google does not guarantee to deliver exactly the same files each
time you scan the library (but to be fair, I think they are tuning things for
the better).

The problem did cause some duplicate named files to be downloaded twice
overwriting their duplicate peer. Note that no files were lost from the library
(since gphotos is read-only) and it was possible to repair things by either:

- using the local comparison feature of gphotos-sync against a prior backup
- or downloading the library again from scratch

In summary, most people will not be affected by the issue I
had unless they have very old photos with duplicate file names.

My detailed notes on the subject are here: `giles notes`_

..  _`giles notes`: https://docs.google.com/document/d/1hK_GDLUwP7PpD1VmDbDsYLyTfbZGv2C-JCihezYhiLY/edit?usp=sharing

Google GPS Info update
----------------------
UPDATE: the GPS scraping no longer works and has been removed. I am investigating a couple of other avenues.

Google does not seem to be interested in fxing the issue of stripping location info from the EXIF info of images
downloaded via their API (see https://issuetracker.google.com/issues/80379228#comment80). So I am investigating a workaround. See the option --get-locations. It uses
Selenium to scrape the GPS info off of the Google Website (your google creds required I'm afraid) and
insert them into the DB of synchronized files. It does not yet update the EXIF on the local files but this
is a minor addition and I'll implement if there is interest.

Have a try and let me know what you think. Hurry, because Google is removing the ability to log in using
automation soon!

.. |build_status| image:: https://travis-ci.org/gilesknap/gphotos-sync.svg?branch=master&style=flat
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
