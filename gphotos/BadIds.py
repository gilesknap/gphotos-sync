from yaml import load, dump, YAMLError, emitter
from typing import NamedTuple, Dict
import os
import logging

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

log = logging.getLogger(__name__)


class Item(NamedTuple):
    path: str
    product_url: str


class BadIds:
    """ keeps a list of media items with ID in a YAML file. The YAML file
    allows a user to easily investigate their list of media items that have
    failed to download

    Attributes:
        items: Dict[str, Item] bad ids found with identifying attributes
        bad_ids_filename: str: file where ids are stored/read
        bad_ids_found: count of Ids found since instantiation
    """

    def __init__(self, root_folder: str):
        self.items: Dict[str, Item] = {}
        self.bad_ids_filename: str = \
            os.path.join(root_folder, "gphotos.bad_ids.yaml")
        self.bad_ids_found: int = 0
        self.load_ids()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.store_ids()

    def load_ids(self):
        try:
            with open(self.bad_ids_filename, 'r') as stream:
                self.items = load(stream, Loader=Loader)
            log.debug("bad_ids file, loaded %d bad ids", len(self.items))
        except (YAMLError, IOError):
            log.debug("no bad_ids file, bad ids list is empty")

    def store_ids(self):
        with open(self.bad_ids_filename, 'w') as stream:
            dump(self.items, stream, Dumper=Dumper, default_flow_style=False)

    def add_id(self, path: str, gid: str, product_url: str, e: Exception):
        item = Item(
            path=path,
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
