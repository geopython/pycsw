.. _tests:

Testing
=======

There are a number of test suites that perform mostly functional testing.
These tests ensure that pycsw operates correctly and is compliant with the 
various supported standards. There is also a growing set of unit tests. 
These focus on smaller scope testing, in order to verify that individual 
bits of code are working as expected.

Tests can be run locally as part of the development cycle. They are also
run on pycsw's `GitHub Actions`_ continuous integration setup against all pushes and
pull requests to the code repository.

pycsw uses `pytest`_ for managing its automated tests.

Install pytest from the development requirements.

.. code:: bash

   pip3 install -r requirements-dev.txt

OGC API - Records
-----------------

Tests for OGC API - Records are located in ``tests/functionaltests/suites/oarec``. They
can be run as follows:

.. code:: bash

   pytest tests/functionaltests/suites/oarec


OGC CSW
-------

Tests for OGC CSW are located in ``tests/functionaltests/suites/csw30``. They
can be run as follows:

.. code:: bash

   pytest tests/functionaltests/suites/csw30


.. _ogc-cite:

OGC CITE
--------

In addition to pycsw's own tests, all public releases are also tested via the
OGC `Compliance & Interoperability Testing & Evaluation Initiative`_ (CITE).
The pycsw `wiki`_ documents CITE testing procedures and status.

Tests for OGC CITE are located in ``tests/functionaltests/suites/cite``. They
can be run as follows:

.. code:: bash

   pytest tests/functionaltests/suites/cite


Functional test suites
----------------------

Most of pycsw's tests are `functional tests`_. This means that
each test case is based on the requirements mandated by the specifications of
the various standards that pycsw implements. These tests focus on making sure
that pycsw works as expected.


Suites for xml-based standards (CSW, ATOM, etc)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A number of different test suites exist under ``tests/functionaltests/suites``.
Each suite specifies the following structure:

* A mandatory ``default.yml`` file with the pycsw configuration that must be
  used by the test suite;

* A mandatory ``expected/`` directory containing the expected results for each
  request;

* An optional ``data/`` directory that contains ``.xml`` files with testing
  data that is to be loaded into the suite's database before running the tests.
  The presence of this directory and its contents have the following meaning
  for tests:

  * If ``data/`` directory is present and contains files, they will be loaded
    into a new database for running the tests of the suite;

  * If ``data/`` directory is present and does not contain any data files, a
    new empty database is used in the tests;

  * If ``data/`` directory is absent, the suite will use a database populated
    with test data from the ``CITE`` suite.

* An optional ``get/requests.txt`` file that holds request parameters used for
  making HTTP GET requests.

  Each line in the file must be formatted with the following scheme:

      test_id,request_query_string

  For example:

    TestGetCapabilities,service=CSW&version=2.0.2&request=GetCapabilities

  When tests are run, the *test_id* is used for naming each test and for
  finding the expected result.

* An optional ``post/`` directory that holds ``.xml`` files used for making
  HTTP POST requests

Test generation uses pytest's `pytest_generate_tests`_ function. This
function is implemented in `tests/functionaltests/conftest.py`. It provides
an automatic parametrization of the
`tests/functionaltests/test_suites_functional:test_suites` test.
This parametrization causes the generation of a test for each of the GET and
POST requests defined in a suite's directory.


Suites for JSON-based standards (OGC API - Records, STAC API, etc)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These are implemented as simple pytest-based tests, for which no custom
test generation function exists. They are simpler to generate - look into the
implementation in `tests/functionaltests/suites/oarec` for examples.


Unit tests
----------

pycsw also features unit tests. These deal with testing the expected behaviour
of individual functions.

The usual implementation of unit tests is to import the function/method under
test, run it with a set of known arguments and assert that the result matches
the expected outcome.

Unit tests are defined in `pycsw/tests/unittests/<module_name>`.

pycsw's unit tests are marked with the `unit` marker. This makes it easy to run
them in isolation:

.. code:: bash

   # running only the unit tests (not the functional ones)
   pytest -m unit



Running tests
-------------

Since pycsw uses `pytest`_, tests are run with the ``pytest`` runner. A basic
test run can be made with:

.. code:: bash

   pytest

This command will run all tests and report on the number of successes, failures
and also the time it took to run them. The `pytest` command accepts several
additional parameters that can be used in order to customize the execution of
tests. Look into `pytest's invocation documentation`_ for a more complete
description. You can also get a description of the available parameters by
running:

.. code:: bash

   pytest --help


Running specific suites and test cases
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

pytest allows tagging tests with markers. These can be used to selectively run
some tests. pycsw uses two markers:

* ``unit`` - run only input tests
* ``functional``- run only functional tests

Markers can be specified by using the ``-m <marker_name>`` flag.

.. code:: bash

   pytest -m functional  # run only functional tests

You can also use the ``-k <name_expression>`` flag to select which tests to run. Since each
test's name includes the suite name, http method and an identifier for the
test, it is easy to run only certain tests.

.. code:: bash

   pytest -k "apiso and GetRecords"  # run only tests from the apiso suite that have GetRecords in their name
   pytest -k "post and GetRecords"  # run only tests that use HTTP POST and GetRecords in their name
   pytest -k "not harvesting"  # run all tests except those from the harvesting suite


The ``-m`` and ``-k`` flags can be combined.


Exiting fast
^^^^^^^^^^^^

The ``--exitfirst`` (or ``-x``) flag can be used to stop the test runner
immediately as soon as a test case fails.

.. code:: bash

   pytest --exitfirst


Seeing more output
^^^^^^^^^^^^^^^^^^

There are three main ways to get more output from running tests:

* The ``--verbose`` (or ``-v``) flag;

* The ``--capture=no`` flag - Messages sent to stdout by a test are not
  suppressed;

* The ``--pycsw-loglevel`` flag - Sets the log level of the pycsw instance
  under test. Set this value to ``debug`` in order to see all debug messages
  sent by pycsw while processing a request.


.. code:: bash

   pytest --verbose
   pytest --pycsw-loglevel=debug
   pytest -v --capture=no --pycsw-loglevel=debug


Comparing xml-based suite results with difflib instead of XML c14n
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Functional tests for XML-based suites compare results with their expected
values by using `XML canonicalisation - XML c14n`_.
Alternatively, you can call pytest with the ``--functional-prefer-diffs``
flag. This will enable comparison based on Python's ``difflib``. Comparison
is made on a line-by-line basis and in case of failure, a unified diff will
be printed to standard output.

.. code:: bash

   pytest -m functional -k 'harvesting' --functional-prefer-diffs


Saving test results for disk
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The result of each XML-based suite test can be saved to disk by using the
``--functional-save-results-directory`` option. Each result file is named
after the test identifier it has when running with pytest.

.. code:: bash

   pytest -m functional -k 'not harvesting' --functional-save-results-directory=/tmp/pycsw-test-results



Test coverage
^^^^^^^^^^^^^

Use the `--cov pycsw` flag in order to see information on code coverage. It is
possible to get output in a variety of formats.

.. code:: bash

   pytest --cov pycsw


Specifying a timeout for tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `--timeout <seconds>` option can be used to specify that if a test takes
more than `<seconds>` to run it is considered to have failed. Seconds can be
a float, so it is possibe to specify sub-second timeouts

.. code:: bash

   pytest --timeout=1.5


Linting with flake8
^^^^^^^^^^^^^^^^^^^

Use the `--flake8` flag to also check if the code complies with Python's style
guide

.. code:: bash

   pytest --flake8


Testing multiple Python versions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For testing multiple Python versions and configurations simultaneously you can
use `tox`_. pycsw includes a `tox.ini` file with a suitable configuration. It
can be used to run tests against multiple Python versions and also multiple
database backends. When running `tox` you can send arguments to the `pytest`
runner by using the invocation `tox <tox arguments> -- <pytest arguments>`.
Examples:

.. code:: bash

   # install tox on your system
   sudo pip3 install tox

   # run all tests on multiple Python versions against all databases,
   # with default arguments
   tox

   # run tests only with python3.7 and using sqlite as backend
   tox -e py37 -sqlite

   # run only csw30 suite tests with python3.7 and postgresql as backend
   tox -e py37-postgresql -- -k 'csw30'


Web Testing
^^^^^^^^^^^

You can also use the pycsw tests via your web browser to perform sample
requests against your pycsw install.  The tests are is located in
``tests/``.  To generate the HTML page:

.. code-block:: bash

   python3 gen_html.py > index.html


Then navigate to ``http://host/path/to/pycsw/tests/index.html``.



.. _Compliance & Interoperability Testing & Evaluation Initiative: https://github.com/opengeospatial/cite/wiki
.. _functional tests: https://en.wikipedia.org/wiki/Functional_testing
.. _pytest's invocation documentation: https://docs.pytest.org/en/stable/usage.html
.. _pytest: https://docs.pytest.org
.. _Github Actions: https://github.com/geopython/pycsw/actions
.. _tox: https://tox.readthedocs.io
.. _wiki: https://github.com/geopython/pycsw/wiki/OGC-CITE-Compliance
.. _pytest_generate_tests: #basic-pytest-generate-tests-example
.. _XML canonicalisation - XML c14n: https://www.w3.org/TR/xml-c14n/
