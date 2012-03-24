.. _geonode:

GeoNode Configuration
======================

GeoNode (http://geonode.org/) is a platform for the management and publication of geospatial data. It brings together mature and stable open-source software projects under a consistent and easy-to-use interface allowing users, with little training, to quickly and easily share data and create interactive maps. GeoNode provides a cost-effective and scalable tool for developing information management systems.  GeoNode uses CSW as a cataloguing mechanism to query and present geospatial metadata.

pycsw supports binding to an existing GeoNode repository for metadata query.  The binding is read-only (transactions are not in scope, as GeoNode manages repository metadata changes in the application proper).

GeoNode Setup
-------------

To connect pycsw to GeoNode's repository, the following steps are required:

- :ref:`mapping <custom_repository>` GeoNode queryables to pycsw's queryables model
- updating the :ref:`configuration` to specify GeoNode as the source repository

Mapping Queryables
^^^^^^^^^^^^^^^^^^

- create a ``mappings.py`` file (a GeoNode sample is in ``server/plugins/repository/geonode/mappings.py``), which associates GeoNode's ResourceBase attributes to pycsw's queryables

Updating Configuration
^^^^^^^^^^^^^^^^^^^^^^

- in ``default.cfg``:

 - set ``repository.source`` to ``geonode`` (``repository.database`` is not required in this context)
 - set ``repository.mappings`` to ``/path/to/mappings.py`` (``repository.database`` is not required in this context)

At this point, pycsw is able to read from the GeoNode repository using the Django ORM.
