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

+-------------------+------------+
| Standard          | Version(s) |
+===================+============+
| `OGC CSW`_        | 2.0.2      |
+-------------------+------------+
| `OGC Filter`_     | 1.1.0      |
+-------------------+------------+
| `OGC OWS Common`_ | 1.0.0      |
+-------------------+------------+
| `Dublin Core`_    | 1.1        |
+-------------------+------------+

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

Download the latest version or fetch svn trunk:

.. code-block:: bash

  $ svn co https://pycsw.svn.sourceforge.net/svnroot/pycsw pycsw 

Configuration
=============

Edit the following in ``default.cfg``:

[server]

- **home**: the full file path to ``pycsw``
- **url**: the URL of the resulting service
- **mimetype**: the MIME type when returning HTTP responses
- **language**: the ISO 639-2 language and country code of the service (e.g. en-CA)
- **encoding**: the content type encoding (e.g. ISO-8859-1)
- **maxrecords**: the maximum number of records to return by default
- **data**: the full file path to the SQLite database

[identification]

- **title**: the title of the service
- **abstract**: some descriptive text about the service
- **keywords**: a comma-seperated keyword list of keywords about the service
- **fees**: fees associated with the service
- **accessconstraints**: access constraints associated with the service

[provider]

- **name**: the name of the service provider
- **url**: the URL of the service provider

[contact]

- **name**: the name of the provider contact
- **position**: the position title of the provider contact
- **address**: the address of the provider contact
- **city**: the city of the provider contact
- **stateorprovince**: the province or territory of the provider contact
- **postalcode**: the postal code of the provider contact
- **country**: the country of the provider contact
- **phone**: the phone number of the provider contact
- **fax**: the facsimile number of the provider contact
- **email**: the email address of the provider contact
- **url**: the URL to more information about the provider contact
- **hours**: the hours of service to contact the provider
- **contactinstructions**: the how to contact the provider contact
- **role**: the role of the provider contact

Testing
=======

OGC CITE
--------

Support
=======

The pycsw wiki is located at https://sourceforge.net/apps/trac/pycsw.

The pycsw source code is available at svn co https://pycsw.svn.sourceforge.net/svnroot/pycsw.  You can browse the source code at at https://sourceforge.net/apps/trac/pycsw/browser.

You can find out about software metrics at the pycsw `ohloh`_ page.

The pycsw mailing list is the primary means for users and developers to exchange ideas, discuss improvements, and ask questions.  To subscribe, visit https://lists.sourceforge.net/lists/listinfo/pycsw-devel.

License
=======

Copyright (c) 2010 Tom Kralidis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

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
