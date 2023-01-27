Developer install
=================

These instructions will take you through the minimal steps required to get a dev
environment setup, so you can run the tests locally.

Clone the repository
--------------------

First clone the repository locally using `Git
<https://git-scm.com/downloads>`_::

    $ git clone git://github.com/DiamondLightSource/python3-pip-skeleton.git

Install dependencies
--------------------

You can choose to either develop on the host machine using a `venv` (which
requires python 3.8 or later) or to run in a container under `VSCode
<https://code.visualstudio.com/>`_

.. tab-set::

    .. tab-item:: Local virtualenv

        .. code::

            $ cd python3-pip-skeleton
            $ python3 -m venv venv
            $ source venv/bin/activate
            $ pip install -e '.[dev]'

    .. tab-item:: VSCode devcontainer

        .. code::

            $ vscode python3-pip-skeleton
            # Click on 'Reopen in Container' when prompted
            # Open a new terminal

See what was installed
----------------------

To see a graph of the python package dependency tree type::

    $ pipdeptree

Build and test
--------------

Now you have a development environment you can run the tests in a terminal::

    $ tox -p

This will run in parallel the following checks:

- `../how-to/build-docs`
- `../how-to/run-tests`
- `../how-to/static-analysis`
- `../how-to/lint`
