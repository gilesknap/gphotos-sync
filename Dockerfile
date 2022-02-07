# This file is for use as a devcontainer and a runtime container
# 
# The devcontainer should use the build target and run as root with podman 
# or docker with user namespaces.
#
FROM python:3.10 as build

# Add any system dependencies for the developer/build environment here
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    busybox \
    git \
    net-tools \
    vim \
    && rm -rf /var/lib/apt/lists/* \
    && busybox --install

COPY . /project

RUN cd /project && \
    pip install --upgrade pip build && \
    export SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct) && \
    python -m build --sdist --wheel && \
    touch requirements.txt

RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH

RUN cd /project && \
    pip install --upgrade pip && \
    pip install -r requirements.txt dist/*.whl && \
    pip freeze  > dist/requirements.txt && \
    # we don't want to include our own wheel in requirements - remove with sed
    # and replace with a comment to avoid a zero length asset upload later
    sed -i '/file:/s/^/# Requirements for /' dist/requirements.txt

FROM python:3.10-slim as runtime

# Add apt-get system dependecies for runtime here if needed

COPY --from=build /venv/ /venv/
ENV PATH=/venv/bin:$PATH

# change this entrypoint if it is not the same as the repo
ENTRYPOINT ["python3-pip-skeleton"]
CMD ["--version"]
