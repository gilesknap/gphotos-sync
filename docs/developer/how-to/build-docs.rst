Build the docs using sphinx
===========================

You can build the `sphinx`_ based docs from the project directory by running::

    $ tox -e docs

This will build the static docs on the ``docs`` directory, which includes API
docs that pull in docstrings from the code.

.. seealso::

    `documentation_standards`

The docs will be built into the ``build/html`` directory, and can be opened
locally with a web browse::

    $ firefox build/html/index.html

.. _sphinx: https://www.sphinx-doc.org/