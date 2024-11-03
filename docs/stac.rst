.. _stac:

SpatioTemporal Asset Catalog (STAC) API Support
===============================================

Versions
--------

pycsw supports `SpatioTemporal Asset Catalog API version v1.0.0`_ by default.

pycsw implements provides STAC support in the following manner:

* a pycsw repository is equivalent to a STAC collection
* pycsw metadata records are equivalent to STAC items

The STAC specification is designed with the same principles as OGC API - Records.


Implementation
--------------

The following design patterns are put forth for STAC support:

Collections
^^^^^^^^^^^

* any pycsw record that is ingested as a STAC Collection will appear on
  ``/stac/collections`` as a collection

Search
^^^^^^

* In addition to OGC API - Records ``/collections/metadata:main/items`` search,
  STAC API specific searches are realized via ``/stac/search``

Links and Assets
^^^^^^^^^^^^^^^^

STAC support will render links as follows:

* links that are enclosures will be encoded as STAC assets (in ``assets``)
* all other links remain as record links (in ``links``)

Request Examples
----------------

.. code-block:: bash

  # landing page
  http://localhost:8000/stac

  # collections
  http://localhost:8000/stac/collections

  # collection queries
  # query parameters can be combined (exclusive/AND)

  # landing page
  http://localhost:8000/stac
  # OpenAPI
  http://localhost:8000/stac/openapi
  # collections
  http://localhost:8000/stac/collections
  # collections query, full text search
  http://localhost:8000/stac/collections?q=sentinel
  # collections query, spatial query
  http://localhost:8000/stac/collections?bbox=-142,42,-52,84
  # collections query, full text search and spatial query
  http://localhost:8000/stac/collections?q=sentinel,bbox=-142,42,-52,84
  # collections query, limiting results
  http://localhost:8000/stac/collections?limit=2
  # collections query, spatial query
  # single collection
  http://localhost:8000/stac/collections/metadata:main
  # collection queryables, all records
  http://localhost:8000/stac/queryables
  # collection query, all records
  http://localhost:8000/stac/search
  # collection query, full text search
  http://localhost:8000/stac/search?q=lorem
  # collection query, spatial query
  http://localhost:8000/stac/search?bbox=-142,42,-52,84
  # collection query, temporal query
  http://localhost:8000/stac/search?datetime=2001-10-30/2007-10-30
  # collection query, temporal query, before
  http://localhost:8000/stac/search?datetime=../2007-10-30
  # collection query, temporal query, after
  http://localhost:8000/stac/search?datetime=2007-10-30/..
  # collection query, property query
  http://localhost:8000/stac/search?title=Lorem%20ipsum
  # collection query, CQL filter
  http://localhost:8000/stac/search?filter=title like "%lorem%"
  # collection query, limiting results
  http://localhost:8000/stac/search?limit=1
  # collection filter query, limiting results
  http://localhost:8000/stac/search?limit=1&collections=landsat
  # collection ids filter query, limiting results
  http://localhost:8000/stac/search?limit=1&ids=id1,id2
  # collection query, paging
  http://localhost:8000/stac/search?limit=10&offset=10
  # collection query, paging and sorting (default ascending)
  http://localhost:8000/stac/search?limit=10&offset=10&sortby=title
  # collection query, paging and sorting (descending)
  http://localhost:8000/stac/search?limit=10&offset=10&sortby=-title
  # collection item as GeoJSON
  http://localhost:8000/stac/collections/metadata:main/items/{itemId}

.. _`SpatioTemporal Asset Catalog API version v1.0.0`: https://github.com/radiantearth/stac-api-spec
