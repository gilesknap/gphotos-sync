drop table if exists Albums;
drop table if exists DriveFiles;
drop table if exists AlbumFiles;
drop table if exists Globals;

create table Albums
(
	Id INTEGER
		primary key,
	AlbumId TEXT,
	AlbumName TEXT,
	StartDate TEXT not null,
	EndDate TEXT not null
)
;

create table DriveFiles
(
	Id INTEGER
		primary key,
	DriveId TEXT,
	OrigFileName TEXT,
	Path TEXT,
	FileName TEXT,
	DuplicateNo INT,
	ExifDate TEXT,
	Checksum TEXT,
	Description TEXT,
	FileSize INT,
	CreateDate TEXT,
	SyncDate TEXT,
  PicassaOnly INT DEFAULT 0
)
;

create table AlbumFiles
(
	Id INTEGER
		primary key,
	AlbumRec INT,
	DriveRec INT,
	foreign key (AlbumRec) references Albums (Id)
			on delete cascade,
	foreign key (DriveRec) references DriveFiles (Id)
			on update cascade on delete cascade)
;

create table Globals
(
	Version TEXT,
	Albums INT,
	Files INT,
	LastScanDate TEXT
)
;

DROP INDEX IF EXISTS DriveFiles_DriveId_uindex;
DROP INDEX IF EXISTS FileNameIdx;
DROP INDEX IF EXISTS FileSizeIdx;
DROP INDEX IF EXISTS FileSizeAndSizeIdx;
DROP INDEX IF EXISTS CreatedIdx;
DROP INDEX IF EXISTS ExifDateIdx;
DROP INDEX IF EXISTS Albums_AlbumId_uindex;
DROP INDEX IF EXISTS Albums_StartDate_index;
DROP INDEX IF EXISTS Albums_AlbumName_index;
DROP INDEX IF EXISTS AlbumFiles_AlbumRec_DriveRec_uindex;

create unique index DriveFiles_DriveId_uindex
	on DriveFiles (DriveId);

create index FileNameIdx
  on DriveFiles (FileName);

create index FileSizeIdx
  on DriveFiles (FileSize);

create index FileSizeAndSizeIdx
  on DriveFiles (FileName, FileSize);

create index CreatedIdx
  on DriveFiles (CreateDate);

create index ExifDateIdx
  on DriveFiles (ExifDate);

CREATE UNIQUE INDEX Albums_AlbumId_uindex ON Albums (AlbumId);
CREATE INDEX Albums_StartDate_index ON Albums (StartDate);
CREATE INDEX Albums_AlbumName_index ON Albums (AlbumName);
create unique index AlbumFiles_AlbumRec_DriveRec_uindex
	on AlbumFiles (AlbumRec, DriveRec)
;

