.. _xslt:

XSLT Support
============

By default, pycsw performs metadata transformations using a generic framework
that attempts to cover generic use cases.  pycsw users can also specify custom
XSLT transformations for specific use cases or communities.

To specify a custom XSLT transformation, you must map to input and output
outputschemas supported by pycsw, where the input outputschema must match
the metadata as ingested and stored in the repository.

.. code-block:: yaml

   xslt:
       - input_os: http://www.opengis.net/cat/csw/2.0.2
         output_os: http://www.isotc211.org/2005/gmd
         transform: tests/functionaltests/suites/xslt/custom.xslt


The ``xslt`` directive must point to a valid XSLT document on disk.

.. note::

  You may also use environment variables to point to XSLT files.
