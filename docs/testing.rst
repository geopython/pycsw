.. _tests:

Testing
=======

Pycsw uses `pytest`_ for managing its automated tests. There are a number of
test suites that perform mostly functional testing. These tests ensure that
pycsw is compliant with the various supported standards.

The tests can be run locally as part of the development cycle. They are also
run on pycsw's `Travis`_ continuous integration server against all pushes and
pull requests to the code repository.

.. _ogc-cite:


OGC CITE
--------

In addition to pycsw's own tests, all public releases are also tested via the
OGC `Compliance & Interoperability Testing & Evaluation Initiative`_ (CITE).
The pycsw `wiki`_ documents CITE testing procedures and status.

.. _pytest: http://pytest.org/latest/
.. _Travis: http://travis-ci.org/geopython/pycsw
.. _Compliance & Interoperability Testing & Evaluation Initiative:
   http://cite.opengeospatial.org/
.. _wiki: https://github.com/geopython/pycsw/wiki/OGC-CITE-Compliance


Test suites
-----------

Currently most of pycsw's tests are `functional tests`_. This means that
each test case is based on the requirements mandated by the specifications of
the various standards that pycsw implements. These tests focus on making sure
that pycsw works as expected.

Each test follows the same workflow:

* Setup a local pycsw instance with a custom configuration and data repository
  for each suite of tests;

* Perform a series of GET and POST requests to the running pycsw instance;

* Compare the results of each request against a previously prepared expected
  result. If the test result matches the expected outcome the test passes,
  otherwise it fails.


A number of different test suites exist under ``tests/suites``. Each suite
specifies the following structure:

* A mandatory ``default.cfg`` file with the pycsw configuration that must be
  used by the test suite

* A mandatory ``expected/`` directory containing the expected results for each
  request

* An optional ``data/`` directory that contains ``.xml`` files with testing
  data that is to be loaded into the suite's database before running the tests

* An optional ``get/requests.txt`` file that holds request parameters used for
  making HTTP GET requests.

  Each line in the file must be formatted with the following scheme:

      test_id,request_query_string

  For example:

    GetCapabilities,service=CSW&version=2.0.2&request=GetCapabilities

  When tests are run, the *test_id* is used for naming each test and for
  finding the expected result.

* An optional ``post/`` directory that holds ``.xml`` files used for making
  HTTP POST requests


.. _functional tests: https://en.wikipedia.org/wiki/Functional_testing


Running tests locally
---------------------

Tests

Tester
------

The pycsw tests framework (in ``tests``) is a collection of testsuites to
perform automated regression testing of the codebase.  Test are run against
all pushes to the GitHub repository via Travis CI.

Running Locally
^^^^^^^^^^^^^^^

The tests framework can be run from ``tests`` using `Paver`_
(see ``pavement.py``) tasks for convenience:

.. code-block:: bash

   cd /path/to/pycsw
   # run all tests (starts up http://localhost:8000)
   paver test
   # run tests only against specific testsuites
   paver test -s apiso,fgdc
   # run all tests, including harvesting (this is turned off by default given
   # the volatility of remote services/data testing)
   paver test -r
   # run all tests with 1000ms time benchmark
   paver test -t 1000

The tests perform HTTP GET and POST requests against
``http://localhost:8000``.  The expected output for each test can be found
in ``expected``.  Results are categorized as ``passed``, ``failed``,
or ``initialized``.  A summary of results is output at the end of the run.

Failed Tests
^^^^^^^^^^^^

If a given test has failed, the output is saved in ``results``.  The
resulting failure can be analyzed by running
``diff tests/expected/name_of_test.xml tests/results/name_of_test.xml`` to
find variances.  The Paver task returns a status code which indicates the
number of tests which have failed (i.e. ``echo $?``).

Test Suites
^^^^^^^^^^^

The tests framework is run against a series of 'suites' (in ``tests/suites``),
each of which specifies a given configuration to test various functionality
of the codebase.  Each suite is structured as follows:

* ``tests/suites/suite/default.cfg``: the configuration for the suite
* ``tests/suites/suite/post``: directory of XML documents for HTTP POST
  requests
* ``tests/suites/suite/get/requests.txt``: directory and text file of KVP
  for HTTP GET requests
* ``tests/suites/suite/data``: directory of sample XML data required for the
  test suite.  Database and test data are setup/loaded automatically as part
  of testing

When the tests are invoked, the following operations are run:

* pycsw configuration is set to ``tests/suites/suite/default.cfg``
* HTTP POST requests are run against ``tests/suites/suite/post/*.xml``
* HTTP GET requests are run against each request in
  ``tests/suites/suite/get/requests.txt``

The CSV format of ``tests/suites/suite/get/requests.txt`` is
``testname,request``, with one line for each test.  The ``testname`` value
is a unique test name (this value sets the name of the output file in the
test results).  The ``request`` value is the HTTP GET request.  The
``PYCSW_SERVER`` token is replaced at runtime with the URL to the pycsw
install.

Adding New Tests
^^^^^^^^^^^^^^^^

To add tests to an existing suite:

* for HTTP POST tests, add XML documents to ``tests/suites/suite/post``
* for HTTP GET tests, add tests (one per line) to
  ``tests/suites/suite/get/requests.txt``
* run ``paver test``

To add a new test suite:

* create a new directory under ``tests/suites`` (e.g. ``foo``)
* create a new configuration in ``tests/suites/foo/default.cfg``

  * Ensure that all file paths are relative to ``path/to/pycsw``
  * Ensure that ``repository.database`` points to an SQLite3 database
    called ``tests/suites/foo/data/records.db``.  The database *must* be
    called ``records.db`` and the directory ``tests/suites/foo/data``
    *must* exist

* populate HTTP POST requests in ``tests/suites/foo/post``
* populate HTTP GET requests in ``tests/suites/foo/get/requests.txt``
* if the testsuite requires test data, create ``tests/suites/foo/data`` are
  store XML file there
* run ``paver test`` (or ``paver test -s foo`` to test only the new test
  suite)

The new test suite database will be created automatically and used as part of
tests.

Web Testing
^^^^^^^^^^^

You can also use the pycsw tests via your web browser to perform sample
requests against your pycsw install.  The tests are is located in
``tests/``.  To generate the HTML page:

.. code-block:: bash

  $ paver gen_tests_html

Then navigate to ``http://host/path/to/pycsw/tests/index.html``.

.. _`Paver`: http://paver.github.io/paver/
