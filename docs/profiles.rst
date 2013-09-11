.. _profiles:

Profile Plugins
===============

Overview
--------

pycsw allows for the implementation of profiles to the core standard. Profiles allow specification of additional metadata format types (i.e. ISO 19139:2007, NASA DIF, INSPIRE, etc.) to the repository, which can be queried and presented to the client.  pycsw supports a plugin architecture which allows for runtime loading of Python code.

All profiles must be placed in the ``pycsw/plugins/profiles`` directory.

Requirements
------------

.. code-block:: none

   pycsw/
     plugins/
     __init__.py # empty
     profiles/ # directory to store profiles
       __init__.py # empty
       profile.py # defines abstract profile object (properties and methods) and functions to load plugins
       apiso/ # profile directory
         __init__.py # empty
         apiso.py # profile code
         ... # supporting files, etc.

Abstract Base Class Definition
------------------------------

All profile code must be instantiated as a subclass of ``profile.Profile``.  Below is an example to add a ``Foo`` profile:

.. code-block:: python

   from pycsw.plugins.profiles import profile

   class FooProfile(profile.Profile):
       profile.Profile.__init__(self,
           name='foo',
           version='1.0.3',
           title='My Foo Profile',
           url='http://example.org/fooprofile/docs',
           namespace='http://example.org/foons',
           typename='foo:RootElement',
           outputschema=http://example.org/foons',
           prefixes=['foo'],
           model=model,
           core_namespaces=namespaces,
           added_namespaces={'foo': 'http://example.org/foons'}
           repository=REPOSITORY['foo:RootElement'])

Your profile plugin class (``FooProfile``) must implement all methods as per ``profile.Profile``.  Profile methods must always return ``lxml.etree.Element`` types, or ``None``.

Enabling Profiles
-----------------

All profiles are disabled by default.  To specify profiles at runtime, set the ``server.profiles`` value in the :ref:`configuration` to the name of the package (in the ``pycsw/plugins/profiles`` directory).  To enable multiple profiles, specify as a comma separated value (see :ref:`configuration`).

Testing
-------

Profiles must add examples to the :ref:`tests` interface, which must provide example requests specific to the profile.

Supported Profiles
==================

.. include:: ../pycsw/plugins/profiles/apiso/docs/apiso.rst
.. include:: ../pycsw/plugins/profiles/ebrim/docs/ebrim.rst
