.. _fgdc:

FGDC CSGDM 1998
---------------

Overview
^^^^^^^^

The `FGDC CSDGM Application Profile`_  is a profile of CSW 2.0.2 which enables discovery of geospatial metadata following FGDC:CSDGM 1998 metadata.
 
Configuration
^^^^^^^^^^^^^

No additional extra configuration is required.

Querying
^^^^^^^^

 * **typename**: fgdc:metadata
 * **outputschema**: http://www.opengis.net/cat/csw/csdgm

Enabling FGDC Support
^^^^^^^^^^^^^^^^^^^^^^

To enable fgdc support, add ``fgdc`` to ``server.profiles``.

Testing
^^^^^^^

A testing interface is available in ``tester/index.html`` which contains tests specific to FGDC to demonstrate functionality.  See :ref:`tester` for more information.

.. _`FGDC CSDGM Application Profile`: http://portal.opengeospatial.org/files/?artifact_id=16936
