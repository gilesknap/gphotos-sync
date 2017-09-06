from unittest import TestCase
from test_setup import SetupDbAndCredentials
from datetime import datetime


class Utils(TestCase):
    # long running test which genuinely tests the token refresh
    @classmethod
    def test_patch_http_client(cls):
        s = SetupDbAndCredentials()
        s.test_setup()
        start_time = datetime.now()

        # index will raise if the token refresh fails
        while True:
            s.gp.picasa_sync.index_album_media()
            elapsed = datetime.now() - start_time
            if elapsed.seconds > 3700:
                break


