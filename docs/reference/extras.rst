Extra Notes
===========

TODO: these are some notes from the previous README that need merging in to the
new documentation format.

GPS News
--------
For a neat workaround to the GPS info stripping see this project  https://github.com/DennyWeinberg/manager-for-google-photos

Introduction
------------
For a very good description and detailed instructions see `Logix's Article at Linux Uprising`_

.. _`Logix's Article at Linux Uprising`: https://www.linuxuprising.com/2019/06/how-to-backup-google-photos-to-your.html



It is only for Google Photos download / backup purposes. It cannot upload photos to Google Photos.

This project uses the new Google Photos API see https://developers.google.com/photos/
and `Google Project Setup`_.

.. _`Google Project Setup`: docs/google-project-setup.rst

After doing a full sync you will have 2 directories off of the specified root:

* **photos** - contains all photos and videos from your Google Photos Library organized into folders with the
  structure 'photos/YYYY/MM' where 'YYYY/MM' is the date the photo/video was taken. The filenames within a folder
  will be as per the original upload except that duplicate names will have a suffix ' (n)' where n is the duplicate number
  of the file (this matches the approach used in the official Google tool for Windows).

* **albums** - contains a folder hierarchy representing the set of albums  and shared albums in your library. All
  the files are symlinks to content in the photos folder. The folder names  will be
  'albums/YYYY/MM Original Album Name'.


Known Issues
------------

- Installing on a slow machine (like old Raspberry Pi) or network may cause timeouts in pipenv.

  - This can be resolved by setting an environment variable ``export PIPENV_TIMEOUT=240``

- Some mounted filesystems including NFS, CIFS and AFP do not support file locks and database access will fail on them.

  - To fix, use the parameter --db-path to specify a location for your DB on the local disk. This will perform better anyway.


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

- For the most up to date notes on creating a client id see `bullyrooks.com`_.
- My previous notes on creating a client id are here `Oauth2 for gphotos-sync`_

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
For some detailed notes on using docker see `bullyrooks.com`_.

You can run the tool from the container using |docker|_. The container has 2 mount points:

.. |docker| replace:: prebuilt Docker image
.. _docker: https://hub.docker.com/r/gilesknap/gphotos-sync

-  ``/storage`` this is where your photos will be stored. You can mount single directory, or multiple subdirectories in case you want to backup multiple accounts
-  ``/config`` the directory that contains ``client_secret.json`` file

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


Scheduling a Regular Backup
---------------------------
On linux you can add gphotos-sync to your cron schedule easily. See https://crontab.guru/
for tips on how to configure regular execution of a command. You will need a script that
looks something like this::

    #!/bin/bash

    cd /mnt/bigdisk/GilesPhotos/gphotos-code
    /home/giles/.local/bin/pipenv run ./gphotos-sync  /mnt/bigdisk/GilesPhotos/ $@ >> /home/giles/logs/gphotos.log --logfile /tmp 2>&1

Note that I give a full path to the local install of pipenv since cron will not load
your profile and hence PATH.

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

.. _`bullyrooks.com`: https://bullyrooks.com/index.php/backing-up-google-photos-to-your-synology-nas/