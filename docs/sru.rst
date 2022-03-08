.. _sru:

Search/Retrieval via URL (SRU) Support
======================================

pycsw supports the `Search/Retrieval via URL`_ search protocol implementation as per subclause 8.4 of the OpenGIS Catalogue Service Implementation Specification.

SRU support is enabled by default.  There are two ways to access SRU
depending on the deployment pattern chosen.

OARec deployment
----------------

.. code-block:: bash

  http://localhost:8000/sru

CSW legacy deployment
---------------------

HTTP GET requests must be specified with ``mode=sru`` for SRU requests, e.g.:

.. code-block:: bash

  http://localhost/pycsw/csw.py?mode=sru&operation=searchRetrieve&query=foo

See https://www.loc.gov/standards/sru/misc/simple.html for example SRU requests.

.. _`Search/Retrieval via URL`: https://www.loc.gov/standards/sru
