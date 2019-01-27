from yaml import load, dump, YAMLError
import os
import logging

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

log = logging.getLogger(__name__)

''' keeps a list of media items with ID in a YAML file. The YAML file
allows a user to easily investigate their list of media items that have
failed to download '''


class BadIds:
    def __init__(self, root_folder):
        self.items = []
        self.ids = []
        self.bad_ids_filename = os.path.join(
            root_folder, "gphotos.bad_ids.yaml")
        self.load_ids()
        self.bad_ids_found = 0

    def load_ids(self):
        try:
            with open(self.bad_ids_filename, 'r') as stream:
                self.items = load(stream, Loader=Loader)
                self.ids = list((item.get('gid') for item in self.items))
        except (YAMLError, IOError):
            log.debug("no bad_ids file, bad ids list is empty")

    def store_ids(self):
        with open(self.bad_ids_filename, 'w') as stream:
            dump(self.items, stream, Dumper=Dumper, default_flow_style=False)

    def add_id(self, path, gid, product_url, e):
        item = {
            'path': path,
            'gid': gid,
            'product_url': product_url
        }
        self.ids.append(gid)
        self.items.append(item)
        log.debug('BAD ID %s for %s', gid, path, exc_info=e)

    def check_id_ok(self, gid):
        if gid in self.ids:
            self.bad_ids_found += 1
            return False
        else:
            return True

    def report(self):
        if self.bad_ids_found > 0:
            log.error("WARNING: skipped %d files listed in %s",
                      self.bad_ids_found, self.bad_ids_filename)
