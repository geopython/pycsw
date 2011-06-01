.. _repository:

Metadata Repository Setup
=========================

pycsw supports the following databases:

- SQLite3
- PostgreSQL (additional databases will be supported in a future release).

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
  $ python ./sbin/setup_db.py sqlite:////path/to/records.db

This will create the necessary tables and values for the repository.

Importing Metadata
------------------

.. code-block:: bash

  $ python ./sbin/load_records.py /path/to/records sqlite:////path/to/records.db

This will import all ``*.xml`` records from ``/path/to/records`` into ``records.db`` and configure the repository to expose queryables as per Table 53 of OGC:CSW.

.. note::

  Records can also be imported using CSW-T (see :ref:`transactions`).

Publishing the Repository
--------------------------

To expose the repository, setup a ``repository`` section as specified in :ref:`configuration`.

Database Specific Notes
-----------------------

PostgreSQL
^^^^^^^^^^

- To enable PostgreSQL support, the database user must be able to create functions within the database.
