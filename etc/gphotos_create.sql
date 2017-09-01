drop table if exists DriveFolders;
drop table if exists Albums;
drop table if exists SyncFiles;
drop table if exists AlbumFiles;
drop table if exists Globals;

create table "DriveFolders"
(
	"Id" INTEGER
		primary key,
	"FolderId" TEXT,
	"ParentId" TEXT,
	"Path" TEXT,
	"FolderName" TEXT,
	"ModifiedDate" INT
)
;


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

create table SyncFiles
(
	Id INTEGER
		primary key,
	RemoteId TEXT,
	Url TEXT,
	Path TEXT,
	FileName TEXT,
	DuplicateNo INT,
	Checksum TEXT,
	Description TEXT,
	FileSize INT,
	ModifyDate INT,
	CreateDate INT,
	SyncDate INT,
  MediaType INT DEFAULT 0,
  SymLink INT DEFAULT 0
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
	foreign key (DriveRec) references SyncFiles (Id)
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

DROP INDEX IF EXISTS RemoteIdIdx;
DROP INDEX IF EXISTS FileNameIdx;
DROP INDEX IF EXISTS FileSizeIdx;
DROP INDEX IF EXISTS FileSizeAndSizeIdx;
DROP INDEX IF EXISTS CreatedIdx;
DROP INDEX IF EXISTS ModifyDateIdx;
DROP INDEX IF EXISTS Albums_AlbumId_uindex;
DROP INDEX IF EXISTS Albums_StartDate_index;
DROP INDEX IF EXISTS Albums_AlbumName_index;
DROP INDEX IF EXISTS AlbumFiles_AlbumRec_DriveRec_uindex;

create unique index RemoteIdIdx	on SyncFiles (RemoteId);
create index FileNameIdx  on SyncFiles (FileName);
create index FileSizeIdx  on SyncFiles (FileSize);
create index FileSizeAndSizeIdx  on SyncFiles (FileName, FileSize);
create index CreatedIdx  on SyncFiles (CreateDate);
create index ModifyDateIdx  on SyncFiles (ModifyDate);
CREATE UNIQUE INDEX Albums_AlbumId_uindex ON Albums (AlbumId);
CREATE INDEX Albums_StartDate_index ON Albums (StartDate);
CREATE INDEX Albums_AlbumName_index ON Albums (AlbumName);
create unique index AlbumFiles_AlbumRec_DriveRec_uindex
	on AlbumFiles (AlbumRec, DriveRec)
;

