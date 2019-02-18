# coding: utf8

match = \
    ["""
-- stage 1 - look for unique matches 
        UPDATE LocalFiles
set RemoteId = (SELECT RemoteId
                FROM SyncFiles
                WHERE (LocalFiles.OriginalFileName == SyncFiles.OrigFileName or
                       LocalFiles.FileName == SyncFiles.FileName)
                  AND (LocalFiles.Uid == SyncFiles.Uid or
                       LocalFiles.CreateDate = SyncFiles.CreateDate)
                  -- 32 character ids are legitimate and unique
                  OR (LocalFiles.Uid == SyncFiles.Uid AND
                  length(LocalFiles.Uid) == 32)
)
WHERE LocalFiles.Uid notnull and LocalFiles.Uid != 'not_supported' and 
LocalFiles.RemoteId ISNULL
;
""",
     """    
-- stage 2 - mop up entries that have no UID (this is a small enough 
-- population that filename is probably unique)
with pre_match(RemoteId) as
   (SELECT RemoteId from LocalFiles where RemoteId notnull)
UPDATE LocalFiles
set RemoteId = (SELECT RemoteId
            FROM SyncFiles
            WHERE (LocalFiles.OriginalFileName == SyncFiles.OrigFileName or
                   LocalFiles.FileName == SyncFiles.FileName)
              AND LocalFiles.CreateDate = SyncFiles.CreateDate
            AND SyncFiles.RemoteId NOT IN (select RemoteId from pre_match)
)
WHERE LocalFiles.RemoteId isnull
;
""",
     """        
-- stage 3 FINAL - mop up on filename alone
with pre_match(RemoteId) as
   (SELECT RemoteId from LocalFiles where RemoteId notnull)
UPDATE LocalFiles
set RemoteId = (SELECT RemoteId
            FROM SyncFiles
            WHERE (LocalFiles.OriginalFileName == SyncFiles.OrigFileName or
                   LocalFiles.FileName == SyncFiles.FileName)
            AND SyncFiles.RemoteId NOT IN (select RemoteId from pre_match)
)
WHERE LocalFiles.RemoteId isnull
;
"""]

missing_files = """select * from LocalFiles where RemoteId isnull;"""

extra_files = """
select *
from Syncfiles
where RemoteId
        in (SELECT S.RemoteId
           FROM SyncFiles S
                  LEFT JOIN LocalFiles L ON S.RemoteId = L.RemoteId
           WHERE L.RemoteId ISNULL)
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
