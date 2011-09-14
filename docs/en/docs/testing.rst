.. _testing:

Testing
=======

.. _ogc-cite:

OGC CITE
--------

Compliance benchmarking is done via the OGC `Compliance & Interoperability Testing & Evaluation Initiative`_.  The pycsw `wiki <http://sourceforge.net/apps/trac/pycsw/wiki/OGCCITECompliance>`_ documents testing procedures and status.

.. _tester:

Tester
------

The pycsw tester framework (in ``tester``) is a collection of testsuites to perform automated regession testing of the codebase.

Running
^^^^^^^

The tester framework can be run from ``tester``:

.. code-block:: bash

  $ cd /path/to/pycsw
  $ cd tester
  $ python ./run_tests.py
  # lots of output

The tester runs HTTP GET and POST requests.  The expected output for each test can be found in ``expected``.  Results are categorized as ``passed``, ``failed``, or ``initialized``.  A summary of results is output at the end of the run.

Failed Tests
^^^^^^^^^^^^

If a given test has failed, the output is saved in ``results``.  The resulting failure can be analyzed by running ``diff expected/name_of_test.xml results/name_of_test.xml`` to find variances.

Test Suites
^^^^^^^^^^^

The tester framework is run against a series of 'suites' (in ``tester/suites``), each of which specifies a given configuration to test various functionality of the codebase.  Each suite is structured as follows:

* ``tester/suite/default.cfg``: the configuration for the suite
* ``tester/suite/post``: directory of XML documents for HTTP POST requests
* ``tester/suite/get/requests.txt``: directory and text file of KVP for HTTP GET requests

When the tester is invoked, the following operations are run:

* pycsw configuration is set to ``tester/suite/default.cfg``
* HTTP POST requests are run against ``tester/suite/post/*.xml``
* HTTP GET requests are run against each request in ``tester/suite/get/requests.txt``

The CSV format of ``tester/suite/get/requests.txt`` is ``testname,request``, with one line for each test.  The ``testname`` value is a unique test name (this value sets the name of the output file in the test results).  The ``request`` value is the HTTP GET request.  The ``PYCSW_SERVER`` token is replaced at runtime with the URL to the pycsw install.

Adding New Tests
^^^^^^^^^^^^^^^^

To add tests to an existing suite:

* for HTTP POST tests, add XML documents to ``tester/suite/post``
* for HTTP GET tests, add tests (one per line) to ``tester/suite/get/requests.txt``
* run ``python ./run_tests.py <url>``

To add a new test suite:

* create a new directory under ``tester/suites`` (e.g. ``foo``)
* create a new configuration in ``tester/suites/foo/default.cfg``.  Ensure that all file paths are relative to ``path/to/pycsw``
* populate HTTP POST requests in ``tester/suites/foo/post``
* populate HTTP GET requests in ``tester/suites/foo/get/requests.txt``
* run ``python ./run_tests.py <url>``

Web Testing
^^^^^^^^^^^

You can also use the pycsw tester via your web browser to perform sample requests against your pycsw install.  The tester is located in ``tester/``.  To generate the HTML page, run ``gen_html.py``:

.. code-block:: bash

  $ python ./gen_html.py > index.html

Then navigate to ``http://host/path/to/pycsw/tester/index.html``.

.. _`Compliance & Interoperability Testing & Evaluation Initiative`: http://cite.opengeospatial.org/
