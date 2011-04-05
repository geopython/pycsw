.. _configuration:

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
- **federatedcatalogues**: comma delimited list of CSW endpoints to be used for distributed searching, if requested by the client (see :ref:`distributedsearching` for more details)
- **xml_pretty_print**: whether to pretty print the output XML (``true`` or ``false``).  Default is ``false``
- **gzip_compresslevel**: gzip compression level, lowest is ``1``, highest is ``9``.  Default is ``9``
- **transactions**: whether to enable transactions (``true`` or ``false``).  Default is ``false``
- **transactions_ips**: comma delimited list of IP addresses which can perform transactions

.. note::

  See :ref:`transactions` for more details.

**[repository]**

.. note::

  See :ref:`repository` for connecting your metadata repository.

- **db**: the full file path to the metadata database, in database URL format (see http://www.sqlalchemy.org/docs/core/engines.html#database-urls for more details)
- **table**: the name of the metadata records table

**[corequeryables]**

.. note::

  See :ref:`repository` for connecting your metadata repository.

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
