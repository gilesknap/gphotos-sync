import subprocess
import sys

from gphotos_sync import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "gphotos_sync", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
