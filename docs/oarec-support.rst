.. _oarec-support:

OGC API - Records Support
=========================

Versions
--------

pycsw supports `OGC API - Records - Part 1: Core, version 1.0`_ by default.

Request Examples
----------------

As the OGC successor to CSW, OGC API - Records is a change in paradigm rooted in lowering
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
  http://localhost:8000/collections/metadata:main/items?filter-lang=cql-text&filter=title LIKE '%lorem%'
  # collection query, limiting results
  http://localhost:8000/collections/metadata:main/items?limit=1
  # collection query, paging
  http://localhost:8000/collections/metadata:main/items?limit=10&offset=10
  # collection query, paging and sorting (default ascending)
  http://localhost:8000/collections/metadata:main/items?limit=10&offset=10&sortby=title
  # collection query, paging and sorting (descending)
  http://localhost:8000/collections/metadata:main/items?limit=10&offset=10&sortby=-title
  # collection query as CQL JSON (HTTP POST), as curl request
  curl http://localhost:8000/collections/metadata:main/items --request POST -H "Content-Type: application/json" --data '{ "eq": [{ "property": "title" }, "Lorem ipsum"]}'
  # collection query as CQL JSON (HTTP POST), limiting results, as curl request
  curl http://localhost:8000/collections/metadata:main/items?limit=0 --request POST -H "Content-Type: application/json" --data '{ "eq": [{ "property": "title" }, "Lorem ipsum"]}'

  # collection item as GeoJSON
  http://localhost:8000/collections/metadata:main/items/{itemId}
  # collection item as HTML
  http://localhost:8000/collections/metadata:main/items/{itemId}?f=html
  # collection item as XML
  http://localhost:8000/collections/metadata:main/items/{itemId}?f=xml

Virtual Collections
-------------------

In OGC API - Records, pycsw's global repository is named `metadata:main`, which
serves all metadata records from a given pycsw configuration.

OGC API - Records support exposes parent metadata as distinct collections,
reducing the barrier for users querying on a specific collection, for
multiple collections.  This functionality is implemented by default and does
not require additional setup/configuration by the user.  More information
on this feature can be found in `RFC 10: OGC API - Records virtual collections support`_.


.. _`OGC API - Records - Part 1: Core, version 1.0`: https://ogcapi.ogc.org/records
.. _`RFC 10: OGC API - Records virtual collections support`: https://pycsw.org/development/rfc/rfc-10.html
