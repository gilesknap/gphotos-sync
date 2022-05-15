drop table if exists Albums;
create table Albums
(
	RemoteId TEXT
		primary key,
	AlbumName TEXT,
	Size INT,
	Description TEXT,
	StartDate INT,
	EndDate INT,
	SyncDate INT,
  Downloaded INT DEFAULT 0
)
;
DROP INDEX IF EXISTS Albums_RemoteId_uindex;
DROP INDEX IF EXISTS Albums_StartDate_index;
DROP INDEX IF EXISTS Albums_AlbumName_index;

create unique index Albums_RemoteId_uindex
	on Albums (RemoteId)
;
create index Albums_AlbumName_index
	on Albums (AlbumName)
;
create index Albums_StartDate_index
	on Albums (StartDate)
;


drop table if exists LocalFiles;
create table LocalFiles
(
	Id INTEGER
		primary key,
	RemoteId TEXT default '',
	Uid Text,
	Path TEXT,
	FileName TEXT,
	OriginalFileName TEXT,
	DuplicateNo INT,
	MimeType TEXT,
	Description TEXT,
	FileSize INT,
	ModifyDate INT,
	CreateDate INT,
	SyncDate INT
);

DROP INDEX IF EXISTS LocalRemoteIdIdx;
DROP INDEX IF EXISTS LocalUidIdx;
DROP INDEX IF EXISTS LocalNameIdx;
DROP INDEX IF EXISTS LocalCreatedIdx;
DROP INDEX IF EXISTS LocalMatchIdx;
DROP INDEX IF EXISTS LocalFiles_Path_FileName_DuplicateNo_uindex;
create index LocalRemoteIdIdx	on LocalFiles (RemoteId);
create index LocalUidIdx	on LocalFiles (Uid);
create index LocalNameIdx  on LocalFiles (FileName);
create index LocalCreatedIdx  on LocalFiles (CreateDate);
create index LocalMatchIdx  on LocalFiles (OriginalFileName, DuplicateNo, Description);
create unique index LocalFiles_Path_FileName_DuplicateNo_uindex
 	on LocalFiles (Path, FileName, DuplicateNo);

drop table if exists SyncFiles;
create table SyncFiles
(
	Id INTEGER
		primary key,
	RemoteId TEXT,
	Uid Text,
	Url TEXT,
	Path TEXT,
	FileName TEXT,
	OrigFileName TEXT,
	DuplicateNo INT,
	MimeType TEXT,
	Description TEXT,
	FileSize INT,
	ModifyDate INT,
	CreateDate INT,
	SyncDate INT,
  Downloaded INT DEFAULT 0,
  Location Text
);

DROP INDEX IF EXISTS RemoteIdIdx;
DROP INDEX IF EXISTS UidIdx;
DROP INDEX IF EXISTS FileNameIdx;
DROP INDEX IF EXISTS FileSizeIdx;
DROP INDEX IF EXISTS FileSizeAndSizeIdx;
DROP INDEX IF EXISTS CreatedIdx;
DROP INDEX IF EXISTS ModifyDateIdx;
DROP INDEX IF EXISTS SyncMatchIdx;
DROP INDEX IF EXISTS SyncFiles_Path_FileName_DuplicateNo_uindex;
create unique index RemoteIdIdx	on SyncFiles (RemoteId);
create index FileNameIdx  on SyncFiles (FileName);
create index UidIdx  on SyncFiles (Uid);
create index FileSizeIdx  on SyncFiles (FileSize);
create index FileSizeAndSizeIdx  on SyncFiles (FileName, FileSize);
create index CreatedIdx  on SyncFiles (CreateDate);
create index ModifyDateIdx  on SyncFiles (ModifyDate);
create index SyncMatchIdx  on SyncFiles (OrigFileName, DuplicateNo, Description);
create unique index SyncFiles_Path_FileName_DuplicateNo_uindex
 	on SyncFiles (Path, FileName, DuplicateNo);


drop table if exists AlbumFiles;
create table AlbumFiles
(
	Id INTEGER
		primary key,
	AlbumRec INT,
	DriveRec INT,
	Position INT,
	foreign key (AlbumRec) references Albums (RemoteId)
			on delete cascade,
	foreign key (DriveRec) references SyncFiles (Id)
			on update cascade on delete cascade)
;
DROP INDEX IF EXISTS AlbumFiles_AlbumRec_DriveRec_uindex;
create unique index AlbumFiles_AlbumRec_DriveRec_uindex
	on AlbumFiles (AlbumRec, DriveRec);

drop table if exists Globals;
CREATE TABLE Globals
(
  Id INTEGER,
  Version TEXT,
  Albums INTEGER,
  Files INTEGER,
  LastIndex INT -- Date of last sync
);
CREATE UNIQUE INDEX Globals_Id_uindex ON Globals (Id);


