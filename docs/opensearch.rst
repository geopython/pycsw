.. _opensearch:

OpenSearch Support
==================

pycsw supports the `A9 OpenSearch`_ 1.1 implementation in support of aggregated searching.

Description Document
--------------------

To generate an OpenSearch Description Document:

.. code-block:: bash

  $ cd /path/to/pycsw
  $ export PYTHONPATH=`pwd` 
  $ python-admin.py -c gen_opensearch_description -f default.cfg -o /path/to/opensearch.xml

This will create the document which can then be `autodiscovered <http://www.opensearch.org/Specifications/OpenSearch/1.1#Autodiscovery>`_.

OpenSearch support is enabled by default.  HTTP requests must be specified with ``mode=opensearch`` in the base URL for OpenSearch requests, e.g.:

.. code-block:: bash

  http://localhost/pycsw/csw.py?mode=opensearch&service=CSW&version=2.0.2&request=GetRecords&elementsetname=brief&typenames=csw:Record&resulttype=results

.. _`A9 OpenSearch`: http://www.opensearch.org/Home
