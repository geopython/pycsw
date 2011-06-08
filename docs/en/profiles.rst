.. _profiles:

Profile Plugins
===============

Overview
--------

pycsw allows for the implementation of profiles to the core standard. Profiles allow specification of additional metadata format types (i.e. ISO 19139:2007, NASA DIF, INSPIRE, etc.) to the repository, which can be queried and presented to the client.  pycsw supports a plugin architecture which allows for runtime loading of Python code.

All profiles must be placed in the ``server/profiles`` directory.

Requirements
------------

.. code-block:: none

   pycsw/
    server/
      profile.py # defines abstract profile object (properties and methods) and functions to load plugins
      profiles/ # directory to store profiles
        __init__.py # empty
        apiso/ # profile directory
          apiso.py # profile code
          ... # supporting files, etc.

Abstract Base Class Definition
------------------------------

All profile code must be instantiated as a subclass of ``profile.Profile``.  For example:

.. code-block:: python

   from server import profile

   class FooProfile(profile.Profile):
       profile.Profile.__init__(self, 'foo', '1.0.0', 'My Profile', 'http://example.org/', 'http://example.org/foons', 'foo:TypeName', 'http://example.org/foons')

Your profile plugin class (``FooProfile``) must implement all methods as per ``profile.Profile``.  Profile methods must always return ``lxml.etree.Element`` types, or ``None``.

Enabling Profiles
-----------------

All profiles are disabled by default.  To specify profiles at runtime, set the ``server.profiles`` value in the :ref:`configuration` to the name of the package (in the ``server/profiles`` directory).  To enable multiple profiles, specify as a comma separated value (see :ref:`configuration`).

Testing
-------

Profiles must add examples to the :ref:`tester` interface, which must provide example requests specific to the profile.

Supported Profiles
==================

.. include:: ../../server/profiles/apiso/docs/apiso.rst
