Run the tests using pytest
==========================

Testing is done with pytest_. It will find functions in the project that `look
like tests`_, and run them to check for errors. You can run it with::

    $ tox -e pytest

It will also report coverage to the commandline and to ``cov.xml``.

.. _pytest: https://pytest.org/
.. _look like tests: https://docs.pytest.org/explanation/goodpractices.html#test-discovery
