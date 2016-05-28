.. _testing:

Testing
=======

.. _ogc-cite:

OGC CITE
--------

Compliance benchmarking is done via the OGC `Compliance & Interoperability Testing & Evaluation Initiative`_.  The pycsw `wiki <https://github.com/geopython/pycsw/wiki/OGC-CITE-Compliance>`_ documents testing procedures and status.

.. _tests:

Tester
------

The pycsw tests framework (in ``tests``) is a collection of testsuites to perform automated regession testing of the codebase.  Test are run against all pushes to the GitHub repository via `Travis CI`_.

Running Locally
^^^^^^^^^^^^^^^

The tests framework can be run from ``tests`` using `Paver`_ (see ``pavement.py``) tasks for convenience:

.. code-block:: bash

  $ cd /path/to/pycsw
  # run all tests (starts up http://localhost:8000)
  $ paver test
  # run tests only against specific testsuites 
  $ paver test -s apiso,fgdc
  # run all tests, including harvesting (this is turned off by default given the volatility of remote services/data testing)
  $ paver test -r
  # run all tests with 1000ms time benchmark
  $ paver test -t 1000

The tests perform HTTP GET and POST requests against ``http://localhost:8000``.  The expected output for each test can be found in ``expected``.  Results are categorized as ``passed``, ``failed``, or ``initialized``.  A summary of results is output at the end of the run.

Failed Tests
^^^^^^^^^^^^

If a given test has failed, the output is saved in ``results``.  The resulting failure can be analyzed by running ``diff tests/expected/name_of_test.xml tests/results/name_of_test.xml`` to find variances.  The Paver task returns a status code which indicates the number of tests which have failed (i.e. ``echo $?``).

Test Suites
^^^^^^^^^^^

The tests framework is run against a series of 'suites' (in ``tests/suites``), each of which specifies a given configuration to test various functionality of the codebase.  Each suite is structured as follows:

* ``tests/suites/suite/default.cfg``: the configuration for the suite
* ``tests/suites/suite/post``: directory of XML documents for HTTP POST requests
* ``tests/suites/suite/get/requests.txt``: directory and text file of KVP for HTTP GET requests
* ``tests/suites/suite/data``: directory of sample XML data required for the test suite.  Database and test data are setup/loaded automatically as part of testing

When the tests are invoked, the following operations are run:

* pycsw configuration is set to ``tests/suites/suite/default.cfg``
* HTTP POST requests are run against ``tests/suites/suite/post/*.xml``
* HTTP GET requests are run against each request in ``tests/suites/suite/get/requests.txt``

The CSV format of ``tests/suites/suite/get/requests.txt`` is ``testname,request``, with one line for each test.  The ``testname`` value is a unique test name (this value sets the name of the output file in the test results).  The ``request`` value is the HTTP GET request.  The ``PYCSW_SERVER`` token is replaced at runtime with the URL to the pycsw install.

Adding New Tests
^^^^^^^^^^^^^^^^

To add tests to an existing suite:

* for HTTP POST tests, add XML documents to ``tests/suites/suite/post``
* for HTTP GET tests, add tests (one per line) to ``tests/suites/suite/get/requests.txt``
* run ``paver test``

To add a new test suite:

* create a new directory under ``tests/suites`` (e.g. ``foo``)
* create a new configuration in ``tests/suites/foo/default.cfg``

  * Ensure that all file paths are relative to ``path/to/pycsw``
  * Ensure that ``repository.database`` points to an SQLite3 database called ``tests/suites/foo/data/records.db``.  The database *must* be called ``records.db`` and the directory ``tests/suites/foo/data`` *must* exist

* populate HTTP POST requests in ``tests/suites/foo/post``
* populate HTTP GET requests in ``tests/suites/foo/get/requests.txt``
* if the testsuite requires test data, create ``tests/suites/foo/data`` are store XML file there
* run ``paver test`` (or ``paver test -s foo`` to test only the new test suite)

The new test suite database will be created automatically and used as part of tests.

Web Testing
^^^^^^^^^^^

You can also use the pycsw tests via your web browser to perform sample requests against your pycsw install.  The tests are is located in ``tests/``.  To generate the HTML page:

.. code-block:: bash

  $ paver gen_tests_html

Then navigate to ``http://host/path/to/pycsw/tests/index.html``.

.. _`Compliance & Interoperability Testing & Evaluation Initiative`: http://cite.opengeospatial.org/
.. _`Travis CI`: http://travis-ci.org/geopython/pycsw
.. _`Paver`: http://paver.github.io/paver/
