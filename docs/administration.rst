.. _administration:

Administration
==============

pycsw administration is handled by the ``pycsw-admin.py`` utility.  ``pycsw-admin.py``
is installed as part of the pycsw install process and should be available in your
PATH.

.. note::
  Run ``pycsw-admin.py -h`` to see all administration operations and parameters

Metadata Repository Setup
-------------------------

pycsw supports the following databases:

- SQLite3
- PostgreSQL
- PostgreSQL with PostGIS enabled
- MySQL

.. note::
  The easiest and fastest way to deploy pycsw is to use SQLite3 as the backend.

.. note::
  PostgreSQL support includes support for PostGIS functions if enabled

.. note::
  If PostGIS (1.x or 2.x) is activated before setting up the pycsw/PostgreSQL database, then native PostGIS geometries will be enabled.

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

  $ pycsw-admin.py -c setup_db -f default.cfg

This will create the necessary tables and values for the repository.

The database created is an `OGC SFSQL`_ compliant database, and can be used with any implementing software.  For example, to use with `OGR`_:

.. code-block:: bash

  $ ogrinfo /path/to/records.db
  INFO: Open of 'records.db'
  using driver 'SQLite' successful.
  1: records (Polygon)
  $ ogrinfo -al /path/to/records.db
  # lots of output

.. note::
  If PostGIS is detected, the pycsw-admin.py script does not create the SFSQL tables as they are already in the database.


Loading Records
----------------

.. code-block:: bash

  $ pycsw-admin.py -c load_records -f default.cfg -p /path/to/records

This will import all ``*.xml`` records from ``/path/to/records`` into the database specified in ``default.cfg`` (``repository.database``).  Passing ``-r`` to the script will process ``/path/to/records`` recursively.  Passing ``-y`` to the script will force overwrite existing metadata with the same identifier.  Note that ``-p`` accepts either a directory path or single file.

.. note::
  Records can also be imported using CSW-T (see :ref:`transactions`).

Exporting the Repository
------------------------

.. code-block:: bash

  $ pycsw-admin.py -c export_records -f default.cfg -p /path/to/output_dir

This will write each record in the database specified in ``default.cfg`` (``repository.database``) to an XML document on disk, in directory ``/path/to/output_dir``.

Optimizing the Database
-----------------------

.. code-block:: bash

  $ pycsw-admin.py -c optimize_db -f default.cfg

.. note::
  This feature is relevant only for PostgreSQL and MySQL

Deleting Records from the Repository
------------------------------------

.. code-block:: bash

  $ pycsw-admin.py -c delete_records -f default.cfg

This will empty the repository of all records.

Database Specific Notes
-----------------------

PostgreSQL
^^^^^^^^^^

- if PostGIS is not enabled, pycsw makes uses of PL/Python functions.  To enable PostgreSQL support, the database user must be able to create functions within the database. In case of recent PostgreSQL versions (9.x), the PL/Python extension must be enabled prior to pycsw setup
- `PostgreSQL Full Text Search`_ is supported for ``csw:AnyText`` based queries.  pycsw creates a tsvector column based on the text from anytext column. Then pycsw creates a GIN index against the anytext_tsvector column.  This is created automatically in ``pycsw.admin.setup_db``.  Any query against `csw:AnyText` or `apiso:AnyText` will process using PostgreSQL FTS handling

PostGIS
^^^^^^^

- pycsw makes use of PostGIS spatial functions and native geometry data type.
- It is advised to install the PostGIS extension before setting up the pycsw database
- If PostGIS is detected, the pycsw-admin.py script will create both a native geometry column and a WKT column, as well as a trigger to keep both synchronized. 
- In case PostGIS gets disabled, pycsw will continue to work with the `WKT`_ column
- In case of migration from plain PostgreSQL database to PostGIS, the spatial functions of PostGIS will be used automatically
- When migrating from plain PostgreSQL database to PostGIS, in order to enable native geometry support, a "GEOMETRY" column named "wkb_geometry" needs to be created manually (along with the update trigger in ``pycsw.admin.setup_db``). Also the native geometries must be filled manually from the `WKT`_ field. Next versions of pycsw will automate this process

.. _custom_repository:

Mapping to an Existing Repository
---------------------------------

pycsw supports publishing metadata from an existing repository.  To enable this functionality, the default database mappings must be modified to represent the existing database columns mapping to the abstract core model (the default mappings are in ``pycsw/config.py:MD_CORE_MODEL``).

To override the default settings:

- define a custom database mapping based on ``etc/mappings.py``
- in ``default.cfg``, set ``repository.mappings`` to the location of the mappings.py file:

.. code-block:: none

  [repository]
  ...
  mappings=path/to/mappings.py

Note you can also reference mappings as a Python object as a dotted path:

.. code-block:: none

  [repository]
  ...
  mappings='path.to.pycsw_mappings'


See the :ref:`geonode`, :ref:`hhypermap`, and :ref:`odc` for further examples.

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
- ``pycsw:BoundingBox``: string of `WKT`_ or `EWKT`_ geometry

The following repository semantics exist if the attributes are specified:

- ``pycsw:Keywords``: comma delimited list of keywords
- ``pycsw:Links``: structure of links in the format "name,description,protocol,url[^,,,[^,,,]]"

Values of mappings can be derived from the following mechanisms:

- text fields
- Python datetime.datetime or datetime.date objects
- Python functions 

Further information is provided in ``pycsw/config.py:MD_CORE_MODEL``.

.. _`OGR`: http://www.gdal.org/ogr
.. _`OGC SFSQL`: http://www.opengeospatial.org/standards/sfs
.. _`WKT`: http://en.wikipedia.org/wiki/Well-known_text
.. _`EWKT`: http://en.wikipedia.org/wiki/Well-known_text#Variations
.. _`PostgreSQL Full Text Search`: http://www.postgresql.org/docs/9.2/static/textsearch.html
