from datetime import datetime
from pathlib import Path
from typing import Optional

from .Checks import get_check


class BaseMedia(object):
    """Base class for media model classes.
    These provide a standard interface for media items that have been loaded
    from disk / loaded from DB / retrieved from the Google Photos Library
    """

    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, root_path: Path = Path(""), **k_args):
        self._id: str = ""
        self._relative_folder: Path = Path("")
        self._root_path: Path = root_path
        self._duplicate_number: int = 0

    # Allow boolean check to fail on empty BaseMedia
    def __bool__(self) -> bool:
        return self._id is not None

    def set_path_by_date(self, root: Path, use_flat_path: bool = False):
        y = "{:04d}".format(self.create_date.year)
        m = "{:02d}".format(self.create_date.month)
        if use_flat_path:
            self._relative_folder = root / (y + "-" + m)
        else:
            self._relative_folder = root / y / m

    @property
    def is_video(self) -> bool:
        # guard against no mimetype issue #231
        if not self.mime_type:
            return False
        return self.mime_type.startswith("video")

    @property
    def duplicate_number(self) -> int:
        return self._duplicate_number

    @duplicate_number.setter
    def duplicate_number(self, value: int):
        self._duplicate_number = value

    # Relative path to the media file from the root of the sync folder
    # e.g. 'Google Photos/2017/09'.
    @property
    def relative_path(self) -> Path:
        return self._relative_folder / self.filename

    # as above but without the filename appended
    @property
    def relative_folder(self) -> Path:
        return self._relative_folder

    @property
    def full_folder(self) -> Path:
        return self._root_path / self._relative_folder

    @property
    def filename(self) -> str:
        if self.duplicate_number > 0:
            file_str = "%(base)s (%(duplicate)d)%(ext)s" % {
                "base": Path(self.orig_name).stem,
                "ext": Path(self.orig_name).suffix,
                "duplicate": self.duplicate_number + 1,
            }
            filename = get_check().valid_file_name(file_str)
        else:
            filename = self.orig_name
        return filename

    # ----- Properties for override below -----
    @property
    def size(self) -> int:
        raise NotImplementedError

    @property
    def id(self) -> Optional[str]:
        raise NotImplementedError

    @property
    def description(self) -> str:
        raise NotImplementedError

    @property
    def orig_name(self) -> str:
        raise NotImplementedError

    @property
    def create_date(self) -> datetime:
        raise NotImplementedError

    @property
    def modify_date(self) -> datetime:
        raise NotImplementedError

    @property
    def mime_type(self) -> Optional[str]:
        raise NotImplementedError

    @property
    def url(self) -> Optional[str]:
        raise NotImplementedError
