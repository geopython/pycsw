.. _transactions:

Transactions
============

pycsw has the ability to process CSW Harvest and Transaction requests (CSW-T).  Transactions are disabled by default; to enable, ``manager.transactions`` must be set to ``true``.  Access to transactional functionality is limited to IP addresses which must be set in ``manager.allowed_ips``.

.. note::

   For transactions to be functional when using SQLite3, the SQLite3 database file (**and it's parent directory**) must be fully writable.  For example:

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

pycsw supports the CSW-T ``Harvest`` operation.  Records which are harvested require to setup a cronjob to periodically refresh records in the local repository.  A sample cronjob is available in ``etc/harvest-all.cron`` which points to ``sbin/pycsw-admin.py`` (you must specify the correct path to your configuration).  Harvest operation results can be sent by email (via ``mailto:``) or ftp (via ``ftp://``) if the Harvest request specifies ``csw:ResponseHandler``.

Transactions
------------

pycsw support 3 modes of the ``Transaction`` operation (``Insert``, ``Update``, ``Delete``):

- **Insert**: full XML documents can be inserted as per CSW-T
- **Update**: updates can be made as full record updates or record properties against a ``csw:Constraint``
- **Delete**: deletes can be made against a ``csw:Constraint``

The :ref:`tester` contains CSW-T request examples.
