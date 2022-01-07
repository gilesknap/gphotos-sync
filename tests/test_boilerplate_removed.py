"""
This file checks that all the example boilerplate text has been removed.
It can be deleted when all the contained tests pass
"""
import configparser
from pathlib import Path

ROOT = Path(__file__).parent.parent


def skeleton_check(check: bool, text: str):
    if ROOT.name == "dls-python3-skeleton":
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


def assert_not_exists(path: str, explanation: str):
    exists = (ROOT / path).exists()
    skeleton_check(exists, f"Please delete ./{path} {explanation}")


# setup.cfg
def test_module_description():
    conf = configparser.ConfigParser()
    conf.read("setup.cfg")
    description = conf["metadata"]["description"]
    skeleton_check(
        "One line description of your module" in description,
        "Please change description in ./setup.cfg "
        "to be a one line description of your module",
    )


# README
def test_changed_README_intro():
    assert_not_contains_text(
        "README.rst",
        "This is where you should write a short paragraph",
        "to include an intro on what your module does",
    )


def test_changed_README_body():
    assert_not_contains_text(
        "README.rst",
        "This is where you should put some images or code snippets",
        "to include some features and why people should use it",
    )


# Docs
def test_docs_ref_api_changed():
    assert_not_contains_text(
        "docs/reference/api.rst",
        "You can mix verbose text with docstring and signature",
        "to introduce the API for your module",
    )


def test_how_tos_written():
    assert_not_exists(
        "docs/how-to/accomplish-a-task.rst", "and write some docs/how-tos"
    )


def test_explanations_written():
    assert_not_exists(
        "docs/explanations/why-is-something-so.rst", "and write some docs/explanations"
    )
