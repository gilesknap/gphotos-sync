# coding: utf8

# noinspection SqlWithoutWhere
match = \
    ["""
-- stage 0 - remove previous matches 
UPDATE LocalFiles
set RemoteId = NULL  ;
""",
     """
-- stage 1 - look for unique matches 
UPDATE LocalFiles
set RemoteId = (SELECT RemoteId
                FROM SyncFiles
                WHERE LocalFiles.OriginalFileName == SyncFiles.OrigFileName
                  AND (LocalFiles.Uid == SyncFiles.Uid AND
                       LocalFiles.CreateDate = SyncFiles.CreateDate)
                  -- 32 character ids are legitimate and unique
                  OR (LocalFiles.Uid == SyncFiles.Uid AND
                  length(LocalFiles.Uid) == 32)
)
WHERE LocalFiles.Uid notnull and LocalFiles.Uid != 'not_supported'
;
""",
     """    
-- stage 2 - mop up entries that have no UID (this is a small enough 
-- population that filename + CreateDate is probably unique)
with pre_match(RemoteId) as
   (SELECT RemoteId from LocalFiles where RemoteId notnull)
UPDATE LocalFiles
set RemoteId = (SELECT RemoteId
            FROM SyncFiles
            WHERE LocalFiles.OriginalFileName == SyncFiles.OrigFileName
              AND LocalFiles.CreateDate = SyncFiles.CreateDate
            AND SyncFiles.RemoteId NOT IN (select RemoteId from pre_match)
)
WHERE LocalFiles.RemoteId isnull
;
""",
     """        
-- stage 3 FINAL - mop up on filename only
with pre_match(RemoteId) as
   (SELECT RemoteId from LocalFiles where RemoteId notnull)
UPDATE LocalFiles
set RemoteId = (SELECT RemoteId
            FROM SyncFiles
            WHERE LocalFiles.OriginalFileName == SyncFiles.OrigFileName
            AND SyncFiles.RemoteId NOT IN (select RemoteId from pre_match)
)
WHERE LocalFiles.RemoteId isnull
;
"""]

missing_files = """select * from LocalFiles where RemoteId isnull;"""

pre_extra_files = """
-- overwrite NULL RemoteIds or extra_files will get no matches
update LocalFiles set RemoteId='not_found' where RemoteId isnull
"""

extra_files = """
select * from SyncFiles where RemoteId not in (select RemoteId from LocalFiles)
-- and uid not in (select uid from LocalFiles where length(SyncFiles.Uid) = 32)
;
"""

duplicate_files = """
with matches(RemoteId) as (
  select RemoteId from LocalFiles
  GROUP BY LocalFiles.RemoteId
  HAVING COUNT(LocalFiles.RemoteId) > 1
)
SELECT *
FROM LocalFiles
       JOIN matches
WHERE LocalFiles.RemoteId = matches.RemoteId
;
"""
