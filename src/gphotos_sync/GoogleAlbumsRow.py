import logging
from datetime import datetime

from gphotos_sync import Utils
from gphotos_sync.DatabaseMedia import DatabaseMedia
from gphotos_sync.DbRow import DbRow
from gphotos_sync.GoogleAlbumMedia import GoogleAlbumMedia

log = logging.getLogger(__name__)


@DbRow.db_row
# pylint: disable=no-member
class GoogleAlbumsRow(DbRow):
    """
    generates a class with attributes for each of the columns in the
    SyncFiles table
    """

    table = "Albums"
    cols_def = {
        "RemoteId": str,
        "AlbumName": str,
        "Size": int,
        "StartDate": datetime,
        "EndDate": datetime,
        "SyncDate": datetime,
        "Downloaded": bool,
    }

    # All properties on this class are dynamically added from the above
    # list using DbRow.make. Hence Mypy cannot see them and they need
    # type: ignore
    def to_media(self) -> DatabaseMedia:  # type:ignore
        db_media = DatabaseMedia(
            _id=self.RemoteId,  # type:ignore
            _filename=self.AlbumName,  # type:ignore
            _size=self.Size,  # type:ignore
            _create_date=self.EndDate,  # type:ignore
        )
        return db_media

    @classmethod
    def from_media(cls, album) -> GoogleAlbumMedia:  # type:ignore
        pass

    @classmethod
    def from_parm(cls, album_id, filename, size, start, end) -> "GoogleAlbumsRow":
        new_row = cls.make(
            RemoteId=album_id,
            AlbumName=filename,
            Size=size,
            StartDate=start,
            EndDate=end,
            SyncDate=Utils.date_to_string(datetime.now()),
            Downloaded=0,
        )
        return new_row
