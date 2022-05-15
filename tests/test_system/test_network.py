import warnings
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from requests import Session
from requests.exceptions import HTTPError

import tests.test_setup as ts
from gphotos_sync.LocalData import LocalData
from tests.test_account import TestAccount

photos_root = Path("photos")
original_get = Session.get
call_count = 0


def patched_get(self, url, stream=True, timeout=20):
    global call_count
    call_count += 1
    # succeed occasionally only
    succeed = call_count % 10 == 0
    if "discovery" in url or succeed:
        return original_get(self, url, stream=stream, timeout=timeout)
    else:
        raise HTTPError(Mock(status=500), "ouch!")


class TestNetwork(TestCase):
    @patch.object(Session, "get", patched_get)
    def test_max_retries_hit(self):
        warnings.filterwarnings(
            action="ignore", message="unclosed", category=ResourceWarning
        )

        with ts.SetupDbAndCredentials() as s:
            args = ["--skip-albums"]
            s.test_setup(
                "test_max_retries_hit", args=args, trash_files=True, trash_db=True
            )
            s.gp.start(s.parsed_args)

            db = LocalData(s.root)

            db.cur.execute("SELECT COUNT() FROM SyncFiles")
            count = db.cur.fetchone()
            self.assertEqual(TestAccount.total_count, count[0])

            pat = str(photos_root / "*" / "*" / "*")
            self.assertEqual(
                9, len(sorted(s.root.glob(pat))), "mismatch on image file count"
            )
