-- noinspection SqlResolveForFile

-- helpful queries for checking the picasa photo to drive file matching

-- find files that are not creations but were not found in the drive folders
---------------------------------------------------------------------------
-- my collection has 85 of these when using --all-drive switch
-- and 253 when not. Hence 168 items outside of Google photos are referenced
--  in albums - it looked like this happened in auto created albums when I
-- uploaded our travel blog to google Drive.
-- numbers are down to 253 and 82 after adding Date matching to +-12 hours
-- which is a paltry gain on 90,000 pics for loads of extra queries
-- update:- 1.0 eschews date matching and there are 104 out of 100,000 files
-- missing from drive and most seem to be genuinely missing - now use picasa to
-- download these
SELECT * from SyncFiles WHERE SyncFiles.MediaType is 1 and SymLink is NULL
and OrigFileName not LIKE "%COLLAGE.jpg"
and OrigFileName not LIKE "%EFFECTS.jpg"
and OrigFileName not LIKE "%ANIMATION.gif"
and OrigFileName not LIKE "%PANO.jpg"
and OrigFileName not LIKE "%MOVIE.%";

-- list of files that are outside of the Google Photos folder
SELECT * from SyncFiles WHERE SyncFiles.Path not like '%/drive/%';

-- files that are in drive but also look like they are 'creations'
SELECT * from SyncFiles WHERE SyncFiles.MediaType is 0
and (OrigFileName LIKE "%COLLAGE.jpg"
or OrigFileName LIKE "%EFFECTS.jpg"
or OrigFileName LIKE "%ANIMATION.gif"
or OrigFileName LIKE "%PANO.jpg"
or OrigFileName LIKE "MOVIE.%");

-- files in albums that did not get a match but the filename exists in drive
SELECT FileName
FROM SyncFiles
WHERE MediaType is 0
INTERSECT
SELECT FileName
FROM SyncFiles
WHERE MediaType is 1;

-- find albums that reference media outside of Google Photos
-- this one shows why we need to index all of drive instead of just G-Photos
select SyncFiles.Path, SyncFiles.FileName, Albums.AlbumName from AlbumFiles
INNER JOIN SyncFiles ON AlbumFiles.DriveRec=SyncFiles.Id
INNER JOIN Albums ON AlbumFiles.AlbumRec=Albums.AlbumId
WHERE SyncFiles.Path not LIKE '%Google Photos%' and SyncFiles.MediaType is 0;

SELECT * from SyncFiles WHERE SyncFiles.MediaType is 1;

-- this one below is anomalous -> they should match, but do not
SELECT * from SyncFiles where SyncFiles.FileName is '20171126_124838.jpg';
SELECT * from SyncFiles where SyncFiles.FileSize is 2091021;

-- get all the files in an album
SELECT SyncFiles.Path, SyncFiles.Filename, SyncFiles.ModifyDate, Albums.AlbumName,
  Albums.EndDate FROM AlbumFiles
  INNER JOIN SyncFiles ON AlbumFiles.DriveRec=SyncFiles.Id
  INNER JOIN Albums ON AlbumFiles.AlbumRec=Albums.AlbumId
  WHERE Albums.AlbumName LIKE '%';

SELECT * from SyncFiles WHERE SyncFiles.MediaType is not 0;
SELECT * from SyncFiles WHERE FileName like 'P1040748%';
SELECT * from SyncFiles WHERE Path like '%Cars%';

SELECT * from AlbumFiles;
