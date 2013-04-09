.. _dif:

Directory Interchange Format (DIF) 9.7
--------------------------------------

Overview
^^^^^^^^

The `Directory Interchange Format`_ (DIF) is a metadata format supported by the NASA `Global Change Master Directory`_.

Configuration
^^^^^^^^^^^^^

No additional configuration is required.

Querying
^^^^^^^^

 * **typename**: ``dif:DIF``
 * **outputschema**: ``http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/``

Enabling DIF Support
^^^^^^^^^^^^^^^^^^^^^^

To enable DIF support, add ``dif`` to ``server.profiles``.

Testing
^^^^^^^

A testing interface is available in ``tests/index.html`` which contains tests specific to DIF to demonstrate functionality.  See :ref:`tests` for more information.

.. _`Directory Interchange Format`: http://gcmd.gsfc.nasa.gov/add/difguide/index.html
.. _`Global Change Master Directory`: http://gcmd.nasa.gov/
