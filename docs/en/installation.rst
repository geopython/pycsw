.. _installation:

Installation
============

Requirements
------------

pycsw requires the following supporting libraries:

- `lxml`_ (version >= 2.2.3) for XML support
- `SQLAlchemy`_ (version >= 0.0.5) for database bindings
- `Shapely`_ (version >= 1.2.8) for geometry support

Install
-------

:ref:`Download <download>` the latest version or fetch svn trunk:

.. code-block:: bash

  $ svn co https://pycsw.svn.sourceforge.net/svnroot/pycsw pycsw 

Ensure that CGI is enabled for your install directory.  For example, on Apache, if you setup pycsw in ``/srv/www/htdocs/pycsw`` (where your URL will be ``http://host/pycsw/csw.py``), add the following to ``httpd.conf``:

.. code-block:: none

  <Location /pycsw/>
   Options FollowSymLinks +ExecCGI
   Allow from all
   AddHandler cgi-script .py
  </Location>

If you install pycsw in ``cgi-bin``, this should work as expected.  Note that the :ref:`tester <sample-requests>` application must be moved to a normal location to serve static HTML documents.

Running on Windows
------------------

For Windows installs, change the first line of ``csw.py`` to:

.. code-block:: python

  #!/Python27/python -u

Note that the use of ``-u`` is required to properly output gzip-compressed responses.

Security
--------

By default, ``default.cfg`` is within root of the pycsw install.  If you have setup pycsw in a non cgi-bin area, this file could be read.  To protect the configuration, you have a couple of options:

- move ``default.cfg`` to a non HTTP accessible area, and modify ``csw.py`` to point to the updated location
- set your web server to deny access to the configuration.  For example, in Apache, add the following to ``httpd.conf``:

.. code-block:: none

  <Files ~ "\.(cfg)$">
   order allow,deny
   deny from all
  </Files>


.. include:: ../../COMMITTERS.txt

.. _`lxml`: http://lxml.de/
.. _`SQLAlchemy`: http://www.sqlalchemy.org/
.. _`Shapely`: http://trac.gispython.org/lab/wiki/Shapely
