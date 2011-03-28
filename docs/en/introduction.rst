.. _introduction:

Introduction
============

pycsw is an OGC CSW server implementation written in Python.

Features
========

- fully passes the `OGC CITE CSW`_ test suite (103 tests)
- realtime XML Schema validation
- full transactional capabilities
- flexible repository configuration
- federated discovery via distributed searching

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
| `Dublin Core`_    | 1.1        |
+-------------------+------------+
| `SOAP`_           | 1.2        |
+-------------------+------------+

Supported Operations
--------------------

.. csv-table::
  :header: Request,Optionality,Supported,HTTP method binding(s)

  GetCapabilities,mandatory,yes,GET (KVP) / POST (XML) / SOAP
  DescribeRecord,mandatory,yes,GET (KVP) / POST (XML) / SOAP
  GetRecords,mandatory,yes,GET (KVP) / POST (XML) / SOAP
  GetRecordById,optional,yes,GET (KVP) / POST (XML) / SOAP
  GetDomain,optional,yes,GET (KVP) / POST (XML) / SOAP
  Harvest,optional,pending,GET (KVP) / POST (XML) / SOAP
  Transaction,optional,pending,POST (XML) / SOAP

.. _`OGC CSW`: http://www.opengeospatial.org/standards/cat
.. _`OGC Filter`: http://www.opengeospatial.org/standards/filter
.. _`OGC OWS Common`: http://www.opengeospatial.org/standards/common
.. _`Dublin Core`: http://www.dublincore.org/
.. _`OGC CITE CSW`: http://cite.opengeospatial.org/test_engine/csw/2.0.2
.. _`SOAP`: http://www.w3.org/TR/soap/
