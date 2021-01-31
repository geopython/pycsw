.. _opensearch:

OpenSearch Support
==================

pycsw supports the `OGC OpenSearch Geo and Time Extensions 1.0`_ standard via the following conformance classes:

- Core (GeoSpatial Service) ``{searchTerms}``, ``{geo:box}``, ``{startIndex}``, ``{count}``
- Temporal Search core ``{time:start}``, ``{time:end}``

OpenSearch support is enabled by default.  HTTP requests must be specified with ``mode=opensearch`` in the base URL for OpenSearch requests, e.g.:

.. code-block:: bash

  http://localhost/pycsw/csw.py?mode=opensearch&service=CSW&version=2.0.2&request=GetCapabilities

This will return the Description document which can then be `autodiscovered <https://github.com/dewitt/opensearch/blob/master/opensearch-1-1-draft-6.md#Autodiscovery>`_.

.. _`OGC OpenSearch Geo and Time Extensions 1.0`: http://www.opengeospatial.org/standards/opensearchgeo

OpenSearch Temporal Queries
---------------------------

By default, pycsw's OpenSearch temporal support will query the Dublin Core ``dc:date`` property as
a time instant/single point in time.  To enable temporal extent search, set ``profiles=apiso`` which
will query the temporal extents of a metadata record (``apiso:TempExtent_begin`` and ``apiso:TempExtent_end``).

At the HTTP API level, time is supported via either ``time=t1/t2`` or ``start=t1&stop=t2``.  If the
``time`` parameter is present, it will override the ``start`` and ``stop`` parameters respectively.

.. _`OGC OpenSearch Extension for Earth Observation`: http://docs.opengeospatial.org/is/13-026r9/13-026r9.html
.. _`OGC OpenSearch Geo and Time Extensions 1.0`: http://www.opengeospatial.org/standards/opensearchgeo
