Pinning Requirements
====================

Introduction
------------

By design this project only defines dependencies in one place, i.e. in
the ``requires`` table in ``pyproject.toml``.

In the ``requires`` table it is possible to pin versions of some dependencies
as needed. For library projects it is best to leave pinning to a minimum so
that your library can be used by the widest range of applications.

When CI builds the project it will use the latest compatible set of
dependencies available (after applying your pins and any dependencies' pins).

This approach means that there is a possibility that a future build may
break because an updated release of a dependency has made a breaking change.

The correct way to fix such an issue is to work out the minimum pinning in
``requires`` that will resolve the problem. However this can be quite hard to
do and may be time consuming when simply trying to release a minor update.

For this reason we provide a mechanism for locking all dependencies to
the same version as a previous successful release. This is a quick fix that
should guarantee a successful CI build.

Finding the lock files
----------------------

Every release of the project will have a set of requirements files published
as release assets.

For example take a look at the release page for python3-pip-skeleton-cli here:
https://github.com/DiamondLightSource/python3-pip-skeleton-cli/releases/tag/3.3.0

There is a list of requirements*.txt files showing as assets on the release.

There is one file for each time the CI installed the project into a virtual
environment. There are multiple of these as the CI creates a number of
different environments.

The files are created using ``pip freeze`` and will contain a full list
of the dependencies and sub-dependencies with pinned versions.

You can download any of these files by clicking on them. It is best to use
the one that ran with the lowest Python version as this is more likely to
be compatible with all the versions of Python in the test matrix.
i.e. ``requirements-test-ubuntu-latest-3.8.txt`` in this example.

Applying the lock file
----------------------

To apply a lockfile:

- copy the requirements file you have downloaded to the root of your
  repository
- rename it to requirements.txt
- commit it into the repo
- push the changes

The CI looks for a requirements.txt in the root and will pass it to pip
when installing each of the test environments. pip will then install exactly
the same set of packages as the previous release.

Removing dependency locking from CI
-----------------------------------

Once the reasons for locking the build have been resolved it is a good idea
to go back to an unlocked build. This is because you get an early indication
of any incoming problems.

To restore unlocked builds in CI simply remove requirements.txt from the root
of the repo and push.
