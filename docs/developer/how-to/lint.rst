Run linting using pre-commit
============================

Code linting is handled by black_ and ruff_ run under pre-commit_.

Running pre-commit
------------------

You can run the above checks on all files with this command::

    $ tox -e pre-commit

Or you can install a pre-commit hook that will run each time you do a ``git
commit`` on just the files that have changed::

    $ pre-commit install

It is also possible to `automatically enable pre-commit on cloned repositories <https://pre-commit.com/#automatically-enabling-pre-commit-on-repositories>`_.
This will result in pre-commits being enabled on every repo your user clones from now on.

Fixing issues
-------------

If black reports an issue you can tell it to reformat all the files in the
repository::

    $ black .

Likewise with ruff::

    $ ruff --fix .

Ruff may not be able to automatically fix all issues; in this case, you will have to fix those manually.

VSCode support
--------------

The ``.vscode/settings.json`` will run black formatting as well as
ruff checking on save. Issues will be highlighted in the editor window.
