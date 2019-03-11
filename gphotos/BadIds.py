from pathlib import Path
from yaml import safe_load, safe_dump, YAMLError
from typing import Dict
import logging

log = logging.getLogger(__name__)


class BadIds:
    """ keeps a list of media items with ID in a YAML file. The YAML file
    allows a user to easily investigate their list of media items that have
    failed to download

    Attributes:
        items: Dict[str, Item] bad ids found with identifying attributes
        bad_ids_filename: str: file where ids are stored/read
        bad_ids_found: count of Ids found since instantiation
    """

    def __init__(self, root_folder: Path):
        self.items: Dict[str, dict] = {}
        self.bad_ids_filename: Path = \
            root_folder / "gphotos.bad_ids.yaml"
        self.bad_ids_found: int = 0
        self.load_ids()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.store_ids()

    def load_ids(self):
        try:
            with self.bad_ids_filename.open('r') as stream:
                self.items = safe_load(stream)
            log.debug("bad_ids file, loaded %d bad ids", len(self.items))
        except (YAMLError, IOError):
            log.debug("no bad_ids file, bad ids list is empty")

    def store_ids(self):
        with self.bad_ids_filename.open('w') as stream:
            safe_dump(self.items, stream, default_flow_style=False)

    def add_id(self, path: str, gid: str, product_url: str, e: Exception):
        item = dict(
            path=str(path),
            product_url=product_url
        )
        self.items[gid] = item
        log.debug('BAD ID %s for %s', gid, path, exc_info=e)

    def check_id_ok(self, gid: str):
        if gid in self.items:
            self.bad_ids_found += 1
            return False
        else:
            return True

    def report(self):
        if self.bad_ids_found > 0:
            log.error("WARNING: skipped %d files listed in %s",
                      self.bad_ids_found, self.bad_ids_filename)
