Build the docs using sphinx
===========================

You can build the `sphinx`_ based docs from the project directory by running::

    $ tox -e docs

This will build the static docs on the ``docs`` directory, which includes API
docs that pull in docstrings from the code.

.. seealso::

    `documentation_standards`

The docs will be built into the ``build/html`` directory, and can be opened
locally with a web browser::

    $ firefox build/html/index.html

Autobuild
---------

You can also run an autobuild process, which will watch your ``docs``
directory for changes and rebuild whenever it sees changes, reloading any
browsers watching the pages::

    $ tox -e docs autobuild

You can view the pages at localhost::

    $ firefox http://localhost:8000

If you are making changes to source code too, you can tell it to watch
changes in this directory too::

    $ tox -e docs autobuild -- --watch src

.. _sphinx: https://www.sphinx-doc.org/
