from pathlib import Path
from unittest import TestCase

from gphotos_sync.Checks import do_check
from gphotos_sync.LocalFilesMedia import LocalFilesMedia

test_data = Path(__file__).absolute().parent.parent / "test-data"


class TestLocalScan(TestCase):
    def test_local_duplicate_names(self):
        ps = "PIC00002 (2).jpg"
        p = Path(test_data) / Path(ps)

        # ugly global stuff to make LocalFilesMedia work
        do_check(test_data)

        lf = LocalFilesMedia(p)
        self.assertEqual(lf.duplicate_number, 1)

        assert str(lf.filename) == ps

        ps = "PIC00002.jpg"
        p = Path(test_data) / Path(ps)

        lf = LocalFilesMedia(p)
        self.assertEqual(lf.duplicate_number, 0)

        assert str(lf.filename) == ps
