.. _installation:

Installation
============

System Requirements
-------------------

pycsw requires the following supporting libraries:

- `lxml`_ (version >= 2.2.3) for XML support
- `SQLAlchemy`_ (version >= 0.0.5) for database bindings
- `pyproj`_ (version >= 1.8.9) for coordinate transformations
- `Shapely`_ (version >= 1.2.15) for spatial query / geometry support
- `OWSLib`_ (version >= 0.5.1) for CSW client and metadata parser

.. note::

  For :ref:`GeoNode <geonode>` deployments, SQLAlchemy is not required

Installing from Source
----------------------

:ref:`Download <download>` the latest version or fetch from Git:

The Quick and Dirty Way
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

  $ git clone git://github.com/geopython/pycsw.git

Ensure that CGI is enabled for the install directory.  For example, on Apache, if pycsw is installed in ``/srv/www/htdocs/pycsw`` (where the URL will be ``http://host/pycsw/csw.py``), add the following to ``httpd.conf``:

.. code-block:: none

  <Location /pycsw/>
   Options FollowSymLinks +ExecCGI
   Allow from all
   AddHandler cgi-script .py
  </Location>

.. note::
  If pycsw is installed in ``cgi-bin``, this should work as expected.  In this case, the :ref:`tester <tester>` application must be moved to a different location to serve static HTML documents.

The Clean and Proper Way
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

  $ git clone git://github.com/geopython/pycsw.git
  $ python setup.py build
  $ python setup.py install

At this point, pycsw is installed as a library and requires a CGI ``csw.py`` or WSGI ``csw.wsgi`` script to be served into your web server environment (see below for WSGI configuration/deployment).

.. _pypi:

Installing from the Python Package Index (PyPi)
-----------------------------------------------

.. code-block:: bash

  # easy_install or pip will do the trick
  $ easy_install pycsw
  # or
  $ pip install pycsw

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

.. _ubuntu:

Installing on Ubuntu/Xubuntu/Kubuntu
------------------------------------

In order to install pycsw to an Ubuntu based distribution, one can run the following commands:

.. code-block:: bash

  # sudo add-apt-repository ppa:gcpp-kalxas/ppa-tzotsos
  # sudo apt-get updated
  # sudo apt-get install pycsw

An alternative method is to use the OSGeoLive installation script located in ``pycsw/etc/dist/osgeolive``:

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

By default, ``default.cfg`` is at the root of the pycsw install.  If pycsw is setup outside an HTTP server's ``cgi-bin`` area, this file could be read.  The following options protect the configuration:

- move ``default.cfg`` to a non HTTP accessible area, and modify ``csw.py`` to point to the updated location
- configure web server to deny access to the configuration.  For example, in Apache, add the following to ``httpd.conf``:

.. code-block:: none

  <Files ~ "\.(cfg)$">
   order allow,deny
   deny from all
  </Files>


Running on WSGI
---------------

pycsw supports the `Web Server Gateway Interface`_ (WSGI).  To run pycsw in WSGI mode, use ``csw.wsgi`` in your WSGI server environment.  Below is an example of configuring with Apache:

.. code-block:: none

  WSGIDaemonProcess host1 home=/var/www/pycsw processes=2
  WSGIProcessGroup host1
  WSGIScriptAlias /pycsw-wsgi /var/www/pycsw/csw.wsgi
  <Directory /var/www/pycsw>
    Order deny,allow
    Allow from all
  </Directory>

or use the `WSGI reference implementation`_:

.. code-block:: bash

  $ python ./csw.wsgi
  Serving on port 8000...

which will publish pycsw to http://localhost:8000/

.. _`lxml`: http://lxml.de/
.. _`SQLAlchemy`: http://www.sqlalchemy.org/
.. _`Shapely`: http://toblerity.github.com/shapely/
.. _`pyproj`: http://code.google.com/p/pyproj/
.. _`OWSLib`: http://github.com/geopython/OWSLib
.. _`Web Server Gateway Interface`: http://en.wikipedia.org/wiki/Web_Server_Gateway_Interface
.. _`WSGI reference implementation`: http://docs.python.org/library/wsgiref.html
