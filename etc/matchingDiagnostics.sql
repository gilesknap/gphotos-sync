
-- find files that are not creations but were not found in the drive folders
SELECT * from SyncFiles WHERE SyncFiles.MediaType is 1
and OrigFileName not LIKE "%COLLAGE.jpg"
and OrigFileName not LIKE "%EFFECTS.jpg"
and OrigFileName not LIKE "%ANIMATION.gif"
and OrigFileName not LIKE "%PANO.jpg"
and OrigFileName not LIKE "%MOVIE.%";

-- list of files that are outside of the Google Photos folder
SELECT * from SyncFiles WHERE SyncFiles.Path not like '%Google Photos%'

-- files that are in drive but also look like they are 'creations'
SELECT * from SyncFiles WHERE SyncFiles.MediaType is 0
and (OrigFileName LIKE "%COLLAGE.jpg"
or OrigFileName LIKE "%EFFECTS.jpg"
or OrigFileName LIKE "%ANIMATION.gif"
or OrigFileName LIKE "%PANO.jpg"
or OrigFileName LIKE "%MOVIE.%");

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


