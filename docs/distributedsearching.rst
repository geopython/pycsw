.. _distributedsearching:

Distributed Searching
=====================

.. note::

   - in CSW mode, distributed search must be configured against remote CSW services
   - in OGC API - Records mode, distributed search must be configured against remote OGC API - Records services

.. note::

   Your server must be able to make outgoing HTTP requests for this functionality.

CSW 2 / 3
---------

pycsw has the ability to perform distributed searching against other CSW servers.  Distributed searching is disabled by default; to enable, ``federatedcatalogues`` must be set.  A CSW client must issue a GetRecords request with ``csw:DistributedSearch`` specified, along with an optional ``hopCount`` attribute (see subclause 10.8.4.13 of the CSW specification).  When enabled, pycsw will search all specified catalogues and return a unified set of search results to the client.  Due to the distributed nature of this functionality, requests will take extra time to process compared to queries against the local repository.

Scenario: Federated Search
^^^^^^^^^^^^^^^^^^^^^^^^^^

pycsw deployment with 3 configurations (CSW-1, CSW-2, CSW-3), subsequently providing three (3) endpoints.  Each endpoint is based on an opaque metadata repository (based on theme/place/discipline, etc.).  Goal is to perform a single search against all endpoints.
 
pycsw realizes this functionality by supporting :ref:`alternate configurations <alternate-configurations>`, and exposes the additional CSW endpoint(s) with the following design pattern:
 
CSW-1: ``http://localhost/pycsw/csw.py?config=CSW-1.yml``
 
CSW-2: ``http://localhost/pycsw/csw.py?config=CSW-2.yml``
 
CSW-3: ``http://localhost/pycsw/csw.py?config=CSW-3.yml``
 
...where the ``*.yml`` configuration files are configured for each respective metadata repository.  The above CSW endpoints can be interacted with as usual.
 
To federate the discovery of the three (3) portals into a unified search, pycsw realizes this functionality by deploying an additional configuration which acts as the superset of CSW-1, CSW-2, CSW-3:

CSW-all: ``http://localhost/pycsw/csw.py?config=CSW-all.yml``

This allows the client to invoke one (1) CSW GetRecords request, in which the CSW endpoint spawns the same GetRecords request to 1..n distributed CSW endpoints.  Distributed CSW endpoints are advertised in CSW Capabilities XML via ``ows:Constraint``:

.. code-block:: xml

  <ows:OperationsMetadata>
  ... 
      <ows:Constraint name="FederatedCatalogues">
          <ows:Value>http://localhost/pycsw/csw.py?config=CSW-1.yml</ows:Value>
          <ows:Value>http://localhost/pycsw/csw.py?config=CSW-2.yml</ows:Value>
          <ows:Value>http://localhost/pycsw/csw.py?config=CSW-3.yml</ows:Value>
      </ows:Constraint>
  ...
  </ows:OperationsMetadata>

...which advertises which CSW endpoint(s) the CSW server will spawn if a distributed search is requested by the client.
 
in the CSW-all configuration:

.. code-block:: yaml

  federatedcatalogues:
      - http://localhost/pycsw/csw.py?config=CSW-1.yml
      - http://localhost/pycsw/csw.py?config=CSW-2.yml
      - http://localhost/pycsw/csw.py?config=CSW-3.yml
 
At which point a CSW client request to CSW-all with ``distributedsearch=TRUE``, while specifying an optional ``hopCount``.  Query network topology:

.. code-block:: none 

          AnyClient
              ^
              |
              v
           CSW-all
              ^ 
              |
              v
       /-------------\
       ^      ^      ^
       |      |      |
       v      v      v
     CSW-1  CSW-2  CSW-3
 
As a result, a pycsw deployment in this scenario may be approached on a per 'theme' basis, or at an aggregate level.
 
All interaction in this scenario is local to the pycsw installation, so network performance would not be problematic.
 
A very important facet of distributed search is as per Annex B of OGC:CSW 2.0.2.  Given that all the CSW endpoints are managed locally, duplicates and infinite looping are not deemed to present an issue.

OGC API - Records
-----------------

Experimental support for distibuted searching is available in pycsw's OGC API - Records support to allow for searching remote services.  The implementation uses the same approach as described above, operating in OGC API - Records mode.

.. note::

   The ``federatedcatalogues`` directives must point to an OGC API - Records **collections** endpoint.

.. code-block:: yaml

  federatedcatalogues:
      - https://example.org/collections/collection1
      - https://example.org/collections/collection2
 
With the above configured, a distributed search can be invoked as follows:

http://localhost/collections/metadata:main/items?distributed=true
