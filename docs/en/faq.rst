.. _faq:

FAQ
===

How do I perform CSW queries on FGDC metadata?
------------------------------------------------------- 

The CSW ``typename`` parameter allows a user to specify which types of metadata to query against (the default being ``csw:Record``).

To perform CSW queries against FGDC metadata, the ``typename`` parameter for FGDC metadata records must be set to ``fgdc:metadata``.  See :ref:`profiles` for valid ``typename`` parameters for all supported metadata.

How can I export my repository?
-------------------------------

Use the ``pycsw-admin.py`` utility to dump the records as XML documents to a directory:

.. code-block:: bash

  $ pycsw-admin.py -c export_records -f default.cfg -p /path/to/output_dir
