#!/bin/bash

command -v docker >/dev/null 2>&1 || { echo >&2 "Docker CLI is required."; exit 1; }
[[ -z "${DOCKER_USERNAME}" ]] || { echo >&2 "DOCKER_USERNAME is not set."; exit 1; }
[[ -z "${DOCKER_PASSWORD}" ]] || { echo >&2 "DOCKER_PASSWORD is not set."; exit 1; }

docker build . \
    -t gilesknap/gphotos-sync:latest \
    -f ./Dockerfile

docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD
docker push gilesknap/gphotos-sync