.. _odc:

Open Data Catalog Configuration
===============================

Open Data Catalog (https://github.com/azavea/Open-Data-Catalog/) is an open data catalog based on Django, Python and PostgreSQL. It was originally developed for OpenDataPhilly.org, a portal that provides access to open data sets, applications, and APIs related to the Philadelphia region. The Open Data Catalog is a generalized version of the original source code with a simple skin. It is intended to display information and links to publicly available data in an easily searchable format. The code also includes options for data owners to submit data for consideration and for registered public users to nominate a type of data they would like to see openly available to the public.

pycsw supports binding to an existing Open Data Catalog repository for metadata query.  The binding is read-only (transactions are not in scope, as Open Data Catalog manages repository metadata changes in the application proper).

Open Data Catalog Setup
-----------------------

Open Data Catalog provides CSW functionality using pycsw out of the box (installing ODC will also install pycsw).  Settings are defined in https://github.com/azavea/Open-Data-Catalog/blob/master/OpenDataCatalog/settings.py#L165.

ODC settings must ensure that ``REGISTRY_PYCSW['repository']['source']`` is set to``hypermap.search.pycsw_repository``.

At this point, pycsw is able to read from the Open Data Catalog repository using the Django ORM.
