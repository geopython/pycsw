.. _documentation:

.. toctree::
  :maxdepth: 2

=============================
pycsw |release| Documentation
=============================

:Author: Tom Kralidis
:Contact: tomkralidis at hotmail.com
:Release: |release|
:Date: |today|

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

Installation
============

Requirements
------------

pycsw requires the following supporting libraries:

- `lxml`_ (version >= 2.2.3) for XML support
- `SQLAlchemy`_ (version >= 0.0.5) for database bindings
- `Shapely`_ (version >= 1.2.8) for geometry support

Install
-------

:ref:`Download <download>` the latest version or fetch svn trunk:

.. code-block:: bash

  $ svn co https://pycsw.svn.sourceforge.net/svnroot/pycsw pycsw 

Configuration
=============

pycsw's runtime configuration is defined by ``default.cfg``.  pycsw ships with a sample file ``default.cfg-shipped``.  Copy the file to ``default.cfg`` and edit the following: 

.. note::

  Option keywords (like ``maxrecords``) are **case-sensitive**.

**[server]**

- **home**: the full file path to pycsw
- **url**: the URL of the resulting service
- **mimetype**: the MIME type when returning HTTP responses
- **language**: the ISO 639-2 language and country code of the service (e.g. en-CA)
- **encoding**: the content type encoding (e.g. ISO-8859-1)
- **maxrecords**: the maximum number of records to return by default
- **loglevel**: the logging level (see http://docs.python.org/library/logging.html#logging-levels for more details)
- **logfile**: the full file path to the logfile
- **ogc_schemas_base**: base URL of OGC XML schemas tree file structure (default is http://schemas.opengis.net).
- **federatedcatalogues**: comma delimited list of CSW endpoints to be used for distributed searching, if requested by the client (see :ref:`distributed-searching` for more details)

**[repository]**

.. note::

  See :ref:`metadata-repository-setup` for connecting your metadata repository.

- **db**: the full file path to the metadata database, in database URL format (see http://www.sqlalchemy.org/docs/core/engines.html#database-urls for more details)
- **table**: the name of the metadata records table

**[transactions]**

.. note::

  See :ref:`transactions` for more details.

- **enabled**: whether to enable transactions ('true' or 'false').  Default is 'false'
- **ips**: comma delimited list of IP addresses which can perform transactions

**[corequeryables]**

.. note::

  See :ref:`metadata-repository-setup` for connecting your metadata repository.

- **dc_title**: db table column name which maps to dc:title
- **dc_creator**: db table column name which maps to dc:creator
- **dc_subject**: db table column name which maps to dc:subject
- **dct_abstract**: db table column name which maps to dct:abstract
- **dc_publisher**: db table column name which maps to dc:publisher
- **dc_contributor**: db table column name which maps to dc:contributor
- **dct_modified**: db table column name which maps to dc:modified
- **dc_type**: db table column name which maps to dc:type
- **dc_format**: db table column name which maps to dc:format
- **dc_identifier**: db table column name which maps to dc:identifier
- **dc_source**: db table column name which maps to dc:source
- **dc_language**: db table column name which maps to dc:language
- **dc_relation**: db table column name which maps to dc:relation
- **dc_rights**: db table column name which maps to dc:rights
- **ows_BoundingBox**: db table column name which stores the geometry (in format 'minx,miny,maxx,maxy')
- **csw_AnyText**: db table column name which stores the full XML metadata record (for fulltext queries)

- **dc_date**: db table column name which maps to dc:date

**[identification]**

- **title**: the title of the service
- **abstract**: some descriptive text about the service
- **keywords**: a comma-seperated keyword list of keywords about the service
- **fees**: fees associated with the service
- **accessconstraints**: access constraints associated with the service

**[provider]**

- **name**: the name of the service provider
- **url**: the URL of the service provider

**[contact]**

- **name**: the name of the provider contact
- **position**: the position title of the provider contact
- **address**: the address of the provider contact
- **city**: the city of the provider contact
- **stateorprovince**: the province or territory of the provider contact
- **postalcode**: the postal code of the provider contact
- **country**: the country of the provider contact
- **phone**: the phone number of the provider contact
- **fax**: the facsimile number of the provider contact
- **email**: the email address of the provider contact
- **url**: the URL to more information about the provider contact
- **hours**: the hours of service to contact the provider
- **contactinstructions**: the how to contact the provider contact
- **role**: the role of the provider contact

.. _metadata-repository-setup:

Metadata Repository Setup
=========================

TODO

.. _distributed-searching:

Distributed Searching
=====================

pycsw has the ability to perform distributed searching against other CSW servers.  Distributed searching is disabled by default; to enable, ``server.federatedcatalogues`` must be set.  A CSW client must issue a GetRecords request with ``csw:DistributedSearch`` specified, along with an optional ``hopCount`` attribute (see subclause 10.8.4.13 of the CSW specification).  When enabled, pycsw will search all specified catalogues and return a unified set of search results to the client.  Due to the distributed nature of this functionality, requests will take extra time to process compared to queries against the local repository.  Distributed searching 

.. _transactions:

XML Sitemaps
============

`XML Sitemaps`_ can be generated by running ``sbin/gen_sitemap.py``:

.. code-block:: bash

  $ cd /path/to/pycsw
  $ export PYTHONPATH=`pwd`
  $ python ./sbin/gen_sitemap.xml > sitemap.xml

Save the output (to ``sitemap.xml``) to an an area on your web server (parallel to or above your pycsw install location) to enable web crawlers to index your repository. 

Transactions
============

pycsw has the ability to process CSW Harvest and Transaction requests.  Transactions are disabled by default; to enable, ``transactions.enabled`` must be set to ``true``.  Access to transactional functionality is limited to IP addresses which must be set in ``transactions.ips``.

Testing
=======

OGC CITE
--------

Compliance benchmarking is done via the OGC `Compliance & Interoperability Testing & Evaluation Initiative`_.  The pycsw `wiki <http://sourceforge.net/apps/trac/pycsw/wiki/OGCCITECompliance>`_ documents testing procedures and status.

Sample Requests
---------------

You can use the pycsw tester via your web browser to perform sample requests against your pycsw install.  The tester is located in the ``tester`` directory.

CSW Clients and Servers
=======================

Clients
-------

- `OWSLib`_
- `qgcsw`_ (`QGIS`_ plugin)

Servers
-------

- `deegree`_
- `eXcat`_
- `GeoNetwork opensource`_


Support
=======

The pycsw wiki is located at http://sourceforge.net/apps/trac/pycsw.

The pycsw source code is available at https://pycsw.svn.sourceforge.net/svnroot/pycsw.  You can browse the source code at at http://sourceforge.net/apps/trac/pycsw/browser.

You can find out about software metrics at the pycsw `ohloh`_ page.  pycsw is also registered on `CIA.vc`_.

The pycsw mailing list is the primary means for users and developers to exchange ideas, discuss improvements, and ask questions.  To subscribe, visit https://lists.sourceforge.net/lists/listinfo/pycsw-devel.

As well, you can visit pycsw on IRC on #pycsw at `freenode <http://freenode.net/>`_ for realtime discussion.

.. _license:

License
=======

Copyright (c) 2010 Tom Kralidis.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Committers
==========

.. include:: ../../COMMITTERS.txt

.. _`Open Geospatial Consortium`: http://www.opengeospatial.org/
.. _`OGC CSW`: http://www.opengeospatial.org/standards/cat
.. _`OGC Filter`: http://www.opengeospatial.org/standards/filter
.. _`OGC OWS Common`: http://www.opengeospatial.org/standards/common
.. _`NASA DIF`: http://gcmd.nasa.gov/User/difguide/ 
.. _`FGDC CSDGM`: http://www.fgdc.gov/metadata/csdgm
.. _`ISO 19115`: http://www.iso.org/iso/catalogue_detail.htm?csnumber=26020
.. _`ISO 19139`: http://www.iso.org/iso/catalogue_detail.htm?csnumber=32557
.. _`Dublin Core`: http://www.dublincore.org/
.. _`lxml`: http://lxml.de/
.. _`SQLAlchemy`: http://www.sqlalchemy.org/
.. _`Shapely`: http://trac.gispython.org/lab/wiki/Shapely
.. _`ohloh`: http://www.ohloh.net/p/pycsw
.. _`Compliance & Interoperability Testing & Evaluation Initiative`: http://cite.opengeospatial.org/
.. _`OWSLib`: http://trac.gispython.org/lab/wiki/OwsLib
.. _`qgcsw`: http://sourceforge.net/apps/trac/qgiscommunitypl/wiki/qgcsw
.. _`QGIS`: http://qgis.org/
.. _`deegree`: http://www.deegree.org/
.. _`eXcat`: http://gdsc.nlr.nl/gdsc/en/tools/excat
.. _`GeoNetwork opensource`: http://geonetwork-opensource.org/
.. _`OGC CITE CSW`: http://cite.opengeospatial.org/test_engine/csw/2.0.2
.. _`SOAP`: http://www.w3.org/TR/SOAP/
.. _`CIA.vc`: http://cia.vc/stats/project/pycsw
.. _`XML Sitemaps`: http://sitemaps.org/
