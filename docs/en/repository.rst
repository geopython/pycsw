.. _repository:

Metadata Repository Setup
=========================

pycsw ships with SQLite support (additional databases will be supported in a future release).

To expose your geospatial metadata via pycsw, perform the following actions:

- setup the database
- import metadata
- configure the db connection

Supported Information Models
----------------------------

By default, pycsw supports the ``csw:Record`` information model.  When specifying a ``[repository:*]`` section with ``typename=csw:Record``, the following options are required:

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

Setting up the Database
-----------------------

.. code-block:: bash

  $ cd /path/to/pycsw
  $ export PYTHONPATH=`pwd` 
  $ python ./sbin/setup_db.py ./etc/schemas/sql/records.ddl records.db

Importing Metadata
------------------

.. code-block:: bash

  $ python ./sbin/load_csw_records.py /path/to/records records.db

This will import all ``*.xml`` records from ``/path/to/records`` into ``records.db``.

Configuring the Database Connection
-----------------------------------

By default, ``default-sample.cfg`` contains all required binding information.  If you are setting up your database as per above,
the default configuration needs only the ``repository.db`` value to be updated.  Otherwise, you can map your own database table and columns.

See :ref:`configuration`, (**[repository:*]**) for more information.
