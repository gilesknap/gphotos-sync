#!/bin/bash
set -x

cd /project
source /venv/bin/activate

touch requirements_dev.txt
pip install -r requirements_dev.txt -e .[dev]
mkdir -p lockfiles
pip freeze --exclude-editable > lockfiles/requirements_dev.txt

pipdeptree

pytest tests
