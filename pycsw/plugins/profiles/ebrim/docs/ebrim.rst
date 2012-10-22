.. _ebrim:

CSW-ebRIM Registry Service - Part 1: ebRIM profile of CSW
---------------------------------------------------------

Overview
^^^^^^^^
The CSW-ebRIM Registry Service is a profile of CSW 2.0.2 which enables discovery of geospatial metadata following the ebXML information model.

Configuration
^^^^^^^^^^^^^

No extra configuration is required.

Querying
^^^^^^^^

 * **typename**: ``rim:RegistryObject``
 * **outputschema**: ``urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0``

Enabling ebRIM Support
^^^^^^^^^^^^^^^^^^^^^^

To enable ebRIM support, add ``ebrim`` to ``server.profiles`` as specified in :ref:`configuration`.

Testing
^^^^^^^

A testing interface is available in ``tests/index.html`` which contains tests specific to ebRIM to demonstrate functionality.  See :ref:`tests` for more information.

