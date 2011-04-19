.. _apiso:

ISO Metadata Application Profile (1.0.0)
----------------------------------------

Overview
^^^^^^^^
The ISO Metadata Application Profile (APISO) is a profile of CSW 2.0.2 which enables discovery of geospatial metadata following ISO 19139:2007 and ISO 19119:2005/PDAM 1.

Configuration
^^^^^^^^^^^^^

To expose your geospatial metadata via the APISO, via pycsw, perform the following actions:

- enable APISO support
- setup the database
- import metadata
- configure the db connection

Enabling APISO Support
----------------------

By default, all profiles in pycsw are disabled.  To enable APISO, set ``[server.profiles]=apiso`` in ``default.cfg``.

Setting up the Database
-----------------------

.. code-block:: bash

  $ cd /path/to/pycsw
  $ export PYTHONPATH=`pwd` 
  $ python ./sbin/setup_db.py ./server/profiles/apiso/etc/schemas/sql/md_metadata.ddl md_metadata.db

Importing Metadata
------------------

.. code-block:: bash

  $ python ./server/profiles/apiso/sbin/load_csw_records.py /path/to/records md_metadata.db

This will import all ``*.xml`` records from ``/path/to/records`` into ``md_metadata.db``.

Configuring the Database Connection
-----------------------------------

By default, ``server/profiles/apiso/apiso.cfg-shipped`` contains all required binding information.  If you are setting up your database as per above,
the default configuration needs only the ``repository.db`` value to be updated.  Otherwise, you can map your own database table and columns.

Testing
-------

A testing interface is available in ``server/profiles/apiso/tester/index.html`` which contains tests specific to APISO to demonstrate functionality.  See :ref:`tester` for more information.
