.. _transactions:

Transactions
============

.. note::

  TODO: transaction support is pending.

pycsw has the ability to process CSW Harvest and Transaction requests.  Transactions are disabled by default; to enable, ``server.transactions`` must be set to ``true``.  Access to transactional functionality is limited to IP addresses which must be set in ``server.transactions_ips``.
