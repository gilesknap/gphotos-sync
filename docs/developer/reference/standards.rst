Standards
=========

This document defines the code and documentation standards used in this
repository.

Code Standards
--------------

The code in this repository conforms to standards set by the following tools:

- black_ for code formatting
- ruff_ for style checks
- mypy_ for static type checking

.. seealso::

    How-to guides `../how-to/lint` and `../how-to/static-analysis`

.. _documentation_standards:

Documentation Standards
-----------------------

Docstrings are pre-processed using the Sphinx Napoleon extension. As such,
google-style_ is considered as standard for this repository. Please use type
hints in the function signature for types. For example:

.. code:: python

    def func(arg1: str, arg2: int) -> bool:
        """Summary line.

        Extended description of function.

        Args:
            arg1: Description of arg1
            arg2: Description of arg2

        Returns:
            Description of return value
        """
        return True

.. _google-style: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/index.html#google-vs-numpy

Documentation is contained in the ``docs`` directory and extracted from
docstrings of the API.

Docs follow the underlining convention::

    Headling 1 (page title)
    =======================

    Heading 2
    ---------

    Heading 3
    ~~~~~~~~~

.. seealso::

    How-to guide `../how-to/build-docs`
