.. _stac:

SpatioTemporal Asset Catalog (STAC) API Support
===============================================

Versions
--------

pycsw supports `SpatioTemporal Asset Catalog API version 1.0.0-beta2`_ by default.

pycsw implements provides STAC support in the following manner:

* a pycsw repository is equivalent to a STAC collection
* pycsw metadata records are equivalent to STAC items

The STAC specification is designed with the same principles as OGC API - Records.

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

  # collection queries
  # query parameters can be combined (exclusive/AND)

  # collection query, all records
  http://localhost:8000/search
  # collection query, full text search
  http://localhost:8000/search?q=lorem
  # collection query, spatial query
  http://localhost:8000/search?bbox=-142,42,-52,84
  # collection query, temporal query
  http://localhost:8000/search?datetime=2001-10-30/2007-10-30
  # collection query, temporal query, before
  http://localhost:8000/search?datetime=../2007-10-30
  # collection query, temporal query, after
  http://localhost:8000/search?datetime=2007-10-30/..
  # collection query, property query
  http://localhost:8000/search?title=Lorem%20ipsum
  # collection query, CQL filter
  http://localhost:8000/search?filter=title like "%lorem%"
  # collection query, limiting results
  http://localhost:8000/search?limit=1
  # collection query, paging
  http://localhost:8000/search?limit=10&startindex=10
  # collection query as JSON (HTTP POST), as curl request
  curl http://localhost:8000/search --request POST -H "Content-Type: application/json" --data '{"bbox": [-180, -90, 180, 90], "datetime": "2006-03-26"}'
  # collection query as CQL JSON (HTTP POST), limiting results, as curl request
  curl http://localhost:8000/search --request POST -H "Content-Type: application/json" --data '{"limit": 1, "bbox": [-180, -90, 180, 90], "datetime": "2006-03-26"}'

  # collection item as GeoJSON
  http://localhost:8000/collections/metadata:main/items/{itemId}
  # collection item as HTML
  http://localhost:8000/collections/metadata:main/items/{itemId}?f=html
  # collection item as XML
  http://localhost:8000/collections/metadata:main/items/{itemId}?f=xml


.. _`SpatioTemporal Asset Catalog API version 1.0.0-beta2`: https://github.com/radiantearth/stac-api-spec
