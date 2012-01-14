.. _repository:

Metadata Repository Setup
=========================

pycsw supports the following databases:

- SQLite3
- PostgreSQL
- MySQL

.. note::
  Unless your installation environment requires PostgreSQL or MySQL, the easiest and fastest way to deploy pycsw is using SQLite3 as the backend.

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

The database created is an `OGC SFSQL`_ compliant database, and can be used with any implementing software.  For example, to use with `OGR`_:

.. code-block:: bash

  $ ogrinfo /path/to/records.db
  INFO: Open of 'records.db'
  using driver 'SQLite' successful.
  1: records (Polygon)
  $ ogrinfo -al /path/to/records.db
  # lots of output

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

Exporting the Repository
------------------------

.. code-block:: bash

  $ python ./sbin/dump_db.py output_dir sqlite:////path/to/records.db

This will write each record in ``records.db`` to an XML document on disk, in directory ``output_dir``.

Database Specific Notes
-----------------------

PostgreSQL
^^^^^^^^^^

- pycsw makes uses of PL/Python functions.  To enable PostgreSQL support, the database user must be able to create functions within the database.

.. _`OGR`: http://www.gdal.org/ogr
.. _`OGC SFSQL`: http://www.opengeospatial.org/standards/sfs
