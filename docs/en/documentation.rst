.. _documentation:

=======================================================
pycsw |release| documentation
=======================================================

.. toctree::
   :maxdepth: 2

:Author: Tom Kralidis
:Contact: tomkralidis at hotmail.com
:Release: |release|
:Date: |today|

Introduction
============

pycsw is an OGC CSW server implementation in Python.

Features
========

Standards Support
-----------------

+-------------------+-------------------+
| Standard          | Version(s)        |
+===================+===================+
| `OGC CSW`_        | 2.0.2             |
+-------------------+-------------------+
| `OGC Filter`_     | 1.1.0             |
+-------------------+-------------------+
| `OGC OWS Common`_ | 1.0.0, 1.1.0, 2.0 |
+-------------------+-------------------+
| `Dublin Core`_    | 1.1               |
+-------------------+-------------------+

Installation
============

Requirements
------------

pycsw requires the following supporting libraries:

- `lxml`_ for XML support
- `SQLAlchemy`_ for database bindings
- `Shapely`_ for geometry support

Install
-------

Subversion:

.. code-block:: bash

  $ svn co https://pycsw.svn.sourceforge.net/svnroot/pycsw pycsw 

The pycsw wiki is located at https://sourceforge.net/apps/trac/pycsw.

The pycsw source code is available at svn co https://pycsw.svn.sourceforge.net/svnroot/pycsw.  You can browse the source code at at https://sourceforge.net/apps/trac/pycsw/browser.

You can find out about software metrics at the pycsw `ohloh`_ page.

Configuration
=============


Testing
=======

OGC CITE
--------

Support
=======

The pycsw mailing list is the primary means for users and developers to exchange ideas, discuss improvements, and ask questions.  To subscribe, visit https://lists.sourceforge.net/lists/listinfo/pycsw-devel.

License
=======

.. include: ../../LICENSE.txt

Contact
=======

 * Tom Kralidis <tomkralidis@hotmail.com>

.. _`Open Geospatial Consortium`: http://www.opengeospatial.org/
.. _`OGC CSW`: http://www.opengeospatial.org/standards/cat
.. _`OGC Filter`: http://www.opengeospatial.org/standards/filter
.. _`OGC OWS Common`: http://www.opengeospatial.org/standards/common
.. _`NASA DIF`: http://gcmd.nasa.gov/User/difguide/ 
.. _`FGDC CSDGM`: http://www.fgdc.gov/metadata/csdgm
.. _`ISO 19115`: http://www.iso.org/iso/catalogue_detail.htm?csnumber=26020
.. _`ISO 19139`: http://www.iso.org/iso/catalogue_detail.htm?csnumber=32557
.. _`Dublin Core`: http://www.dublincore.org/
.. _`lxml`: http://codespeak.net/lxml
.. _`SQLAlchemy`: http://www.sqlalchemy.org/
.. _`Shapely`: http://trac.gispython.org/lab/wiki/Shapely
.. _`ohloh`: http://www.ohloh.net/p/pycsw
