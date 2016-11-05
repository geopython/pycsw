.. _transactions:

Transactions
============

pycsw has the ability to process CSW Harvest and Transaction requests (CSW-T).  Transactions are disabled by default; to enable, ``manager.transactions`` must be set to ``true``.  Access to transactional functionality is limited to IP addresses which must be set in ``manager.allowed_ips``.

Supported Resource Types
------------------------

For transactions and harvesting, pycsw supports the following metadata resource types by default:

.. csv-table::
  :header: Resource Type,Namespace,Transaction,Harvest

  Dublin Core,``http://www.opengis.net/cat/csw/2.0.2``,yes,yes
  FGDC,``http://www.opengis.net/cat/csw/csdgm``,yes,yes
  GM03,``http://www.interlis.ch/INTERLIS2.3``,yes,yes
  ISO 19139,``http://www.isotc211.org/2005/gmd``,yes,yes
  ISO GMI,``http://www.isotc211.org/2005/gmi``,yes,yes
  OGC:CSW 2.0.2,``http://www.opengis.net/cat/csw/2.0.2``,,yes
  OGC:WMS 1.1.1/1.3.0,``http://www.opengis.net/wms``,,yes
  OGC:WMTS 1.0.0,``http://www.opengis.net/wmts/1.0``,,yes
  OGC:WFS 1.0.0/1.1.0/2.0.0,``http://www.opengis.net/wfs``,,yes
  OGC:WCS 1.0.0,``http://www.opengis.net/wcs``,,yes
  OGC:WPS 1.0.0,``http://www.opengis.net/wps/1.0.0``,,yes
  OGC:SOS 1.0.0,``http://www.opengis.net/sos/1.0``,,yes
  OGC:SOS 2.0.0,``http://www.opengis.net/sos/2.0``,,yes
  `WAF`_,``urn:geoss:urn``,,yes

Additional metadata models are supported by enabling the appropriate :ref:`profiles`.

.. note::

   For transactions to be functional when using SQLite3, the SQLite3 database file (**and its parent directory**) must be fully writable.  For example:

.. code-block:: bash

  $ mkdir /path/data
  $ chmod 777 /path/data
  $ chmod 666 test.db
  $ mv test.db /path/data

For CSW-T deployments, it is strongly advised that this directory reside in an area that is not accessible by HTTP.

Harvesting
----------

.. note::

   Your server must be able to make outgoing HTTP requests for this functionality.

pycsw supports the CSW-T ``Harvest`` operation.  Records which are harvested require to setup a cronjob to periodically refresh records in the local repository.  A sample cronjob is available in ``etc/harvest-all.cron`` which points to ``pycsw-admin.py`` (you must specify the correct path to your configuration).  Harvest operation results can be sent by email (via ``mailto:``) or ftp (via ``ftp://``) if the Harvest request specifies ``csw:ResponseHandler``.

.. note::

  For ``csw:ResponseHandler`` values using the ``mailto:`` protocol, you must have ``server.smtp_host`` set in your :ref:`configuration <configuration>`.

OGC Web Services
^^^^^^^^^^^^^^^^

When harvesting OGC web services, requests can provide the base URL of the service as part of the Harvest request.  pycsw will construct a ``GetCapabilities`` request dynamically.

When harvesting other CSW servers, pycsw pages through the entire CSW in default increments of 10.  This value can be modified via the ``manager.csw_harvest_pagesize`` :ref:`configuration <configuration>` option.  It is strongly advised to use the ``csw:ResponseHandler`` parameter for harvesting large CSW catalogues to prevent HTTP timeouts.

Transactions
------------

pycsw supports 3 modes of the ``Transaction`` operation (``Insert``, ``Update``, ``Delete``):

- **Insert**: full XML documents can be inserted as per CSW-T
- **Update**: updates can be made as full record updates or record properties against a ``csw:Constraint``
- **Delete**: deletes can be made against a ``csw:Constraint``

Transaction operation results can be sent by email (via ``mailto:``) or ftp (via ``ftp://``) if the Transaction request specifies ``csw:ResponseHandler``.

The :ref:`tests` contain CSW-T request examples.

.. _`WAF`: http://seabass.ieee.org/groups/geoss/index.php?option=com_sir_200&Itemid=157&ID=183
