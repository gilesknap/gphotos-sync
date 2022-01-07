import subprocess
import sys

from dls_python3_skeleton import __main__, __version__, hello


def test_hello_class_formats_greeting() -> None:
    inst = hello.HelloClass("person")
    assert inst.format_greeting() == "Hello person"


def test_hello_lots_defaults(capsys) -> None:
    hello.say_hello_lots()
    captured = capsys.readouterr()
    assert captured.out == "Hello me\n" * 5
    assert captured.err == ""


def test_cli_greets(capsys) -> None:
    __main__.main(["person", "--times=2"])
    captured = capsys.readouterr()
    assert captured.out == "Hello person\n" * 2
    assert captured.err == ""


def test_cli_version():
    cmd = [sys.executable, "-m", "dls_python3_skeleton", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
