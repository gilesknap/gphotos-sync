"""
This file checks that all the example boilerplate text has been removed.
It can be deleted when all the contained tests pass
"""
import sys
from pathlib import Path

if sys.version_info < (3, 8):
    from importlib_metadata import metadata  # noqa
else:
    from importlib.metadata import metadata  # noqa

ROOT = Path(__file__).parent.parent


def skeleton_check(check: bool, text: str):
    if ROOT.name == "python3-pip-skeleton" or str(ROOT) == "/project":
        # In the skeleton module the check should fail
        check = not check
        text = f"Skeleton didn't raise: {text}"
    if check:
        raise AssertionError(text)


def assert_not_contains_text(path: str, text: str, explanation: str):
    full_path = ROOT / path
    if full_path.exists():
        contents = full_path.read_text().replace("\n", " ")
        skeleton_check(text in contents, f"Please change ./{path} {explanation}")


# pyproject.toml
def test_module_summary():
    summary = metadata("gphotos-sync")["summary"]
    skeleton_check(
        "One line description of your module" in summary,
        "Please change project.description in ./pyproject.toml "
        "to be a one line description of your module",
    )


# README
def test_changed_README_intro():
    assert_not_contains_text(
        "README.rst",
        "This is where you should write a short paragraph",
        "to include an intro on what your module does",
    )


def test_removed_adopt_skeleton():
    assert_not_contains_text(
        "README.rst",
        "This project contains template code only",
        "remove the note at the start",
    )


def test_changed_README_body():
    assert_not_contains_text(
        "README.rst",
        "This is where you should put some images or code snippets",
        "to include some features and why people should use it",
    )
