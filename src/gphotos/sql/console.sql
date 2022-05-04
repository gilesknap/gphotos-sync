-- stage 1
-- affects 80167 rows
-- 80167, remoteIDs found
-- duplicate count 1905 (in local files)
UPDATE LocalFiles
set RemoteId = (SELECT RemoteId
                FROM SyncFiles
                WHERE (LocalFiles.OriginalFileName == SyncFiles.OrigFileName or
                       LocalFiles.FileName == SyncFiles.FileName)
                  AND (LocalFiles.Uid == SyncFiles.Uid or
                       LocalFiles.CreateDate = SyncFiles.CreateDate)
)
WHERE LocalFiles.Uid notnull and LocalFiles.Uid != 'not_supported'
;

-- stage 2 - mop up entries that have no UID (this is a small enough population that filename is probably unique)
-- affects 16109 rows
-- 90057 total remoteIDs found
-- duplicate count 2569
-- important: prematch provides the list of matches before we start the main query
with prematch(RemoteId) as
       (SELECT RemoteId from LocalFiles where RemoteId notnull)
UPDATE LocalFiles
set RemoteId = (SELECT RemoteId
                FROM SyncFiles
                WHERE (LocalFiles.OriginalFileName == SyncFiles.OrigFileName or
                       LocalFiles.FileName == SyncFiles.FileName)
                  AND LocalFiles.CreateDate = SyncFiles.CreateDate
                AND SyncFiles.RemoteId NOT IN (select RemoteId from prematch)
                  --AND not Exists (SELECT 1 FROM LocalFiles L WHERE L.RemoteId = Syncfiles.RemoteId)
)
WHERE LocalFiles.RemoteId isnull
;

-- stage 3 FINAL - mop up on filename alone
-- affects 5841 rows
-- 92141 total remoteIDs found
-- duplicate count 2680
-- missing 3689, Only in SyncFiles 4554, Total in SyncFiles 96695
-- 92141+4554 = 96695 so that verifies the numbers
-- ALSO - when I uploaded the 3689 missing to Google Photos, it reports 1691 when I go to
--  https://photos.google.com/search/_tra_ - I think this implies many are duplicates of
--  files that already reside in GP
with prematch(RemoteId) as
       (SELECT RemoteId from LocalFiles where RemoteId notnull)
UPDATE LocalFiles
set RemoteId = (SELECT RemoteId
                FROM SyncFiles
                WHERE (LocalFiles.OriginalFileName == SyncFiles.OrigFileName or
                       LocalFiles.FileName == SyncFiles.FileName)
                AND SyncFiles.RemoteId NOT IN (select RemoteId from prematch)
)
WHERE LocalFiles.RemoteId isnull
;

-- Todo, (at least one problem remains)
--  stage 2 and 3 will not match duplicates, because after the first is found, the Exists eliminates it
--  this means that where Google Drive has two copies of a file with no Uid, the 2nd will end up in the missing list
--  it looks like about 200 files fit this category and lots are AVIs
-- Fixed with temporary Table approach
-- Todo this could probably be compressed into a single CTE ???

-- THIS demonstrates that the duplicates are actually duplicates created by InSync (probably) -------------------
-- 1905 total
with matches(RemoteId) as (
  select RemoteId
  from LocalFiles
  GROUP BY LocalFiles.RemoteId
  HAVING COUNT(LocalFiles.RemoteId) > 1
)
SELECT *
FROM LocalFiles
       JOIN matches
WHERE LocalFiles.RemoteId = matches.RemoteId;

-- THIS discovers the matched files
select *
from SyncFiles
where RemoteId = (SELECT RemoteId
                  from LocalFiles
                  where SyncFiles.RemoteId = LocalFiles.RemoteId)
;

-- THIS discovers the remaining unmatched LocalFile (looks like they are genuinely missing)
-- REPRESENTS missing files that Insync has eaten and I restored manually back up to Google Drive
--  looks good and is the whole point of this entire exercise!
select *
from LocalFiles
where RemoteId isnull;

-- THIS discovers the remaining unmatched in Syncfiles
-- REPRESENTS files that Google Drive has not synced over from Google Photos
-- ALSO this is files that Google Drive holds OUTSIDE of the Google Photos folder
--  because drive integration copies them to Photos, but their location in drive
--  remains - e.g. Drive/Noah/Drawings
select *
from Syncfiles
where RemoteId
        in (SELECT S.RemoteId
           FROM SyncFiles S
                  LEFT JOIN LocalFiles L ON S.RemoteId = L.RemoteId
           WHERE L.RemoteId ISNULL);
;
-- OR ?? --
select *
FROM SyncFiles
WHERE SyncFiles.RemoteId NOT IN (SELECT LocalFiles.RemoteId from LocalFiles);



------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------
-- scratch work --------------------------------------------------------------------------------------------------


-- resetting
drop index LocalRemoteIdIdx;
create index LocalRemoteIdIdx on LocalFiles (RemoteId);
update LocalFiles set RemoteId = null;

select * from LocalFiles where FileName = 'Y2013 M08 D30 Noah August - 2013-08-30 20.38.22.mp4';

SELECT A.Path, A.FileName, A.CreateDate, B.CreateDate, A.Description, B.RemoteId, A.Uid
FROM (SELECT Path, FileName, OriginalFileName, DuplicateNo, Description, CreateDate, Uid FROM LocalFiles) A
       JOIN
     (SELECT RemoteId, FileName, OrigFileName, Description, DuplicateNo, CreateDate, Uid from SyncFiles) B
     ON (A.OriginalFileName == B.OrigFileName) AND (A.Uid == B.Uid or A.CreateDate = B.CreateDate)
;



select count(RemoteId), *
from LocalFiles
group by RemoteId
having count(RemoteId) > 1;




UPDATE
  software
SET purchprice = (SELECT purchprice
                  FROM softwarecost
                  WHERE id = software.id)
where EXISTS(SELECT purchprice
             FROM softwarecost
             WHERE id = software.id)


-- NO 502 not unique! (what does this mean?)
SELECT A.Path,
       B.Path,
       A.FileName,
       A.CreateDate,
       B.CreateDate,
       A.Description,
       Count(B.RemoteId),
       B.RemoteId
FROM (SELECT Path, RemoteId, FileName, OrigFileName, Description, DuplicateNo, CreateDate from SyncFiles) B
       JOIN
     (SELECT Path, FileName, OriginalFileName, DuplicateNo, Description, CreateDate FROM LocalFiles) A
     ON (A.OriginalFileName == B.OrigFileName) AND (A.Description like B.Description)
       AND (A.DuplicateNo == B.DuplicateNo)

GROUP BY A.RemoteId
HAVING COUNT(B.RemoteId) > 1
;

-- THIS WORKS and is fast with indexes in place ------------------------------------------------------------------
-- Note the below inspection fails to recognize the Common Table Expression 'Where'
-- noinspection SqlWithoutWhere
with matches(Id, NewRemoteId) as (
  select local.Id      as Id,
         sync.RemoteId as NewRemoteId
  from LocalFiles local,
       SyncFiles sync
  where local.FileName = sync.FileName
    and local.Uid = sync.Uid
)

update LocalFiles
Set RemoteId =
      (SELECT matches.NewRemoteId from matches where LocalFiles.Id = matches.Id)
;
----------------------------------------------------------------------------------------------------------
--missing?
select *
from LocalFiles
where not RemoteId isnull;

-- AFTER ABOVE - check for missing matches --------------------------------------------------------------------------
SELECT A.Path,
       A.FileName,
       A.CreateDate,
       B.CreateDate,
       A.Description,
       B.Description,
       B.RemoteId,
       A.RemoteId
FROM (SELECT Path, FileName, OriginalFileName, DuplicateNo, Description, CreateDate, RemoteId FROM LocalFiles) A
       JOIN
     (SELECT RemoteId, FileName, OrigFileName, Description, DuplicateNo, CreateDate from SyncFiles) B
     ON (A.OriginalFileName == B.OrigFileName) AND
        A.DuplicateNo == B.DuplicateNo AND A.RemoteId isnull
;

-- random helpful stuff ---------------------------------------------------------
select *
from LocalFiles
where RemoteId = 'AHsKWi-2Apn3v_XfHWbzMUJ-qH5-OcOsgo7Bb29qZlI7P9vQylageXH8ppBrBz-0Nd3DSSD1byzk2m7bCHMhuj1Fu62T-ziPvQ';

select COUNT(OriginalFileName), *
from LocalFiles
where MimeType like 'video%'

GROUP BY OriginalFileName
HAVING COUNT(OriginalFileName) > 1
;

select *
from LocalFiles
where RemoteId ISNULL; -- 8582
select count()
from LocalFiles
where RemoteId != ''; --88548
select count()
from LocalFiles; --97130
select count()
from SyncFiles
where RemoteId != '';

select *
from LocalFiles
where OriginalFileName Like '1987%';
select *
from SyncFiles
where OrigFileName Like '1987%';
-- ------------------------------------------------------------------------------

-- Looking at uniqueness of filenames -------------------------------------------
-- all unique file names
select *
from LocalFiles
GROUP BY LocalFiles.OriginalFileName
HAVING COUNT(LocalFiles.OriginalFileName) = 1;
-- non unique file names
with matches(OriginalFileName) as (
  select OriginalFileName
  from LocalFiles
  GROUP BY LocalFiles.OriginalFileName
  HAVING COUNT(LocalFiles.OriginalFileName) > 1
)
SELECT *
FROM LocalFiles
       JOIN matches
WHERE LocalFiles.OriginalFileName = matches.OriginalFileName;

-- non unique Uid
with matches(Uid) as (
  select Uid
  from LocalFiles
  GROUP BY LocalFiles.Uid
  HAVING COUNT(LocalFiles.Uid) > 1
)
SELECT *
FROM LocalFiles
       JOIN matches
WHERE LocalFiles.Uid = matches.Uid;


-- fast query on the join
with matches(Id, FileName, remote_id, Uid) as (
  select local.Id               as Id,
         local.OriginalFileName as FileName,
         sync.RemoteId          as remote_id,
         sync.Uid               as Uid
  from LocalFiles local,
       SyncFiles sync
  where local.CreateDate = sync.CreateDate and local.FileName = sync.FileName
     or local.FileName = sync.FileName and local.Uid = sync.Uid
  -- local.OriginalFileName = sync.OrigFileName
  --AND local.Description like sync.Description
  --AND local.DuplicateNo = sync.DuplicateNo
)
Select *
from matches
;


-- caution
delete
from LocalFiles;


-- *****************************************************************************************************************
-- Early attempts


-- SUPER SLOW QUERY - speed this bad boy up !!!!
SELECT FileName
From LocalFiles
WHERE Id in (
  SELECT RemoteId
  FROM SyncFiles
  WHERE LocalFiles.OriginalFileName = OrigFileName
    AND LocalFiles.Description like Description
    AND LocalFiles.DuplicateNo = DuplicateNo);


-- update RemoteID on all matching LocalFile rows
-- SLOW VERSION
-- **********************************************
UPDATE LocalFiles
SET RemoteId = (
  SELECT RemoteId
  FROM SyncFiles
  WHERE LocalFiles.OriginalFileName = OrigFileName
    AND LocalFiles.Description like Description
    AND LocalFiles.DuplicateNo = DuplicateNo
);
-- **********************************************

select *
from SyncFiles
where OrigFileName like '% (_).%';


update LocalFiles
set RemoteId = '';

delete
from LocalFiles;
delete
from LocalFiles
where Description = 'cof';
select *
from LocalFiles
where Description = 'cof';


create index LocalMatchIdx on LocalFiles (OriginalFileName, DuplicateNo, Description);
create index SyncMatchIdx on SyncFiles (OrigFileName, DuplicateNo, Description);

SELECT Id,
       RemoteId,
       Path,
       FileName,
       OriginalFileName,
       DuplicateNo,
       MimeType,
       Description,
       FileSize,
       ModifyDate,
       CreateDate,
       SyncDate
FROM LocalFiles
WHERE RemoteId LIKE "%"
  AND FileName LIKE "00-NoahAndSnake.jpg"
  and Path
  LIKE "/media/Data/GoogleDriveInsync/Google Photos";

select *
from SyncFiles
where FileName like 'Y2006 M07 D29 %'

select * from PreMatched;

        SELECT SyncFiles.Path, SyncFiles.Filename, Albums.AlbumName,
        Albums.EndDate, Albums.RemoteId FROM AlbumFiles
        INNER JOIN SyncFiles ON AlbumFiles.DriveRec=SyncFiles.RemoteId
        INNER JOIN Albums ON AlbumFiles.AlbumRec=Albums.RemoteId
        WHERE Albums.AlbumName LIKE '%Brick%'

select * from Albums where Albums.AlbumName LIKE '%Brick%';
select * from AlbumFiles where AlbumFiles.AlbumRec='AHsKWi_BLrIVGjOhABLD0FRbYKA_BHHiTpi1yYsD_bVnw7PkYfwd63kCLNHnWSyRfmv1P3XnWgXaO7HiWkEaFbc8heU7tZL-aw';
select * from SyncFiles where SyncFiles.RemoteId='AHsKWi-FYFJ3yjQWFZTnB8-KlRVmJU6QEAevu5LcBrVDANQ_JrQhUl27hgiqxjcrAojUcXyN3awY'
select FileName from SyncFiles where FileName like '%HEIC';

select * from SyncFiles where exists(select * from SyncFiles where FileName like '%HEIC');

INSERT INTO SyncFiles (FileName, RemoteId)  SELECT 'TT', 'aaa' WHERE NOT EXISTS
                    (SELECT * FROM SyncFiles
                    WHERE Filename = 'TTP');
select * from SyncFiles where FileName = 'TT';
delete from SyncFiles where FileName = 'TT';