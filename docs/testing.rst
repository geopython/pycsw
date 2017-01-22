.. _tests:

Testing
=======

Pycsw uses `pytest`_ for managing its automated tests. There are a number of
test suites that perform mostly functional testing. These tests ensure that
pycsw is compliant with the various supported standards.

Tests can be run locally as part of the development cycle. They are also
run on pycsw's `Travis`_ continuous integration server against all pushes and
pull requests to the code repository.


.. _ogc-cite:

OGC CITE
--------

In addition to pycsw's own tests, all public releases are also tested via the
OGC `Compliance & Interoperability Testing & Evaluation Initiative`_ (CITE).
The pycsw `wiki`_ documents CITE testing procedures and status.


Functional test suites
----------------------

Currently most of pycsw's tests are `functional tests`_. This means that
each test case is based on the requirements mandated by the specifications of
the various standards that pycsw implements. These tests focus on making sure
that pycsw works as expected.

Each test follows the same workflow:

* Create a new pycsw instance with a custom configuration and data repository
  for each suite of tests;

* Perform a series of GET and POST requests to the running pycsw instance;

* Compare the results of each request against a previously prepared expected
  result. If the test result matches the expected outcome the test passes,
  otherwise it fails.


A number of different test suites exist under ``tests/functionaltests/suites``.
Each suite specifies the following structure:

* A mandatory ``default.cfg`` file with the pycsw configuration that must be
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


Test identifiers
^^^^^^^^^^^^^^^^

Each test has an identifier that is built using the following rule:

    <test_function>[<suite_name>_<http_method>_<test_name>]

For example:

    test_suites[default_post_GetRecords-end]


Functional tests' implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Functional tests are generated for each suite directory present under 
`tests/functionaltests/suites`. Test generation uses pytest's 
`pytest_generate_tests`_ function. This function is implemented in 
`tests/functionaltests/conftest.py`. It provides an automatic parametrization 
of the `tests/functionaltests/test_suites_functional:test_suites` function. 
This parametrization causes the generation of a test for each of the GET and 
POST requests defined in a suite's directory.


Adding New Tests
^^^^^^^^^^^^^^^^

To add tests to an existing suite:

* for HTTP POST tests, add XML documents to 
  ``tests/functionaltests/suites/<suite>/post``
* for HTTP GET tests, add tests (one per line) to
  ``tests/functionaltests/suites/<suite>/get/requests.txt``

To add a new test suite:

* Create a new directory under ``tests/functionaltests/suites`` (e.g. ``foo``)
* Create a new configuration in ``tests/suites/foo/default.cfg``
* Populate HTTP POST requests in ``tests/suites/foo/post``
* Populate HTTP GET requests in ``tests/suites/foo/get/requests.txt``
* If the test suite requires test data, create ``tests/suites/foo/data`` and
  store XML files there. These will be inserted in the test catalogue at test
  runtime
* Use pytest or tox as described above in order to run the tests

The new test suite database will be created automatically and used as part of
tests.


Running tests
-------------

Since pycsw uses `pytest`_, tests are run with the ``py.test`` runner. A basic
test run can be made with:

.. code:: bash

   py.test

This command will run all tests and report on the number of successes, failures
and also the time it took to run them. The `py.test` command accepts several
additional parameters that can be used in order to customize the execution of
tests. Look into `pytest's invocation documentation`_ for a more complete
description. You can also get a description of the available parameters by
running:

.. code:: bash

   py.test --help


Running specific suites and test cases
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the ``-k <name_expression>`` flag to select which tests to run. Since each
test's name includes the suite name, http method and an identifier for the
test, it is easy to run only certain tests.

.. code:: bash

   py.test -k "apiso and GetRecords"  # run only tests from the apiso suite that have GetRecords in their name
   py.test -k "post and GetRecords"  # run only tests that use HTTP POST and GetRecords in their name
   py.test -k "not harvesting"  # run all tests except those from the harvesting suite


Exiting fast
^^^^^^^^^^^^

The ``--exitfirst`` (or ``-x``) flag can be used to stop the test runner
immediately as soon as a test case fails.

.. code:: bash

   py.test --exitfirst


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

   py.test --verbose
   py.test --pycsw-loglevel=debug
   py.test -v --capture=no --pycsw-loglevel=debug


Test coverage
^^^^^^^^^^^^^

Use the `--cov pycsw` flag in order to see information on code coverage. It is
possible to get output in a variety of formats.

.. code:: bash

   py.test --cov pycsw


Specifying a timeout for tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `--timeout <seconds>` option can be used to specify that if a test takes
more than `<seconds>` to run it is considered to have failed. Seconds can be
a float, so it is possibe to specify sub-second timeouts

.. code:: bash

   py.test --timeout=1.5


Linting with flake8
^^^^^^^^^^^^^^^^^^^

Use the `--flake8` flag to also check if the code complies with Python's style
guide

.. code:: bash

   py.test --flake8


Testing multiple python versions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For testing multiple python versions and configurations simultaneously you can
use `tox`_. pycsw includes a `tox.ini` file with a suitable configuration. It
can be used to run tests against multiple python versions and also multiple
database backends. When running `tox` you can send arguments to the `py.test`
runner by using the invocation `tox <tox arguments> -- <py.test arguments>`.
Examples:

.. code:: bash

   # install tox on your system
   sudo pip install tox

   # run all tests on multiple python versions against all databases,
   # with default arguments
   tox

   # run tests only with python2.7 and using sqlite as backend
   tox -e py27-sqlite

   # run only csw30 suite tests with python3.5 and postgresql as backend
   tox -e py35-postgresql -- -k 'csw30'


Web Testing
^^^^^^^^^^^

You can also use the pycsw tests via your web browser to perform sample
requests against your pycsw install.  The tests are is located in
``tests/``.  To generate the HTML page:

.. code-block:: bash

  $ paver gen_tests_html

Then navigate to ``http://host/path/to/pycsw/tests/index.html``.



.. _Compliance & Interoperability Testing & Evaluation Initiative: http://cite.opengeospatial.org/
.. _functional tests: https://en.wikipedia.org/wiki/Functional_testing
.. _`Paver`: http://paver.github.io/paver/
.. _pytest's invocation documentation: http://docs.pytest.org/en/latest/usage.html
.. _pytest: http://pytest.org/latest/
.. _Travis: http://travis-ci.org/geopython/pycsw
.. _tox: https://tox.readthedocs.io
.. _wiki: https://github.com/geopython/pycsw/wiki/OGC-CITE-Compliance
.. _pytest_generate_tests: http://docs.pytest.org/en/latest/parametrize.html#basic-pytest-generate-tests-example
