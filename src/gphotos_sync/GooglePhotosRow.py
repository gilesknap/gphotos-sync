import logging
from datetime import datetime
from pathlib import Path

from gphotos_sync.BaseMedia import BaseMedia
from gphotos_sync.DatabaseMedia import DatabaseMedia
from gphotos_sync.DbRow import DbRow
from gphotos_sync.GooglePhotosMedia import GooglePhotosMedia

log = logging.getLogger(__name__)


@DbRow.db_row
# pylint: disable=no-member
class GooglePhotosRow(DbRow):
    """
    generates a class with attributes for each of the columns in the
    SyncFiles table
    """

    table = "SyncFiles"
    cols_def = {
        "Id": int,
        "RemoteId": str,
        "Uid": str,
        "Url": str,
        "Path": str,
        "FileName": str,
        "OrigFileName": str,
        "DuplicateNo": int,
        "FileSize": int,
        "MimeType": str,
        "Description": str,
        "ModifyDate": datetime,
        "CreateDate": datetime,
        "SyncDate": datetime,
        "Downloaded": int,
        "Location": str,
    }
    no_update = ["Id"]

    # All properties on this class are dynamically added from the above
    # list using DbRow.make. Hence Mypy cannot see them and they need
    # type: ignore
    def to_media(self) -> DatabaseMedia:
        pth = Path(self.Path) if self.Path else None  # type: ignore
        db_media = DatabaseMedia(
            _id=self.RemoteId,  # type: ignore
            _url=self.Url,  # type: ignore
            _uid=self.Uid,  # type: ignore
            _relative_folder=pth,  # type: ignore
            _filename=self.FileName,  # type: ignore
            _orig_name=self.OrigFileName,  # type: ignore
            _duplicate_number=self.DuplicateNo,  # type: ignore
            _size=self.FileSize,  # type: ignore
            _mime_type=self.MimeType,  # type: ignore
            _description=self.Description,  # type: ignore
            _date=self.ModifyDate,  # type: ignore
            _create_date=self.CreateDate,  # type: ignore
            _downloaded=self.Downloaded,  # type: ignore
            _location=self.Location,  # type: ignore
        )
        return db_media

    @classmethod
    def from_media(  # type: ignore
        cls,
        media: GooglePhotosMedia,
    ) -> "GooglePhotosRow":
        now_time = datetime.now().strftime(BaseMedia.TIME_FORMAT)
        new_row = cls.make(
            RemoteId=media.id,
            Url=media.url,
            Uid=media.uid,
            Path=str(media.relative_folder),
            FileName=str(media.filename),
            OrigFileName=str(media.orig_name),
            DuplicateNo=media.duplicate_number,
            FileSize=media.size,
            MimeType=media.mime_type,
            Description=media.description,
            ModifyDate=media.modify_date,
            CreateDate=media.create_date,
            SyncDate=now_time,
            Downloaded=0,
            Location="",
        )
        return new_row
