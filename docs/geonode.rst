.. _geonode:

GeoNode Configuration
======================

GeoNode (http://geonode.org/) is a platform for the management and publication of geospatial data. It brings together mature and stable open-source software projects under a consistent and easy-to-use interface allowing users, with little training, to quickly and easily share data and create interactive maps. GeoNode provides a cost-effective and scalable tool for developing information management systems.  GeoNode uses CSW as a cataloguing mechanism to query and present geospatial metadata.

pycsw supports binding to an existing GeoNode repository for metadata query.  The binding is read-only (transactions are not in scope, as GeoNode manages repository metadata changes in the application proper).

GeoNode Setup
-------------

pycsw is enabled and configured by default in GeoNode, so there are no additional steps required once GeoNode is setup.  See the ``CATALOGUE`` and ``PYCSW`` `settings.py entries`_ at http://docs.geonode.org/en/latest/developers/reference/django-apps.html#id1 for customizing pycsw within GeoNode.

The GeoNode plugin is managed outside of pycsw within the GeoNode project.

.. _`settings.py entries`: http://docs.geonode.org/en/latest/developers/reference/django-apps.html#id1
