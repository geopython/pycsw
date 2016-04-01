.. _opensearch:

OpenSearch Support
==================

pycsw supports the `OGC OpenSearch Geo and Time Extensions 1.0`_ standard via the following conformance classes:

- Core (GeoSpatial Service) ``{searchTerms}``, ``{geo:box}``, ``{startIndex}``, ``{count}``
- Temporal Search core ``{time:start}``, ``{time:end}``

OpenSearch support is enabled by default.  HTTP requests must be specified with ``mode=opensearch`` in the base URL for OpenSearch requests, e.g.:

.. code-block:: bash

  http://localhost/pycsw/csw.py?mode=opensearch&service=CSW&version=2.0.2&request=GetCapabilities

This will return the Description document which can then be `autodiscovered <http://www.opensearch.org/Specifications/OpenSearch/1.1#Autodiscovery>`_.

.. _`OGC OpenSearch Geo and Time Extensions 1.0`: http://www.opengeospatial.org/standards/opensearchgeo

