from datetime import datetime
from pathlib import Path
from attr import dataclass

"""
Defines a dataclass for passing all configuration information between
the worker classes
"""


@dataclass
class Settings:
    start_date: datetime
    end_date: datetime
    use_start_date: bool

    photos_path: Path
    use_flat_path: bool

    albums_path: Path
    album_index: bool
    omit_album_date: bool
    album: str
    shared_albums: bool

    favourites_only: bool
    include_video: bool
    archived: bool
    use_hardlinks: bool

    retry_download: bool
    rescan: bool
    max_retries: int
    max_threads: int
    case_insensitive_fs: bool
    progress: bool
