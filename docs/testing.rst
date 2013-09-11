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

The pycsw tests framework (in ``tests``) is a collection of testsuites to perform automated regession testing of the codebase.

Running
^^^^^^^

The tests framework can be run from ``tests``:

.. code-block:: bash

  $ cd /path/to/pycsw
  $ cd tests
  # run all tests against http://localhost:8000/
  $ python ./run_tests.py -u http://localhost:8000/
  # run only specific testsuites against http://localhost:8000/
  $ python ./run_tests.py -u http://localhost:8000/ -s apiso,fgdc
  # lots of output

The tests runs HTTP GET and POST requests.  The expected output for each test can be found in ``expected``.  Results are categorized as ``passed``, ``failed``, or ``initialized``.  A summary of results is output at the end of the run.

Failed Tests
^^^^^^^^^^^^

If a given test has failed, the output is saved in ``results``.  The resulting failure can be analyzed by running ``diff expected/name_of_test.xml results/name_of_test.xml`` to find variances.

Test Suites
^^^^^^^^^^^

The tests framework is run against a series of 'suites' (in ``tests/suites``), each of which specifies a given configuration to test various functionality of the codebase.  Each suite is structured as follows:

* ``tests/suites/suite/default.cfg``: the configuration for the suite
* ``tests/suites/suite/post``: directory of XML documents for HTTP POST requests
* ``tests/suites/suite/get/requests.txt``: directory and text file of KVP for HTTP GET requests

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
* run ``python ./run_tests.py -u <url>``

To add a new test suite:

* create a new directory under ``tests/suites`` (e.g. ``foo``)
* create a new configuration in ``tests/suites/foo/default.cfg``.  Ensure that all file paths are relative to ``path/to/pycsw``
* populate HTTP POST requests in ``tests/suites/foo/post``
* populate HTTP GET requests in ``tests/suites/foo/get/requests.txt``
* run ``python ./run_tests.py -u <url>``

Web Testing
^^^^^^^^^^^

You can also use the pycsw tests via your web browser to perform sample requests against your pycsw install.  The tests are is located in ``tests/``.  To generate the HTML page, run ``gen_html.py``:

.. code-block:: bash

  $ python ./gen_html.py > index.html

Then navigate to ``http://host/path/to/pycsw/tests/index.html``.

.. _`Compliance & Interoperability Testing & Evaluation Initiative`: http://cite.opengeospatial.org/
