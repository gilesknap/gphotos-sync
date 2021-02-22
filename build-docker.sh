#!/bin/bash
set -x

command -v docker >/dev/null 2>&1 || { echo >&2 "Docker CLI is required."; exit 1; }
[[ -z "${DOCKER_USERNAME}" ]] && { echo >&2 "DOCKER_USERNAME is not set."; exit 1; }
[[ -z "${DOCKER_PASSWORD}" ]] && { echo >&2 "DOCKER_PASSWORD is not set."; exit 1; }

# install latest docker-ce with buildx for multiarch build
# https://www.docker.com/blog/multi-arch-build-what-about-travis/
sudo rm -rf /var/lib/apt/lists/*
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) edge"
sudo apt-get update
sudo apt-get -y -o Dpkg::Options::="--force-confnew" install docker-ce
mkdir -vp ~/.docker/cli-plugins/
curl --silent -L "https://github.com/docker/buildx/releases/download/v0.3.0/buildx-v0.3.0.linux-amd64" > ~/.docker/cli-plugins/docker-buildx
chmod a+x ~/.docker/cli-plugins/docker-buildx

docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}
docker buildx create --use

docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t gilesknap/gphotos-sync:latest \
    -t gilesknap/gphotos-sync:${TRAVIS_TAG} \
    --push \
    .
