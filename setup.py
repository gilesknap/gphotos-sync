#!/usr/bin/env python3

import sys
from setuptools import setup, find_packages, os

# Place the directory containing _version_git on the path
for path, _, filenames in os.walk(os.path.dirname(os.path.abspath(__file__))):
    if "_version_git.py" in filenames:
        sys.path.append(path)
        break

from _version_git import get_cmdclass, __version__  # noqa E402

print(f"installing version {__version__}")

module_name = "gphotos-sync"

install_reqs = [
    "attrs",
    "exif",
    "appdirs",
    "requests_oauthlib",
    "pyyaml>=4.2b1",
    "psutil",
]

develop_reqs = [
    "pytest>=5.0.1",
    "mock",
    "coverage",
    "pytest",
    "flake8",
    "black",
    "rope",
]

if os.name == "nt":
    install_reqs.append("pywin32")

with open("README.rst", "rb") as f:
    long_description = f.read().decode("utf-8")

packages = [x for x in find_packages() if x.startswith("gphotos")]

setup(
    name=module_name,
    cmdclass=get_cmdclass(),
    version=__version__,
    python_requires=">=3.6",
    license="MIT",
    platforms=["Linux", "Windows", "Mac"],
    description="Google Photos and Albums backup tool",
    packages=packages,
    entry_points={"console_scripts": ["gphotos-sync = gphotos.Main:main"]},
    long_description=long_description,
    install_requires=install_reqs,
    extras_require={"dev": develop_reqs},
    package_data={"": ["gphotos/sql/gphotos_create.sql", "LICENSE"]},
    include_package_data=True,
    author="Giles Knap",
    author_email="gilesknap@gmail.com",
    url="https://github.com/gilesknap/gphotos-sync",
)
