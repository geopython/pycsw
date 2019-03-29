.. _installation:

Installation
============

System Requirements
-------------------

pycsw is written in `Python <http://python.org>`_, and works with (tested) version 2.7, 3.4 and 3.5

pycsw requires the following Python supporting libraries:

- `lxml`_ for XML support
- `SQLAlchemy`_ for database bindings
- `pyproj`_ for coordinate transformations
- `Shapely`_ for spatial query / geometry support
- `OWSLib`_ for CSW client and metadata parser
- `six`_ for Python 2/3 compatibility
- `xmltodict`_ for working with XML similar to working with JSON
- `geolinks`_ for dealing with geospatial links

.. note::

  You can install these dependencies via `easy_install`_ or `pip`_

.. note::

  For :ref:`GeoNode <geonode>` or :ref:`Open Data Catalog <odc>` or :ref:`HHypermap <hhypermap>` deployments, SQLAlchemy is not required

Installing from Source
----------------------

`Download <https://pycsw.org/download>`_ the latest stable version or fetch from Git.

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
  $ python pycsw/wsgi.py
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

At this point, pycsw is installed as a library and requires a CGI ``csw.py``
or WSGI ``pycsw/wsgi.py`` script to be served into your web server environment
(see below for WSGI configuration/deployment).

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

In order to install the pycsw package in openSUSE Leap (stable distribution), one can run the following commands as user ``root``:

.. code-block:: bash

  # zypper -ar http://download.opensuse.org/repositories/Application:/Geo/openSUSE_Leap_42.1/ GEO
  # zypper refresh
  # zypper install python-pycsw pycsw-cgi


In order to install the pycsw package in openSUSE Tumbleweed (rolling distribution), one can run the following commands as user ``root``:

.. code-block:: bash

  # zypper -ar http://download.opensuse.org/repositories/Application:/Geo/openSUSE_Tumbleweed/ GEO
  # zypper refresh
  # zypper install python-pycsw pycsw-cgi

An alternative method is to use the `One-Click Installer <https://software.opensuse.org/package/python-pycsw>`_.

.. _ubuntu:

Installing on Ubuntu/Mint
-------------------------

In order to install the most recent pycsw release to an Ubuntu-based distribution, one can use the UbuntuGIS Unstable repository by running the following commands:

.. code-block:: bash

  # sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable
  # sudo apt-get update
  # sudo apt-get install python-pycsw pycsw-cgi

Alternatively, one can use the UbuntuGIS Stable repository which includes older but very well tested versions:

  # sudo add-apt-repository ppa:ubuntugis/ppa
  # sudo apt-get update
  # sudo apt-get install python-pycsw pycsw-cgi

.. note::
  Since Ubuntu 16.04 LTS Xenial release, pycsw is included by default in the official Multiverse repository.

Running on Windows
------------------

For Windows installs, change the first line of ``csw.py`` to:

.. code-block:: python

  #!/Python27/python -u

.. note::
  The use of ``-u`` is required to properly output gzip-compressed responses.
  
.. Tip::
  
   `MS4W <https://ms4w.com>`__  (MapServer for Windows) as of its version 4.0 release includes pycsw,
   Apache's mod_wsgi, Python 3.7, and many other tools, all ready to use out of the box.  After installing,
   you will find your local pycsw catalogue endpoint, and steps for further configuration, on your
   browser's localhost page.  You can read more about pycsw inside MS4W `here <https://ms4w.com/README_INSTALL.html#pycsw>`__.

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

pycsw supports the `Web Server Gateway Interface`_ (WSGI).  To run pycsw in
WSGI mode, use ``pycsw/wsgi.py`` in your WSGI server environment.

.. note::

  ``mod_wsgi`` supports only the version of python it was compiled with. If the target server
  already supports WSGI applications, pycsw will need to use the same python version.
  `WSGIDaemonProcess`_ provides a ``python-path`` directive that may allow a virtualenv created from the python version ``mod_wsgi`` uses.

Below is an example of configuring with Apache:

.. code-block:: none

  WSGIDaemonProcess host1 home=/var/www/pycsw processes=2
  WSGIProcessGroup host1
  WSGIScriptAlias /pycsw-wsgi /var/www/pycsw/wsgi.py
  <Directory /var/www/pycsw>
    Order deny,allow
    Allow from all
  </Directory>


or use the `WSGI reference implementation`_:

.. code-block:: bash

  $ python ./pycsw/wsgi.py
  Serving on port 8000...

which will publish pycsw to ``http://localhost:8000/``

.. _`lxml`: http://lxml.de/
.. _`SQLAlchemy`: http://www.sqlalchemy.org/
.. _`Shapely`: http://toblerity.github.io/shapely/
.. _`pyproj`: http://code.google.com/p/pyproj/
.. _`OWSLib`: https://github.com/geopython/OWSLib
.. _`six`: https://pypi.python.org/pypi/six/
.. _`xmltodict`: https://github.com/martinblech/xmltodict
.. _`geolinks`: https://github.com/geopython/geolinks
.. _`easy_install`: http://packages.python.org/distribute/easy_install.html
.. _`pip`: http://www.pip-installer.org
.. _`Web Server Gateway Interface`: http://en.wikipedia.org/wiki/Web_Server_Gateway_Interface
.. _`WSGIDaemonProcess`: https://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIDaemonProcess
.. _`WSGI reference implementation`: http://docs.python.org/library/wsgiref.html
