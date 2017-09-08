-- helpful queries for checking the picasa photo to drive file matching

-- find files that are not creations but were not found in the drive folders
---------------------------------------------------------------------------
-- my collection has 85 of these when using --all-drive switch
-- and 253 when not. Hence 168 items outside of Google photos are referenced
--  in albums - it looked like this happened in auto created albums when I
-- uploaded our travel blog to google Drive.
-- numbers are down to 253 and 82 after adding Date matching to +-12 hours
-- which is a paltry gain on 90,000 pics for loads of extra queries
-- todo still need to do more analysis on how often date matching is being fired

-- TODO trying to get the 253 down by adding date matching with timezone slip
-- TODO  tests - running this test on 4/9/17
-- TODO  at least 2 files suburu?.jpg are in drive and should get a match
-- but most are genuinely missing
-- TODO also need to reinstate 'Auto Backup' and see if there are any other
-- files missing
SELECT * from SyncFiles WHERE SyncFiles.MediaType is 1
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


-- get all the files in an album
SELECT SyncFiles.Path, SyncFiles.Filename, SyncFiles.ModifyDate, Albums.AlbumName,
  Albums.EndDate FROM AlbumFiles
  INNER JOIN SyncFiles ON AlbumFiles.DriveRec=SyncFiles.Id
  INNER JOIN Albums ON AlbumFiles.AlbumRec=Albums.AlbumId
  WHERE Albums.AlbumName LIKE '%Clivedon%';

SELECT * from SyncFiles WHERE SyncFiles.MediaType is not 0;
SELECT * from SyncFiles WHERE FileName like 'P1040748%';
SELECT * from SyncFiles WHERE Path like '%Cars%';