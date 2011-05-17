.. _transactions:

Transactions
============

pycsw has the ability to process CSW Harvest and Transaction requests (CSW-T).  Transactions are disabled by default; to enable, ``manager.transactions`` must be set to ``true``.  Access to transactional functionality is limited to IP addresses which must be set in ``manager.allowed_ips``.

For transactions to be functional, the SQLite database file (**and it's parent directory**) must be fully writable.  For example:

.. code-block:: bash

  $ mkdir /path/data
  $ chmod 777 /path/data
  $ chmod 666 test.db
  $ mv test.db /path/data

For CSW-T deployments, it is strongly advised that this directory reside in an area that is not accessible by HTTP.

Harvesting
----------

pycsw supports the CSW-T ``Harvest`` operation.  Records which are harvested require to setup a cronjob to refresh records in the local repository.  A sample cronjob is available in ``etc/harvest-records.sh``.  Harverst operation Results can be sent by email if the Harvest request specifies a ``ResponseHandler`` with an email address (via the ``mailto:`` protocol).

Transactions
------------

pycsw support 3 modes of the ``Transaction`` operation (``Insert``, ``Update``, ``Delete``):

- **Insert**: full XML documents can be inserted as per CSW-T
- **Update**: TODO
- **Delete**: TODO

For reference, the :ref:`tester` contains CSW-T request examples.
