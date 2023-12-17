Run static analysis using mypy
==============================

Static type analysis is done with mypy_. It checks type definition in source
files without running them, and highlights potential issues where types do not
match. You can run it with::

    $ tox -e mypy
