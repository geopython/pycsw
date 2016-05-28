.. _hhypermap:

HHypermap Configuration
=======================

HHypermap (Harvard Hypermap) Supervisor (https://github.com/cga-harvard/HHypermap) is an application that manages OWS, Esri REST, and other types of map service harvesting, and maintains uptime statistics for services and layers. HHypermap Supervisor will publish to HHypermap Search (based on Lucene) which provides a fast search and visualization environment for spatio-temporal materials. 

HHypermap uses CSW as a cataloguing mechanism to ingest, query and present geospatial metadata.

pycsw supports binding to an existing HHypermap repository for metadata query.

HHypermap Setup
---------------

pycsw is enabled and configured by default in HHypermap, so there are no additional steps required once HHypermap is setup.  See the ``PYCSW`` `settings/default.py entries`_ for customizing pycsw within HHypermap.

.. _`settings/default.py entries`: https://github.com/cga-harvard/HHypermap/blob/master/hypermap/settings/default.py#L197
