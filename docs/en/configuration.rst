.. _configuration:

Configuration
=============

pycsw's runtime configuration is defined by ``default.cfg``.  pycsw ships with a sample file ``default-sample.cfg``.  Copy the file to ``default.cfg`` and edit the following: 

.. note::

  Option keywords (like ``maxrecords``) are **case-sensitive**.

**[server]**

- **home**: the full filesystem path to pycsw
- **url**: the URL of the resulting service
- **mimetype**: the MIME type when returning HTTP responses
- **language**: the ISO 639-2 language and country code of the service (e.g. en-CA)
- **encoding**: the content type encoding (e.g. ISO-8859-1)
- **maxrecords**: the maximum number of records to return by default
- **loglevel**: the logging level (see http://docs.python.org/library/logging.html#logging-levels for more details)
- **logfile**: the full file path to the logfile
- **ogc_schemas_base**: base URL of OGC XML schemas tree file structure (default is http://schemas.opengis.net)
- **federatedcatalogues**: comma delimited list of CSW endpoints to be used for distributed searching, if requested by the client (see :ref:`distributedsearching` for more details)
- **xml_pretty_print**: whether to pretty print the output XML (``true`` or ``false``).  Default is ``false``
- **gzip_compresslevel**: gzip compression level, lowest is ``1``, highest is ``9``.  Default is ``9``
- **transactions**: whether to enable transactions (``true`` or ``false``).  Default is ``false``.  See :ref:`transactions` for more details
- **transactions_ips**: comma delimited list of IP addresses which can perform transactions.  See :ref:`transactions` for more details
- **profiles**: comma separated list of profiles to load at runtime (default is none).  See :ref:`profiles` for more details

**[metadata]**

- **identification_title**: the title of the service
- **identification_abstract**: some descriptive text about the service
- **identification_keywords**: a comma-seperated keyword list of keywords about the service
- **identification_fees**: fees associated with the service
- **identification_accessconstraints**: access constraints associated with the service
- **provider_name**: the name of the service provider
- **provider_url**: the URL of the service provider
- **contact_name**: the name of the provider contact
- **contact_position**: the position title of the provider contact
- **contact_address**: the address of the provider contact
- **contact_city**: the city of the provider contact
- **contact_stateorprovince**: the province or territory of the provider contact
- **contact_postalcode**: the postal code of the provider contact
- **contact_country**: the country of the provider contact
- **contact_phone**: the phone number of the provider contact
- **contact_fax**: the facsimile number of the provider contact
- **contact_email**: the email address of the provider contact
- **contact_url**: the URL to more information about the provider contact
- **contact_hours**: the hours of service to contact the provider
- **contact_instructions**: the how to contact the provider contact
- **contact_role**: the role of the provider contact

**[repository:*]**

Repository sections are namespaced to support definition of multiple repositories within configuration (e.g. ``[repository:cite]``, ``[repository:my_iso_records]``.  Names are up to the user, however the ``typename`` value within a repository section must be a supported information model (e.g. ``csw:Record``).

.. note::

  See :ref:`repository` for connecting your metadata repository.

- **enabled**: whether to include the repository at runtime (``true`` or ``false``)
- **typename**: the typename of the repository (csw:Record)
- **db**: the full file path to the metadata database, in database URL format (see http://www.sqlalchemy.org/docs/core/engines.html#database-urls for more details)
- **db_table**: the name of the metadata records table
- **cq_dc_title**: db table column name which maps to dc:title
- **cq_dc_creator**: db table column name which maps to dc:creator
- **cq_dc_subject**: db table column name which maps to dc:subject
- **cq_dct_abstract**: db table column name which maps to dct:abstract
- **cq_dc_publisher**: db table column name which maps to dc:publisher
- **cq_dc_contributor**: db table column name which maps to dc:contributor
- **cq_dct_modified**: db table column name which maps to dc:modified
- **cq_dc_type**: db table column name which maps to dc:type
- **cq_dc_format**: db table column name which maps to dc:format
- **cq_dc_identifier**: db table column name which maps to dc:identifier
- **cq_dc_source**: db table column name which maps to dc:source
- **cq_dc_language**: db table column name which maps to dc:language
- **cq_dc_relation**: db table column name which maps to dc:relation
- **cq_dc_rights**: db table column name which maps to dc:rights
- **cq_ows_BoundingBox**: db table column name which stores the geometry (in OGC `WKT <http://en.wikipedia.org/wiki/Well-known_text>`_ format)
- **cq_csw_AnyText**: db table column name which stores the full XML metadata record (for fulltext queries)
- **cq_dc_date**: db table column name which maps to dc:date

