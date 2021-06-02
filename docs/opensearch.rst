.. _opensearch:

OpenSearch Support
==================

pycsw OpenSearch support is enabled by default.  There are two ways to access OpenSearch
depending on the deployment pattern chosen.

OARec deployment
----------------

.. code-block:: bash

  http://localhost:8000/opensearch

CSW legacy deployment
---------------------

HTTP requests must be specified with ``mode=opensearch`` in the base URL for OpenSearch requests, e.g.:

.. code-block:: bash

  http://localhost/pycsw/csw.py?mode=opensearch&service=CSW&version=2.0.2&request=GetCapabilities

This will return the Description document which can then be `autodiscovered <https://github.com/dewitt/opensearch/blob/master/opensearch-1-1-draft-6.md#Autodiscovery>`_.

OGC OpenSearch Geo and Time Extensions 1.0
------------------------------------------

pycsw supports the `OGC OpenSearch Geo and Time Extensions 1.0`_ standard via the following conformance classes:

- Core (GeoSpatial Service) ``{searchTerms}``, ``{geo:box}``, ``{startIndex}``, ``{count}``
- Temporal Search core ``{time:start}``, ``{time:end}``

Supported Query Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``q``
- ``time``
- ``bbox``

OGC OpenSearch Extension for Earth Observation
----------------------------------------------

pycsw supports the `OGC OpenSearch Extension for Earth Observation`_ standard via the following conformance classes:

- Core

Supported Query Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``eo:cloudCover``
- ``eo:instrument``
- ``eo:orbitDirection``
- ``eo:orbitNumber``
- ``eo:platform``
- ``eo:processingLevel``
- ``eo:productType``
- ``eo:sensorType``
- ``eo:snowCover``
- ``eo:spectralRange``

Mapping of non-19115 Queryable Mappings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following queryables are implemented as faceted keywords given they are not
implemented in generic geospatial metadata standards:

- ``eo:productType``
- ``eo:orbitNumber``
- ``eo:orbitDirection``
- ``eo:snowCover``
- ``eo:processingLevel``

This means metadata ingested into pycsw must have these fields implemented as keywords, as
per the examples below:

.. code-block:: xml

  <!-- ISO 19115 -->
  <gmd:keyword>
    <gco:CharacterString>eo:productType:S2MSI2A</gco:CharacterString>
  </gmd:keyword>
  <gmd:keyword>
    <gco:CharacterString>eo:orbitNumber:50</gco:CharacterString>
  </gmd:keyword>
  <gmd:keyword>
    <gco:CharacterString>eo:orbitDirection:DESCENDING</gco:CharacterString>
  </gmd:keyword>
  <gmd:keyword>
    <gco:CharacterString>eo:snowCover:0.0</gco:CharacterString>
  </gmd:keyword>
  <gmd:keyword>
    <gco:CharacterString>eo:procesingLevel:Level-2A</gco:CharacterString>
  </gmd:keyword>
 
.. code-block:: xml

  <!-- Dublin Core -->
  <dc:subject>eo:productType:S2MSI2A</dc:subject>
  <dc:subject>eo:orbitNumber:50</dc:subject>
  <dc:subject>eo:orbitDirection:DESCENDING</dc:subject>
  <dc:subject>eo:snowCover:0.0</dc:subject>
  <dc:subject>eo:procesingLevel:Level-2A</dc:subject>


OpenSearch Temporal Queries Implementation
------------------------------------------

By default, pycsw's OpenSearch temporal support will query the Dublin Core ``dc:date`` property as
a time instant/single point in time.  To enable temporal extent search, set ``profiles=apiso`` which
will query the temporal extents of a metadata record (``apiso:TempExtent_begin`` and ``apiso:TempExtent_end``).

At the HTTP API level, time is supported via either ``time=t1/t2`` or ``start=t1&stop=t2``.  If the
``time`` parameter is present, it will override the ``start`` and ``stop`` parameters respectively.

.. _`OGC OpenSearch Extension for Earth Observation`: https://docs.ogc.org/is/13-026r9/13-026r9.html
.. _`OGC OpenSearch Geo and Time Extensions 1.0`: https://www.ogc.org/standards/opensearchgeo
