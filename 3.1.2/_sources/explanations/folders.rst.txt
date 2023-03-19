.. _Folders:

Folder Layout
=============

After doing a full sync you will have 2 directories off of the specified root:

Media Files
-----------

photos:
    contains all photos and videos from your Google Photos Library organized 
    into folders with the structure 'photos/YYYY/MM' where 'YYYY/MM' is 
    the date the photo/video was taken. The filenames within a folder will 
    be as per the original upload except that duplicate names will have a 
    suffix ' (n)' where n is the duplicate number of the file (this matches 
    the approach used in the official Google tool for Windows).

albums:
    contains a folder hierarchy representing the set of albums and shared
    albums in your library. All the files are symlinks to content in the photos
    folder. The folder names will be 'albums/YYYY/MM Original Album Name'.

Note that these are the default layouts and you can change what is downloaded
and how it is layed out with command line options. See the help for details::

    gphotos-sync --help

Other Files
-----------

The following files will also appear in the root folder:-
             
  - gphotos.sqlite: the database that tracks what files have been indexed,
    you can open this with sqlite3 to examine what media and metadata you have.
  - gphotos.log: a log of the most recent run, including debug info       
  - gphotos.lock: the lock file used to make sure only one gphotos-sync runs
    at a time   
  - gphotos.trace: a trace file if logging is set to trace level. This logs 
    the calls to the Google Photos API. 
  - gphotos.bad_ids.yaml: A list of bad entries that cause the API to get 
    an error when downloading. Delete this file to retry downloading these
    bad items.
