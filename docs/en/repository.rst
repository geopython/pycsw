.. _repository:

Metadata Repository Setup
=========================

pycsw ships with SQLite support (additional databases will be supported in a future release).

To expose your geospatial metadata via pycsw, perform the following actions:

- setup the database
- import metadata
- publish the repository

Supported Information Models
----------------------------

By default, pycsw supports the ``csw:Record`` information model.

Setting up the Database
-----------------------

.. code-block:: bash

  $ cd /path/to/pycsw
  $ export PYTHONPATH=`pwd` 
  $ python ./sbin/setup_db.py ./etc/schemas/sql/records.ddl records.db

Importing Metadata
------------------

.. code-block:: bash

  $ python ./sbin/load_records.py /path/to/records records.db

This will import all ``*.xml`` records from ``/path/to/records`` into ``records.db`` and configure the repository to expose queryables as per Table 53 of OGC:CSW.

.. note::

  Records can also be imported using CSW-T (see :ref:`transactions`).

Publishing the Repository
--------------------------

To expose the repository, setup a ``repository`` section as specified in :ref:`configuration`.

