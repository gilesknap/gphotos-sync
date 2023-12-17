2. Adopt gphotos-sync for project structure
===================================================

Date: 2022-02-18

Status
------

Accepted

Context
-------

We should use the following `pip-skeleton <https://github.com/gilesknap/gphotos-sync>`_.
The skeleton will ensure consistency in developer
environments and package management.

Decision
--------

We have switched to using the skeleton.

Consequences
------------

This module will use a fixed set of tools as developed in gphotos-sync
and can pull from this skeleton to update the packaging to the latest techniques.

As such, the developer environment may have changed, the following could be
different:

- linting
- formatting
- pip venv setup
- CI/CD
