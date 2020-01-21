#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${DIR}
pipenv run ./gphotos-sync /tmp/test-gphotos --secret /home/giles/github//gphotos-sync/test/test_credentials/client_secret.json --log-level trace