.. _xslt:

XSLT Support
============

By default, pycsw performs metadata transformations using a generic framework
that attempts to cover generic use cases.  pycsw users can also specify custom
XSLT transformations for specific use cases or communities.

To specify a custom XSLT transformation, you must map to input and output
outputschemas supported by pycsw, where the input outputschema must match
the metadata as ingested and stored in the repository.

.. code-block:: ini 

   # custom XSLT (section format: xslt:input_xml_schema,output_xml_schema)
   [xslt:http://www.opengis.net/cat/csw/2.0.2,http://www.isotc211.org/2005/gmd]
   xslt=/path/to/my-custom-iso.xslt

The ``xslt`` directive must point to a valid XSLT document on disk.

.. note::

  You may also use environment variables to point to XSLT files.
