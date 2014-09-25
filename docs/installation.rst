.. _installation:

Installation
============

System Requirements
-------------------

pycsw is written in `Python <http://python.org>`_, and works with (tested) version 2.6 and 2.7

pycsw requires the following Python supporting libraries:

- `lxml`_ for XML support
- `SQLAlchemy`_ for database bindings
- `pyproj`_ for coordinate transformations
- `Shapely`_ for spatial query / geometry support
- `OWSLib`_ for CSW client and metadata parser

.. note::

  You can install these dependencies via `easy_install`_ or `pip`_

.. note::

  For :ref:`GeoNode <geonode>` or :ref:`Open Data Catalog <odc>` deployments, SQLAlchemy is not required

Installing from Source
----------------------

`Download </download.html>`_ the latest stable version or fetch from Git.

For Developers and the Truly Impatient
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The 4 minute install:

.. code-block:: bash

  $ virtualenv pycsw && cd pycsw && . bin/activate
  $ git clone https://github.com/geopython/pycsw.git && cd pycsw
  $ pip install -e . && pip install -r requirements-standalone.txt
  $ cp default-sample.cfg default.cfg
  $ vi default.cfg
  # adjust paths in
  # - server.home
  # - repository.database
  # set server.url to http://localhost:8000/
  $ python csw.wsgi
  $ curl http://localhost:8000/?service=CSW&version=2.0.2&request=GetCapabilities


The Quick and Dirty Way
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

  $ git clone git://github.com/geopython/pycsw.git

Ensure that CGI is enabled for the install directory.  For example, on Apache, if pycsw is installed in ``/srv/www/htdocs/pycsw`` (where the URL will be ``http://host/pycsw/csw.py``), add the following to ``httpd.conf``:

.. code-block:: none

  <Location /pycsw/>
   Options +FollowSymLinks +ExecCGI
   Allow from all
   AddHandler cgi-script .py
  </Location>

.. note::
  If pycsw is installed in ``cgi-bin``, this should work as expected.  In this case, the :ref:`tests <tests>` application must be moved to a different location to serve static HTML documents.

Make sure, you have all the dependencies from ``requirements.txt and requirements-standalone.txt``

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

In order to install the OBS package in openSUSE 12.3, one can run the following commands as user ``root``:

.. code-block:: bash

  # zypper -ar http://download.opensuse.org/repositories/Application:/Geo/openSUSE_12.3/ GEO
  # zypper -ar http://download.opensuse.org/repositories/devel:/languages:/python/openSUSE_12.3/ python
  # zypper refresh
  # zypper install python-pycsw pycsw-cgi

For earlier openSUSE versions change ``12.3`` with ``12.2``. For future openSUSE version use ``Factory``.

An alternative method is to use the `One-Click Installer <http://software.opensuse.org/search?q=pycsw&baseproject=openSUSE%3A12.3&lang=en&include_home=true&exclude_debug=true>`_.

.. _ubuntu:

Installing on Ubuntu/Xubuntu/Kubuntu
------------------------------------

In order to install pycsw to an Ubuntu based distribution, one can run the following commands:

.. code-block:: bash

  # sudo add-apt-repository ppa:pycsw/stable
  # sudo apt-get update
  # sudo apt-get install python-pycsw pycsw-cgi

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

pycsw supports the `Web Server Gateway Interface`_ (WSGI).  To run pycsw in WSGI mode, use ``csw.wsgi`` in your WSGI server environment.

**NOTE:** mod_wsgi supports only the version of python it was compiled with. If the target server
already supports one or more WSGI applications, pycsw will need to use the same python version.
WSGIDaemonProcess <https://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIDaemonProcess> provides a python-path directive
that may allow a virtualenv created from the python version mod_wsgi uses.

Below is an example of configuring with Apache:

.. code-block:: none

  WSGIDaemonProcess host1 home=/var/www/pycsw processes=2
  WSGIProcessGroup host1
  WSGIScriptAlias /pycsw-wsgi /var/www/pycsw/csw.wsgi
  <Directory /var/www/pycsw>
    Order deny,allow
    Allow from all
  </Directory>

**NOTE:** mod_wsgi supports only the version of python it was compiled with. If the target server
already supports one or more WSGI applications, pycsw will need to use the same python version.
WSGIDaemonProcess <https://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIDaemonProcess> provides a python-path directive
that may allow a virtualenv created from the python version mod_wsgi uses.

or use the `WSGI reference implementation`_:

.. code-block:: bash

  $ python ./csw.wsgi
  Serving on port 8000...

which will publish pycsw to ``http://localhost:8000/``

.. _`lxml`: http://lxml.de/
.. _`SQLAlchemy`: http://www.sqlalchemy.org/
.. _`Shapely`: http://toblerity.github.io/shapely/
.. _`pyproj`: http://code.google.com/p/pyproj/
.. _`OWSLib`: https://github.com/geopython/OWSLib
.. _`easy_install`: http://packages.python.org/distribute/easy_install.html
.. _`pip`: http://www.pip-installer.org
.. _`Web Server Gateway Interface`: http://en.wikipedia.org/wiki/Web_Server_Gateway_Interface
.. _`WSGI reference implementation`: http://docs.python.org/library/wsgiref.html
