.. _repository:

Metadata Repository Setup
=========================

pycsw ships with SQLite support (additional databases will be supported in a future release).

To expose your geospatial metadata via pycsw, perform the following actions:

- setup the database
- import metadata
- configure the db connection

Setting up the Database
-----------------------

.. code-block:: bash

  $ cd /path/to/pycsw
  $ export PYTHONPATH=`pwd` 
  $ python ./sbin/setup_db.py ./etc/schemas/sql/records.ddl records.db

Importing Metadata
------------------

.. code-block:: bash

  $ python ./sbin/load_csw_records.py /path/to/records records.db

This will import all ``*.xml`` records from ``/path/to/records`` into ``records.db``.

Configuring the Database Connection
-----------------------------------

By default, ``default-sample.cfg`` contains all required binding information.  If you are setting up your database as per above,
the default configuration needs only the ``repository.db`` value to be updated.  Otherwise, you can map your own database table and columns.

See :ref:`configuration`, (**[repository]**) for more information.
