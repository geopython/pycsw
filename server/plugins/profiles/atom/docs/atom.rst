.. _atom:

Atom Syndication Format 1.0
---------------------------

Overview
^^^^^^^^

The `Atom Syndication Format`_ is used in `RSS`_ feeds as well as :ref:`OpenSearch <opensearch>`.

Configuration
^^^^^^^^^^^^^

No additional configuration is required.


Querying
^^^^^^^^

 * **typename**: atom:entry
 * **outputschema**: http://www.w3.org/2005/Atom

Enabling Atom Support
^^^^^^^^^^^^^^^^^^^^^^

To enable Atom support, add ``atom`` to ``server.profiles``.

Testing
^^^^^^^

A testing interface is available in ``tester/index.html`` which contains tests specific to Atom to demonstrate functionality.  See :ref:`tester` for more information.

.. _`Atom Syndication Format`: http://tools.ietf.org/html/rfc4287
.. _`RSS`: http://en.wikipedia.org/wiki/RSS
