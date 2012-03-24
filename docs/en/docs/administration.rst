.. _administration:

Administration
==============

pycsw administration is handled by ``sbin/pycsw-admin.py``.

.. note::
  Run ``sbin/pycsw-admin.py -h`` to see all administration operations and parameters

Metadata Repository Setup
-------------------------

pycsw supports the following databases:

- SQLite3
- PostgreSQL
- MySQL

.. note::
  The easiest and fastest way to deploy pycsw is to use SQLite3 as the backend.

To expose your geospatial metadata via pycsw, perform the following actions:

- setup the database
- import metadata
- publish the repository

Supported Information Models
----------------------------

By default, pycsw supports the ``csw:Record`` information model.

.. note::
  See :ref:`profiles` for information on enabling profiles

Setting up the Database
-----------------------

.. code-block:: bash

  $ cd /path/to/pycsw
  $ export PYTHONPATH=`pwd` 
  $ python ./sbin/pycsw-admin.py -c setup_db -f default.cfg

This will create the necessary tables and values for the repository.

The database created is an `OGC SFSQL`_ compliant database, and can be used with any implementing software.  For example, to use with `OGR`_:

.. code-block:: bash

  $ ogrinfo /path/to/records.db
  INFO: Open of 'records.db'
  using driver 'SQLite' successful.
  1: records (Polygon)
  $ ogrinfo -al /path/to/records.db
  # lots of output

Loading Records
----------------

.. code-block:: bash

  $ python ./sbin/pycsw-admin.py -c load_records -f default.cfg -p /path/to/records

This will import all ``*.xml`` records from ``/path/to/records`` into the database specified in ``default.cfg`` (``repository.database``).  Passing ``-r`` to the script will process ``/path/to/records`` recursively.

.. note::
  Records can also be imported using CSW-T (see :ref:`transactions`).

Exporting the Repository
------------------------

.. code-block:: bash

  $ python ./sbin/pycsw-admin.py -c export_records -f default.cfg -p /path/to/output_dir

This will write each record in the database specified in ``default.cfg`` (``repository.database``) to an XML document on disk, in directory ``/path/to/output_dir``.

Optimizing the Database
-----------------------

.. code-block:: bash

  $ python ./sbin/pycsw-admin.py -c optimize_db -f default.cfg

Database Specific Notes
-----------------------

PostgreSQL
^^^^^^^^^^

- pycsw makes uses of PL/Python functions.  To enable PostgreSQL support, the database user must be able to create functions within the database.

.. _custom_repository:

Mapping to an Existing Repository
---------------------------------

pycsw supports publishing metadata from an existing repository.  To enable this functionality, the default database mappings must be modified to represent the existing database columns mapping to the abstract core model (the default mappings are in ``server/config.py:MD_CORE_MODEL``).

To override the default settings:

- define a custom database mapping based on ``etc/mappings.py``
- in ``default.cfg``, set ``repository.mappings`` to the location of the mappings.py file:

.. code-block:: none

  [repository]
  ...
  mappings=path/to/mappings.py

Existing Repository Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

pycsw requires certain repository attributes and semantics to exist in any repository to operate as follows:

- ``pycsw:Identifier``: unique identifier
- ``pycsw:Typename``: typename for the metadata; typically the value of the root element tag (e.g. ``csw:Record``, ``gmd:MD_Metadata``)
- ``pycsw:Schema``: schema for the metadata; typically the target namespace (e.g. ``http://www.opengis.net/cat/csw/2.0.2``, ``http://www.isotc211.org/2005/gmd``)
- ``pycsw:InsertDate``: date of insertion
- ``pycsw:XML``: full XML representation
- ``pycsw:AnyText``: bag of XML element text values, used for full text search.  Realized with the following design pattern:

  - capture all XML element and attribute values
  - store in repository
- ``pycsw:BoundingBox``: string of WKT or EWKT geometry

The following repository semantics exist if the attributes are specified:

- ``pycsw:Keywords``: comma delimited list of keywords
- ``pycsw:Links``: structure of links in the format "name,description,protocol,url[^,,,[^,,,]]"

Values of mappings can be derived from the following mechanisms:

- text fields
- Python datetime objects
- Python functions 

Further information is provided in ``server/config.py:MD_CORE_MODEL``.

.. _`OGR`: http://www.gdal.org/ogr
.. _`OGC SFSQL`: http://www.opengeospatial.org/standards/sfs
