Container Local Build and Test
==============================

CI builds a runtime container for the project. The local tests
checks available via ``tox -p`` do not verify this because not
all developers will have docker installed locally.

If CI is failing to build the container, then it is best to fix and
test the problem locally. This would require that you have docker
or podman installed on your local workstation.

In the following examples the command ``docker`` is interchangeable with
``podman`` depending on which container cli you have installed.

To build the container and call it ``test``::

    cd <root of the project>
    docker build -t test .

To verify that the container runs::

    docker run -it test --help

You can pass any other command line parameters to your application
instead of --help.
