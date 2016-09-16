.. _hhypermap:

HHypermap Configuration
=======================

HHypermap (Harvard Hypermap) Registry (https://github.com/cga-harvard/HHypermap) is an application that manages OWS, Esri REST, and other types of map service harvesting, and maintains uptime statistics for services and layers. HHypermap Registry will publish to HHypermap Search (based on Lucene) which provides a fast search and visualization environment for spatio-temporal materials.

HHypermap uses CSW as a cataloguing mechanism to ingest, query and present geospatial metadata.

pycsw supports binding to an existing HHypermap repository for metadata query.

HHypermap Setup
---------------

pycsw is enabled and configured by default in HHypermap, so there are no additional steps required once HHypermap is setup.  See the ``REGISTRY_PYCSW`` `hypermap/settings.py entries`_ for customizing pycsw within HHypermap.

The HHypermap plugin is managed outside of pycsw within the HHypermap project.  HHypermap settings must ensure that ``REGISTRY_PYCSW['repository']['source']`` is set to``hypermap.search.pycsw_repository``.

.. _`hypermap/settings.py entries`: https://github.com/cga-harvard/HHypermap/blob/master/hypermap/settings.py
