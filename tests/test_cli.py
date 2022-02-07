import subprocess
import sys

from python3_pip_skeleton import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "python3_pip_skeleton", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
