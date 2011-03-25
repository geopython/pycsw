.. _transactions:

Transactions
============

pycsw has the ability to process CSW Harvest and Transaction requests.  Transactions are disabled by default; to enable, ``transactions.enabled`` must be set to ``true``.  Access to transactional functionality is limited to IP addresses which must be set in ``transactions.ips``.
