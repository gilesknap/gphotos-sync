import logging
from datetime import datetime
from pathlib import Path

from gphotos_sync.BaseMedia import BaseMedia
from gphotos_sync.DatabaseMedia import DatabaseMedia
from gphotos_sync.DbRow import DbRow
from gphotos_sync.LocalFilesMedia import LocalFilesMedia

log = logging.getLogger(__name__)


@DbRow.db_row
class LocalFilesRow(DbRow):
    """
    generates a class with attributes for each of the columns in the
    LocalFiles table
    """

    table = "LocalFiles"
    cols_def = {
        "Id": int,
        "RemoteId": str,
        "Uid": str,
        "Path": str,
        "FileName": str,
        "OriginalFileName": str,
        "DuplicateNo": int,
        "MimeType": str,
        "Description": str,
        "FileSize": int,
        "ModifyDate": datetime,
        "CreateDate": datetime,
        "SyncDate": datetime,
    }
    no_update = ["Id"]

    # All properties on this class are dynamically added from the above
    # list using DbRow.make. Hence Mypy cannot see them and they need
    # type: ignore
    def to_media(self) -> DatabaseMedia:
        pth = Path(self.Path) if self.Path else None  # type: ignore
        db_media = DatabaseMedia(
            _id=self.RemoteId,  # type: ignore
            _relative_folder=pth,  # type: ignore
            _filename=self.FileName,  # type: ignore
            _orig_name=self.OriginalFileName,  # type: ignore
            _duplicate_number=self.DuplicateNo,  # type: ignore
            _size=self.FileSize,  # type: ignore
            _mime_type=self.MimeType,  # type: ignore
            _description=self.Description,  # type: ignore
            _date=self.ModifyDate,  # type: ignore
            _create_date=self.CreateDate,  # type: ignore
        )
        return db_media

    @classmethod
    def from_media(cls, media: LocalFilesMedia) -> "LocalFilesRow":  # type: ignore
        now_time = datetime.now().strftime(BaseMedia.TIME_FORMAT)
        new_row = cls.make(
            Path=str(media.relative_folder),
            Uid=media.uid,
            FileName=media.filename,
            OriginalFileName=media.orig_name,
            DuplicateNo=media.duplicate_number,
            FileSize=media.size,
            MimeType=media.mime_type,
            Description=media.description,
            ModifyDate=media.modify_date,
            CreateDate=media.create_date,
            SyncDate=now_time,
        )
        return new_row
