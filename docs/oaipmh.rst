.. _oaipmh:

OAI-PMH Support
===============

pycsw supports the `The Open Archives Initiative Protocol for Metadata Harvesting`_ (OAI-PMH) standard.

OAI-PMH OpenSearch support is enabled by default.  HTTP requests must be specified with ``mode=oaipmh`` in the base URL for OAI-PMH requests, e.g.:

.. code-block:: bash

  http://localhost/pycsw/csw.py?mode=oaipmh&verb=Identify

See http://www.openarchives.org/OAI/openarchivesprotocol.html for more information on OAI-PMH as well as request / reponse examples.

.. _`The Open Archives Initiative Protocol for Metadata Harvesting`: http://www.openarchives.org/OAI/openarchivesprotocol.html

