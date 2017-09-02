drop table if exists DriveFolders;
create table DriveFolders
(
	Id INTEGER
		primary key,
	FolderId TEXT,
	ParentId TEXT,
	Path TEXT,
	FolderName TEXT,
	ModifiedDate INT
)
;
create unique index DriveFolders_FolderId_uindex on DriveFolders (FolderId);
create index DriveFolders_ParentId_index on DriveFolders (ParentId);


drop table if exists Albums;
create table Albums
(
	AlbumId TEXT
		primary key,
	AlbumName TEXT,
	StartDate TEXT not null,
	EndDate TEXT not null
)
;
DROP INDEX IF EXISTS Albums_AlbumId_uindex;
DROP INDEX IF EXISTS Albums_StartDate_index;
DROP INDEX IF EXISTS Albums_AlbumName_index;

create unique index Albums_AlbumId_uindex
	on Albums (AlbumId)
;
create index Albums_AlbumName_index
	on Albums (AlbumName)
;
create index Albums_StartDate_index
	on Albums (StartDate)
;


drop table if exists SyncFiles;
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
DROP INDEX IF EXISTS RemoteIdIdx;
DROP INDEX IF EXISTS FileNameIdx;
DROP INDEX IF EXISTS FileSizeIdx;
DROP INDEX IF EXISTS FileSizeAndSizeIdx;
DROP INDEX IF EXISTS CreatedIdx;
DROP INDEX IF EXISTS ModifyDateIdx;
DROP INDEX IF EXISTS SyncFiles_Path_FileName_DuplicateNo_uindex;
create unique index RemoteIdIdx	on SyncFiles (RemoteId);
create index FileNameIdx  on SyncFiles (FileName);
create index FileSizeIdx  on SyncFiles (FileSize);
create index FileSizeAndSizeIdx  on SyncFiles (FileName, FileSize);
create index CreatedIdx  on SyncFiles (CreateDate);
create index ModifyDateIdx  on SyncFiles (ModifyDate);
create unique index SyncFiles_Path_FileName_DuplicateNo_uindex
	on SyncFiles (Path, FileName, DuplicateNo);


drop table if exists AlbumFiles;
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
DROP INDEX IF EXISTS AlbumFiles_AlbumRec_DriveRec_uindex;
create unique index AlbumFiles_AlbumRec_DriveRec_uindex
	on AlbumFiles (AlbumRec, DriveRec);

drop table if exists Globals;
create table Globals
(
	Version TEXT,
	Albums INT,
	Files INT,
	LastScanDate TEXT
)
;

