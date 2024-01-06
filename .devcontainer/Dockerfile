# ideas from https://www.docker.com/blog/containerized-python-development-part-1/

# This file is for use as a .vscode devcontainer as well as a runtime
# container. The devcontainer should be rootful and use podman or docker
# with user namespaces.

ARG BASE="mcr.microsoft.com/devcontainers/python:dev-3.12-bullseye"
FROM ${BASE} as base

# use root to pin where the packages will install
USER root
ENV PATH=/root/.local/bin:$PATH

FROM base as developer

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY . .

# install runtime from DIST if there is one
RUN mkdir -vp /root/.local && \
    if [ -d dist ] ; then \
    touch requirements.txt && \
    pip install --no-cache --user -r requirements.txt dist/*.whl ; \
    fi

FROM base as runtime

COPY --from=developer /root/.local /root/.local

RUN mkdir -vp /root/.config /config \
    && ln -vs /config /root/.config/gphotos-sync \
    && mkdir -vp /storage

# make the installed version of gphotos-sync available to non root users
RUN chmod -R a+rx /root
ENV HOME=/root

VOLUME /config /storage

ENTRYPOINT ["gphotos-sync"]
CMD ["--version"]

EXPOSE 8080
