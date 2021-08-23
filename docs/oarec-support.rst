.. _oarec-support:

OGC API - Records Support
=========================

Versions
--------

pycsw supports `OGC API - Records - Part 1: Core, version 1.0`_ (OARec) by default.

Request Examples
----------------

As the OGC successor to CSW, OARec is a change in paradigm rooted in lowering
the barrier to entry, being webby/of the web, and focusing on developer experience/adoption.
JSON and HTML output formats are both supported via the ``f`` parameter.

.. code-block:: bash

  # landing page
  http://localhost:8000/
  # landing page explictly as JSON
  http://localhost:8000/?f=json
  # landing page as HTML
  http://localhost:8000/?f=html
  # conformance classes
  http://localhost:8000/conformance
  # all collections
  http://localhost:8000/collections
  # default collection
  http://localhost:8000/collections/metadata:main
  # default collection queryables
  http://localhost:8000/collections/metadata:main/queryables

  # collection queries
  # query parameters can be combined (exclusive/AND)

  # collection query, all records
  http://localhost:8000/collections/metadata:main/items
  # collection query, full text search
  http://localhost:8000/collections/metadata:main/items?q=lorem
  # collection query, full text search (multiple terms result in an exclusive (AND) search
  http://localhost:8000/collections/metadata:main/items?q=lorem dolor
  # collection query, spatial query
  http://localhost:8000/collections/metadata:main/items?bbox=-142,42,-52,84
  # collection query, temporal query
  http://localhost:8000/collections/metadata:main/items?datetime=2001-10-30/2007-10-30
  # collection query, temporal query, before
  http://localhost:8000/collections/metadata:main/items?datetime=../2007-10-30
  # collection query, temporal query, after
  http://localhost:8000/collections/metadata:main/items?datetime=2007-10-30/..
  # collection query, property query
  http://localhost:8000/collections/metadata:main/items?title=Lorem%20ipsum
  # collection query, CQL filter
  http://localhost:8000/collections/metadata:main/items?filter=title like "%lorem%"
  # collection query, limiting results
  http://localhost:8000/collections/metadata:main/items?limit=1
  # collection query, paging
  http://localhost:8000/collections/metadata:main/items?limit=10&startindex=10

  # collection item as GeoJSON
  http://localhost:8000/collections/metadata:main/items/{itemId}
  # collection item as HTML
  http://localhost:8000/collections/metadata:main/items/{itemId}?f=html
  # collection item as XML
  http://localhost:8000/collections/metadata:main/items/{itemId}?f=xml


.. _`OGC API - Records - Part 1: Core, version 1.0`: https://ogcapi.ogc.org/records
