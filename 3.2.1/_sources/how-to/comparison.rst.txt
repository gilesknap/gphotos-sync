Comparing The Google Photos Library With Local files
====================================================

.. warning::
  This feature is deprecated. Working out if files in the filesystem match
  those in the Google Library more of an art than a science. I used this 
  feature to prove that gphotos-sync had worked on my library when I fully 
  committed to Google Photos in 2015 and it has not been touched since. It uses
  complicated SQL functions to do the comparison and is probably not working 
  anymore.

  I'm leaving it enabled in case anyone wants to have a go or if any 
  contributors want to resurrect it. But I'm not supporting this feature
  anymore.

There will be additional folders created when using the --compare-folder option.  

The option is used to make a
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
