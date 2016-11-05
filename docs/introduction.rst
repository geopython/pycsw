.. _introduction:

Introduction
============

pycsw is an OGC CSW server implementation written in Python.

Features
========

- certified OGC `Compliant`_ and OGC Reference Implementation for both CSW 2.0.2 and CSW 3.0.0
- harvesting support for WMS, WFS, WCS, WPS, WAF, CSW, SOS
- implements `INSPIRE Discovery Services 3.0`_
- implements `ISO Metadata Application Profile 1.0.0`_
- implements `FGDC CSDGM Application Profile for CSW 2.0`_
- implements the Search/Retrieval via URL (`SRU`_) search protocol
- implements Full Text Search capabilities
- implements OGC OpenSearch Geo and Time Extensions
- implements Open Archives Initiative Protocol for Metadata Harvesting
- supports ISO, Dublin Core, DIF, FGDC, Atom and GM03 metadata models
- CGI or WSGI deployment
- Python 2 and 3 compatible
- simple configuration
- transactional capabilities (CSW-T)
- flexible repository configuration
- `GeoNode`_ connectivity
- `HHypermap`_ connectivity
- `Open Data Catalog`_ connectivity
- `CKAN`_ connectivity
- federated catalogue distributed searching
- realtime XML Schema validation
- extensible profile plugin architecture

Standards Support
-----------------

+-------------------+--------------+
| Standard          | Version(s)   |
+===================+==============+
| `OGC CSW`_        | 2.0.2, 3.0.0 |
+-------------------+--------------+
| `OGC Filter`_     | 1.1.0, 2.0.0 |
+-------------------+--------------+
| `OGC OWS Common`_ | 1.0.0, 2.0.0 |
+-------------------+--------------+
| `OGC GML`_        | 3.1.1        |
+-------------------+--------------+
| `OGC SFSQL`_      | 1.2.1        |
+-------------------+--------------+
| `Dublin Core`_    | 1.1          |
+-------------------+--------------+
| `SOAP`_           | 1.2          |
+-------------------+--------------+
| `ISO 19115`_      | 2003         |
+-------------------+--------------+
| `ISO 19139`_      | 2007         |
+-------------------+--------------+
| `ISO 19119`_      | 2005         |
+-------------------+--------------+
| `NASA DIF`_       | 9.7          |
+-------------------+--------------+
| `FGDC CSDGM`_     | 1998         |
+-------------------+--------------+
| `GM03`_           | 2.1          |
+-------------------+--------------+
| `SRU`_            | 1.1          |
+-------------------+--------------+
| `OGC OpenSearch`_ | 1.0          |
+-------------------+--------------+
| `OAI-PMH`_        | 2.0          |
+-------------------+--------------+

Supported Operations
--------------------

.. csv-table::
  :header: Request,Optionality,Supported,HTTP method binding(s)

  GetCapabilities,mandatory,yes,GET (KVP) / POST (XML) / SOAP
  DescribeRecord,mandatory,yes,GET (KVP) / POST (XML) / SOAP
  GetRecords,mandatory,yes,GET (KVP) / POST (XML) / SOAP
  GetRecordById,optional,yes,GET (KVP) / POST (XML) / SOAP
  GetRepositoryItem,optional,yes,GET (KVP)
  GetDomain,optional,yes,GET (KVP) / POST (XML) / SOAP
  Harvest,optional,yes,GET (KVP) / POST (XML) / SOAP
  UnHarvest,optional,no,
  Transaction,optional,yes,POST (XML) / SOAP

.. note::

  Asynchronous processing supported for GetRecords and Harvest requests (via ``csw:ResponseHandler``)

.. note::

  Supported Harvest Resource Types are listed in :ref:`transactions`

Supported Output Formats
------------------------

- XML (default)
- JSON

Supported Output Schemas
------------------------

- Dublin Core
- ISO 19139
- FGDC CSDGM
- NASA DIF
- Atom
- GM03

Supported Sorting Functionality
-------------------------------

- ogc:SortBy
- ascending or descending
- aspatial (queryable properties)
- spatial (geometric area)

Supported Filters
-----------------

Full Text Search
^^^^^^^^^^^^^^^^

- csw:AnyText

Geometry Operands
^^^^^^^^^^^^^^^^^

- gml:Point
- gml:LineString
- gml:Polygon
- gml:Envelope

.. note::

  Coordinate transformations are supported

Spatial Operators
^^^^^^^^^^^^^^^^^

- BBOX
- Beyond
- Contains
- Crosses
- Disjoint
- DWithin
- Equals
- Intersects
- Overlaps
- Touches
- Within

Logical Operators
^^^^^^^^^^^^^^^^^

- Between
- EqualTo
- LessThanEqualTo
- GreaterThan
- Like
- LessThan
- GreaterThanEqualTo
- NotEqualTo
- NullCheck

Functions
^^^^^^^^^
- length
- lower
- ltrim
- rtrim
- trim
- upper

.. _`OGC CSW`: http://www.opengeospatial.org/standards/cat
.. _`ISO Metadata Application Profile 1.0.0`: http://portal.opengeospatial.org/files/?artifact_id=21460
.. _`OGC Filter`: http://www.opengeospatial.org/standards/filter
.. _`OGC OWS Common`: http://www.opengeospatial.org/standards/common
.. _`OGC GML`: http://www.opengeospatial.org/standards/gml
.. _`OGC SFSQL`: http://www.opengeospatial.org/standards/sfs
.. _`Dublin Core`: http://www.dublincore.org/
.. _`OGC CITE CSW`: http://cite.opengeospatial.org/test_engine/csw/2.0.2
.. _`SOAP`: http://www.w3.org/TR/soap/
.. _`INSPIRE Discovery Services 3.0`: http://inspire.jrc.ec.europa.eu/documents/Network_Services/TechnicalGuidance_DiscoveryServices_v3.0.pdf
.. _`ISO 19115`: http://www.iso.org/iso/catalogue_detail.htm?csnumber=26020
.. _`ISO 19139`: http://www.iso.org/iso/catalogue_detail.htm?csnumber=32557
.. _`ISO 19119`: http://www.iso.org/iso/iso_catalogue/catalogue_tc/catalogue_detail.htm?csnumber=39890
.. _`NASA DIF`: http://gcmd.gsfc.nasa.gov/add/difguide/index.html
.. _`FGDC CSDGM`: http://www.fgdc.gov/metadata/csdgm
.. _`FGDC CSDGM Application Profile for CSW 2.0`: http://portal.opengeospatial.org/files/?artifact_id=16936
.. _`SRU`: http://www.loc.gov/standards/sru/
.. _`OGC OpenSearch`: http://www.opengeospatial.org/standards/opensearchgeo
.. _`GeoNode`: http://geonode.org/
.. _`HHypermap`: https://github.com/cga-harvard/HHypermap
.. _`Open Data Catalog`: https://github.com/azavea/Open-Data-Catalog/
.. _`CKAN`: http://ckan.org/
.. _`Compliant`: http://www.opengeospatial.org/resource/products/details/?pid=1374
.. _`OAI-PMH`: http://www.openarchives.org/OAI/openarchivesprotocol.html
.. _`GM03`: http://www.geocat.ch/internet/geocat/en/home/documentation/gm03.html
