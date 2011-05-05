.. _introduction:

Introduction
============

pycsw is an OGC CSW server implementation written in Python.

Features
========

- fully passes the `OGC CITE CSW`_ test suite (103 tests)
- implements `INSPIRE Discovery Services 3.0`_
- implements `ISO Metadata Application Profile 1.0.0`_
- transactional capabilities (pending)
- flexible repository configuration
- federated catalogue distributed searching
- realtime XML Schema validation
- extensible profile plugin architecture

Standards Support
-----------------

+-------------------+------------+
| Standard          | Version(s) |
+===================+============+
| `OGC CSW`_        | 2.0.2      |
+-------------------+------------+
| `OGC Filter`_     | 1.1.0      |
+-------------------+------------+
| `OGC OWS Common`_ | 1.0.0      |
+-------------------+------------+
| `OGC GML`_        | 3.1.1      |
+-------------------+------------+
| `Dublin Core`_    | 1.1        |
+-------------------+------------+
| `SOAP`_           | 1.2        |
+-------------------+------------+
| `ISO 19115`_      | 2003       |
+-------------------+------------+
| `ISO 19139`_      | 2007       |
+-------------------+------------+
| `ISO 19119`_      | 2005       |
+-------------------+------------+

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
  Harvest,optional,pending,GET (KVP) / POST (XML) / SOAP
  Transaction,optional,pending,POST (XML) / SOAP

Supported Filters
-----------------

Geometry Operands
^^^^^^^^^^^^^^^^^

- gml:Point
- gml:LineString
- gml:Polygon
- gml:Envelope

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

.. _`OGC CSW`: http://www.opengeospatial.org/standards/cat
.. _`ISO Metadata Application Profile 1.0.0`: http://portal.opengeospatial.org/files/?artifact_id=21460
.. _`OGC Filter`: http://www.opengeospatial.org/standards/filter
.. _`OGC OWS Common`: http://www.opengeospatial.org/standards/common
.. _`OGC GML`: http://www.opengeospatial.org/standards/gml
.. _`Dublin Core`: http://www.dublincore.org/
.. _`OGC CITE CSW`: http://cite.opengeospatial.org/test_engine/csw/2.0.2
.. _`SOAP`: http://www.w3.org/TR/soap/
.. _`INSPIRE Discovery Services 3.0`: http://inspire.jrc.ec.europa.eu/documents/Network_Services/TechnicalGuidance_DiscoveryServices_v3.0.pdf
.. _`ISO 19115`: http://www.iso.org/iso/catalogue_detail.htm?csnumber=26020
.. _`ISO 19139`: http://www.iso.org/iso/catalogue_detail.htm?csnumber=32557
.. _`ISO 19119`: http://www.iso.org/iso/iso_catalogue/catalogue_tc/catalogue_detail.htm?csnumber=39890
