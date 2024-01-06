.. _administration:

Administration
==============

pycsw administration is handled by the ``pycsw-admin.py`` utility.  ``pycsw-admin.py``
is installed as part of the pycsw install process and should be available in your
PATH.

.. note::
  Run ``pycsw-admin.py --help`` to see all administration operations and parameters

Metadata Repository Setup
-------------------------

pycsw supports the following databases:

- SQLite3
- PostgreSQL (without PostGIS)
- PostgreSQL with PostGIS enabled
- MySQL

.. note::
  The easiest and fastest way to deploy pycsw is to use SQLite3 as the backend. To use an SQLite
  in-memory database, in the pycsw configuration, set `repository.database` to ``sqlite://``.

.. note::
  PostgreSQL support includes support for PostGIS functions if enabled

.. note::
  If PostGIS is activated before setting up the pycsw/PostgreSQL database, then native PostGIS geometries will be enabled.

To expose your geospatial metadata via pycsw, perform the following actions:

- setup the database
- import metadata
- publish the repository

Supported Information Models
----------------------------

By default, pycsw's API  supports the core OGC API - Records and CSW Record information models.  From
the database perspective, the pycsw metadata model is loosely based on ISO 19115 and is
able to transform to other formats as part of transformation during OGC API - Records/CSW requests.

.. note::
  See :ref:`profiles` for information on enabling profiles

.. note::
  See :ref:`metadata-model-reference` for detailed information on pycsw's internal metadata model

Setting up the Database
-----------------------

.. code-block:: bash

  pycsw-admin.py setup-repository --config default.yml

This will create the necessary tables and values for the repository.

The database created is an `OGC SFSQL`_ compliant database, and can be used with any implementing software.  For example, to use with `GDAL`_:

.. code-block:: bash

  ogrinfo /path/to/records.db
  INFO: Open of 'records.db'
  using driver 'SQLite' successful.
  1: records (Polygon)
  ogrinfo -al /path/to/records.db
  # lots of output

.. note::
  If PostGIS is detected, the ``pycsw-admin.py`` script does not create the SFSQL tables as they are already in the database.


Loading Records
----------------

.. code-block:: bash

  pycsw-admin.py load-records --config default.yml --path /path/to/records

This will import all ``*.xml`` records from ``/path/to/records`` into the database specified in ``default.yml`` (``repository.database``).  Passing ``-r`` to the script will process ``/path/to/records`` recursively.  Passing ``-y`` to the script will force overwrite existing metadata with the same identifier.  Note that ``-p`` accepts either a directory path or single file.

.. note::
  Records can also be imported using CSW-T (see :ref:`transactions`).

Exporting the Repository
------------------------

.. code-block:: bash

  pycsw-admin.py export-records --config default.yml --path /path/to/output_dir

This will write each record in the database specified in ``default.yml`` (``repository.database``) to an XML document on disk, in directory ``/path/to/output_dir``.

Optimizing the Database
-----------------------

.. code-block:: bash

  pycsw-admin.py optimize-db --config default.yml
  pycsw-admin.py rebuild-db-indexes --config default.yml

.. note::
  This feature is relevant only for PostgreSQL and MySQL

Deleting Records from the Repository
------------------------------------

.. code-block:: bash

  pycsw-admin.py delete-records --config default.yml

This will empty the repository of all records.

Database Specific Notes
-----------------------

PostgreSQL
^^^^^^^^^^

-  To enable PostgreSQL support, the database user must be able to create functions within the database.
- `PostgreSQL Full Text Search`_ is supported for ``csw:AnyText`` based queries.  pycsw creates a tsvector column based on the text from anytext column. Then pycsw creates a GIN index against the anytext_tsvector column.  This is created automatically in ``pycsw.core.repository.setup``.  Any query against the OGC API - Records ``q`` parameter or CSW `csw:AnyText` or `apiso:AnyText` will process using PostgreSQL FTS handling

PostGIS
^^^^^^^

- pycsw makes use of PostGIS spatial functions and native geometry data type.
- It is advised to install the PostGIS extension before setting up the pycsw database
- If PostGIS is detected, the ``pycsw-admin.py`` script will create both a native geometry column and a WKT column, as well as a trigger to keep both synchronized
- In case PostGIS gets disabled, pycsw will continue to work with the `WKT`_ column
- In case of migration from plain PostgreSQL database to PostGIS, the spatial functions of PostGIS will be used automatically
- When migrating from plain PostgreSQL database to PostGIS, in order to enable native geometry support, a "GEOMETRY" column named "wkb_geometry" needs to be created manually (along with the update trigger in ``pycsw.core.repository.setup``). Also the native geometries must be filled manually from the `WKT`_ field. Next versions of pycsw will automate this process

.. _custom_repository:

Mapping to an Existing Repository
---------------------------------

pycsw supports publishing metadata from an existing repository.  To enable this functionality, the default database
mappings must be modified to represent the existing database columns mapping to the abstract core model (the default
mappings are in ``pycsw/core/config.py:StaticContext.md_core_model``).

To override the default settings:

- define a custom database mapping based on ``etc/mappings.py``
- in ``default.yml``, set ``repository.mappings`` to the location of the mappings.py file:

.. code-block:: yaml

  repository:
      ...
      mappings: path/to/mappings.py

Note you can also reference mappings as a Python object as a dotted path:

.. code-block:: yaml

  repository:
      ...
      mappings: path.to.pycsw_mappings


See the :ref:`geonode`, :ref:`hhypermap`, and :ref:`odc` for further examples.

.. _existing-repository-requirements:

Existing Repository Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

pycsw requires certain repository attributes and semantics to exist in any repository to operate as follows:

- ``pycsw:Identifier``: unique identifier
- ``pycsw:Typename``: typename for the metadata; typically the value of the root element tag (e.g. ``csw:Record``, ``gmd:MD_Metadata``)
- ``pycsw:Schema``: schema for the metadata; typically the target namespace (e.g. ``http://www.opengis.net/cat/csw/2.0.2``, ``http://www.isotc211.org/2005/gmd``)
- ``pycsw:InsertDate``: date of insertion
- ``pycsw:XML``: full XML representation (deprecated; will be removed in a future release)
- ``pycsw:Metadata``: full metadata representation
- ``pycsw:MetadataType``: media type of metadata representation
- ``pycsw:AnyText``: bag of XML element text values, used for full text search.  Realized with the following design pattern:

  - capture all XML element and attribute values
  - store in repository
- ``pycsw:BoundingBox``: string of `WKT`_ or `EWKT`_ geometry

The following repository semantics exist if the attributes are specified:

- ``pycsw:Keywords``: comma delimited list of keywords
- ``pycsw:Themes``: Text field of JSON list of objects with properties ``concepts``, ``scheme``

.. code-block:: json

   [
     {
       "concepts": [
         {
           "id": "atmosphericComposition"
         },
         {
           "id": "pollution"
         },
         {
           "id": "observationPlatform"
         },
         {
           "id": "rocketSounding"
         }
       ],
       "scheme": "https://wis.wmo.int/2012/codelists/WMOCodeLists.xml#WMO_CategoryCode"
     }
   ]

- ``pycsw:Contacts``: Text field of JSON list of objects with properties as per the OGC API - Records party definition

.. code-block:: json

   [
     {
       "name": "contact",
       "individual": "Lastname, Firstname",
       "positionName": "Position Title",
       "contactInfo": {
         "phone": {
           "office": "+xx-xxx-xxx-xxxx"
         },
         "email": {
           "office": "you@example.org"
         },
         "address": {
           "office": {
             "deliveryPoint": "Mailing Address",
             "city": "City",
             "administrativeArea": "Administrative Area",
             "postalCode": "Zip or Postal Code",
             "country": "COuntry"
           },
           "onlineResource": {
             "href": "Contact URL"
           }
         },
         "hoursOfService": "Hours of Service",
         "contactInstructions": "During hours of service.  Off on weekends",
         "url": {
           "rel": "canonical",
           "type": "text/html",
           "href": "https://example.org"
         }
       },
       "roles": [
         {
           "name": "pointOfContact"
         }
       ]
     }
   ]

- ``pycsw:Links``: Text field of JSON list of objects with properties ``name``, ``description``, ``protocol``, ``url``

.. code-block:: json

   [
     {
       "name": "foo",
       "description": "bar",
       "protocol": "OGC:WMS",
       "url": "https://example.org/wms"
     }
  ]

.. note::
  The ``pycsw:Links`` field should be a text type, not a JSON object type

- ``pycsw:Bands``: Text field of JSON list of dicts with properties: ``name``, ``units``, ``min``, ``max``

.. code-block:: json

   [
     {
       "name": "B1",
       "units": "nm",
       "min": 0.1,
       "max": 0.333
     }
  ]

.. note::
  The ``pycsw:Bands`` field should be a text type, not a JSON object type

Values of mappings can be derived from the following mechanisms:

- text fields
- Python datetime.datetime or datetime.date objects
- Python functions 

Further information is provided in ``pycsw/config.py:MD_CORE_MODEL``.


.. note::
  See :ref:`metadata-model-reference` for detailed information on pycsw's internal metadata model

Using a SQL View as the repository table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your pre-existing database stores information in a normalized fashion, *i.e.* distributed on multiple tables rather
than on a single table (which is what pycsw expects by default), you have the option to create a DB view and use that
as pycsw's repository.

As a practical example, lets say you have a `CKAN`_ project which you would like to also provide pycsw integration with.
CKAN stores dataset-related information over multiple tables:

- ``package`` - has base metadata fields for each dataset;
- ``package_extra`` - additional custom metadata fields, depending on the user's metadata schema;
- ``package_tag`` - dataset_related keywords;
- ``tag`` - dataset_related keywords;
- ``group`` - details about a dataset's owner organization;
- etc.

One way to adapt such a DB structure to be able to integrate with pycsw is to create a `PostgreSQL Materialized View`_.
For example:

.. code-block:: SQL

  CREATE MATERIALIZED VIEW IF NOT EXISTS my_pycsw_view AS
      WITH cte_extras AS (
          SELECT
                 p.id,
                 p.title,
                 g.title AS org_name,
                 json_object_agg(pe.key, pe.value) AS extras,
                 array_agg(DISTINCT t.name) AS tags
                 -- remaining columns omitted for brevity
          FROM package AS p
              JOIN package_extra AS pe ON p.id = pe.package_id
              JOIN "group" AS g ON p.owner_org = g.id
              JOIN package_tag AS pt ON p.id = pt.package_id
              JOIN tag AS t on pt.tag_id = t.id
          WHERE p.state = 'active'
           AND p.private = false
          GROUP BY p.id, g.title
      )
      SELECT
             c.id AS identifier,
             c.title AS title,
             c.org_name AS organization,
             ST_GeomFromGeoJSON(c.extras->>'spatial')::geometry(Polygon, 4326) AS geom,
             c.extras->>'reference_date' AS date,
             concat_ws(', ', VARIADIC c.tags) AS keywords
             -- remaining columns omitted for brevity
      FROM cte_extras AS c
  WITH DATA;

Creating this SQL view in the database means that all we now have the CKAN dataset information all on a single flat
table, ready for pycsw to integrate with.

A crucial setup that is required in order for SQL Views to be usable by pycsw is to include the additional
``column_constraints`` property in your custom mappings. This property is used to specify which column(s) should
function as the primary key of the SQL View:

.. code-block:: python

    # contents of my_custom_pycsw_mappings.py
    from sqlalchemy.schema import PrimaryKeyConstraint

    MD_CORE_MODEL = {
        "column_constraints": (PrimaryKeyConstraint("identifier"),),
        "typename": "pycsw:CoreMetadata",
        "outputschema": "http://pycsw.org/metadata",
        "mappings": {
            "pycsw:Identifier": "identifier",
            # remaining mappings omitted for brevity

The above code snippet demonstrates how you could instruct sqlalchemy, which is what pycsw uses to interface with
the DB, that the ``identifier`` column of the SQL view should be assumed to be the primary key of the table.

Finally, we can configure pycsw with the path to the custom mappings and the name of the SQL view:

.. code-block:: yaml

    # file: pycsw.yml

    repository:
        database: postgresql://${DB_USERNAME}:${DB_PASSWORD}@${DB_HOST}/${DB_NAME}
        mappings: /path/to/my_custom_pycsw_mappings.py
        table: my_pycsw_view


.. _`GDAL`: https://www.gdal.org
.. _`OGC SFSQL`: https://www.ogc.org/standards/sfs
.. _`WKT`: https://en.wikipedia.org/wiki/Well-known_text
.. _`EWKT`: https://en.wikipedia.org/wiki/Well-known_text#Variations
.. _`PostgreSQL Full Text Search`: https://www.postgresql.org/docs/current/textsearch.html
.. _`CKAN`: https://ckan.org/
.. _`PostgreSQL Materialized View`: https://www.postgresql.org/docs/current/sql-creatematerializedview.html
