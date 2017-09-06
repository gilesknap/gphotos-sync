from Main import GooglePhotosSyncMain
import sys
from mock import patch


class SetupDbAndCredentials:
    def __init__(self):
        self.gp = GooglePhotosSyncMain()

    def create_args(self, *args, **k_args):
        return

    def test_setup(self):
        test_args = ["/tmp/gp_test", "--flush_index"]
        with patch.object(sys, 'argv', test_args):
            args = self.gp.parser.parse_args()
        self.gp.setup(args)

    def test_done(self):
        self.gp.data_store.store()
