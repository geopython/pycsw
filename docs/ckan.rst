.. _ckan:

CKAN Configuration
==================

CKAN (http://ckan.org) is a powerful data management system that makes data accessible – by providing tools to streamline publishing, sharing, finding and using data. CKAN is aimed at data publishers (national and regional governments, companies and organizations) wanting to make their data open and available.

`ckanext-spatial`_ is CKAN's geospatial extension.  The extension adds a spatial field to the default CKAN dataset schema, using PostGIS as the backend. This allows to perform spatial queries and display the dataset extent on the frontend. It also provides harvesters to import geospatial metadata into CKAN from other sources, as well as commands to support the CSW standard. Finally, it also includes plugins to preview spatial formats such as GeoJSON.

CKAN Setup
----------

Installation and configuration Instructions are provided as part of the ckanext-spatial `documentation`_.

.. _`ckanext-spatial`: https://github.com/okfn/ckanext-spatial
.. _`documentation`: http://docs.ckan.org/projects/ckanext-spatial/en/latest/csw.html
