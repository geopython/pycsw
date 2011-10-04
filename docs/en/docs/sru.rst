.. _sru:

Search/Retrieval via URL (SRU) Support
======================================

pycsw supports the `Search/Retrieval via URL`_ search protocol implementation as per subclause 8.4 of the OpenGIS Catalogue Service Implementation Specification.

SRU support is enabled by default.  HTTP GET requests must be specified with ``mode=sru`` for SRU requests, e.g.:

.. code-block:: bash

  http://localhost/pycsw/csw.py?mode=sru&operation=searchRetrieve&query=foo

See http://www.loc.gov/standards/sru/simple.html for example SRU requests.

.. _`Search/Retrieval via URL`: http://www.loc.gov/standards/sru/
