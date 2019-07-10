
Gphotos sync and Python 3.6
---------------------------
Pipenv has a hard Python version requirement so to support Python 3.6 use a
virtual environment:

- git clone git@github.com:gilesknap/gphotos-sync.git
- cd gphotos-sync
- virtualenv venv36
- . venv36/bin/activate
- pip3 install .
- gphotos-sync --help

This will most likely work for earlier Python versions as long as you edit the
Python dependency in setup.py. Only Python 3.6 has been tested.