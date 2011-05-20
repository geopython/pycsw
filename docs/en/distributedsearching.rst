.. _distributedsearching:

Distributed Searching
=====================

.. note::

   Your server must be able to make outgoing HTTP requests for this functionality.

pycsw has the ability to perform distributed searching against other CSW servers.  Distributed searching is disabled by default; to enable, ``server.federatedcatalogues`` must be set.  A CSW client must issue a GetRecords request with ``csw:DistributedSearch`` specified, along with an optional ``hopCount`` attribute (see subclause 10.8.4.13 of the CSW specification).  When enabled, pycsw will search all specified catalogues and return a unified set of search results to the client.  Due to the distributed nature of this functionality, requests will take extra time to process compared to queries against the local repository.
