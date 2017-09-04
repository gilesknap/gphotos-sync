
SELECT * from SyncFiles WHERE SyncFiles.MediaType is 1
and OrigFileName not LIKE "%COLLAGE.jpg"
and OrigFileName not LIKE "%EFFECTS.jpg"
and OrigFileName not LIKE "%ANIMATION.gif"
and OrigFileName not LIKE "%PANO.jpg"
and OrigFileName not LIKE "%MOVIE.%";

SELECT * from SyncFiles WHERE SyncFiles.MediaType is 0
and (OrigFileName LIKE "%COLLAGE.jpg"
or OrigFileName LIKE "%EFFECTS.jpg"
or OrigFileName LIKE "%ANIMATION.gif"
or OrigFileName LIKE "%PANO.jpg"
or OrigFileName LIKE "%MOVIE.%");

SELECT FileName
FROM SyncFiles
WHERE MediaType is 0
INTERSECT
SELECT FileName
FROM SyncFiles
WHERE MediaType is 1;

SELECT * from SyncFiles WHERE FileName is '20160909_192437.mp4';