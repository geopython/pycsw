.. _outputschemas:

Output Schema Plugins
=====================

Overview
--------

pycsw allows for extending the implementation of output schemas to the core standard.  outputschemas allow for a client to request metadata in a specific format (ISO, Dublin Core, FGDC, NASA DIF Atom and GM03 are default).

All outputschemas must be placed in the ``pycsw/plugins/outputschemas`` directory.

Requirements
------------

.. code-block:: none

   pycsw/
     plugins/
     __init__.py # empty
     outputschemas/
       __init__.py # __all__ is a list of all provided outputschemas
       atom.py # default
       dif.py # default
       fgdc.py # default
       gm03.py # default

Implementing a new outputschema
-------------------------------

Create a file in ``pycsw/plugins/outputschemas``, which defines the following:

- ``NAMESPACE``: the default namespace of the outputschema which will be advertised
- ``NAMESPACE``: dict of all applicable namespaces to outputschema
- ``XPATH_MAPPINGS``: dict of pycsw core queryables mapped to the equivalent XPath of the outputschema
- ``write_record``: function which returns a record as an ``lxml.etree.Element`` object

Add the name of the file to ``__init__.py:__all__``.  The new outputschema is now supported in pycsw.

Testing
-------

New outputschemas must add examples to the :ref:`tests` interface, which must provide example requests specific to the profile.
