Run in a container
==================

Pre-built containers with gphotos-sync and its dependencies already
installed are available on `Github Container Registry
<https://ghcr.io/gilesknap/gphotos-sync>`_.

Starting the container
----------------------

To pull the container from github container registry and run::

    $ docker run ghcr.io/gilesknap/gphotos-sync:main --version

To get a released version, use a numbered release instead of ``main``.
