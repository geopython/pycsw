.. _installation:

Installation
============

System Requirements
-------------------

pycsw requires the following supporting libraries:

- `lxml`_ (version >= 2.2.3) for XML support
- `SQLAlchemy`_ (version >= 0.0.5) for database bindings
- `Shapely`_ (version >= 1.2.8) for spatial query / geometry support
- `pyproj`_ (version >= 1.8.9) for coordinate transformations

Installing from Source
----------------------

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

.. note::
  If you install pycsw in ``cgi-bin``, this should work as expected.  In this case, the :ref:`tester <tester>` application must be moved to a normal location to serve static HTML documents.

.. _opensuse:

Installing from OpenSUSE Build Service
--------------------------------------

In order to install the OBS package in openSUSE 12.1, one can run the following commands as user ``root``:

.. code-block:: bash

  # zypper -ar http://download.opensuse.org/repositories/Application:/Geo/openSUSE_12.1/ GEO
  # zypper -ar http://download.opensuse.org/repositories/devel:/languages:/python/openSUSE_12.1/ python
  # zypper refresh
  # zypper install pycsw

For earlier openSUSE versions change ``12.1`` with ``11.4``. For future openSUSE version use ``Factory``.

An alternative method is to use the `One-Click Installer <http://software.opensuse.org/search?q=pycsw&baseproject=openSUSE%3A12.1&lang=en&include_home=true&exclude_debug=true>`_.

Installing on Ubuntu/Xubuntu/Kubuntu
------------------------------------

In order to install pycsw to an Ubuntu based distribution, one can use the OSGeoLive installation script located in ``pycsw/etc/dist``:

.. code-block:: bash

  # cd pycsw/etc/dist
  # sudo ./install_pycsw.sh

The script installs the dependencies (Apache, lxml, sqlalchemy, shapely, pyproj) and then pycsw to ``/var/www``. 
  
Running on Windows
------------------

For Windows installs, change the first line of ``csw.py`` to:

.. code-block:: python

  #!/Python27/python -u

.. note::
  The use of ``-u`` is required to properly output gzip-compressed responses.

Security
--------

By default, ``default.cfg`` is at the root of the pycsw install.  If you have setup pycsw outside your HTTP server's ``cgi-bin`` area, this file could be read.  To protect the configuration, you have a couple of options:

- move ``default.cfg`` to a non HTTP accessible area, and modify ``csw.py`` to point to the updated location
- set your web server to deny access to the configuration.  For example, in Apache, add the following to ``httpd.conf``:

.. code-block:: none

  <Files ~ "\.(cfg)$">
   order allow,deny
   deny from all
  </Files>

.. _`lxml`: http://lxml.de/
.. _`SQLAlchemy`: http://www.sqlalchemy.org/
.. _`Shapely`: http://toblerity.github.com/shapely/
.. _`pyproj`: http://code.google.com/p/pyproj/
