.. _repositories:

Repository Plugins
==================

Overview
--------

pycsw allows for the implementation of custom repositories in order to connect to a backend different from the pycsw's default.  This is especially useful when downstream applications manage their own metadata model/database/document store and want pycsw to connect to it directly instead of using pycsw's default model, thus creating duplicate repositories which then require syncronization/accounting.  Repository plugins enable a single metadata backend which is independent from the pycsw setup.  pycsw thereby becomes a pure wrapper around a given backend in providing CSW and other APIs atop a given application.

All outputschemas must be placed in the ``pycsw/plugins/outputschemas`` directory.

Requirements
------------

Repository plugins:

- can be developed and referenced / connected external to pycsw
- must be accessible within the ``PYTHONPATH`` of a given application
- must implement pycsw's ``pycsw.core.repository.Repository`` properties and methods
- must be specified in the pycsw :ref:`configuration` as a class reference (e.g. ``path.to.repo_plugin.MyRepository``)
- must minimally implement the ``query_insert``, ``query_domain``, ``query_ids``, and ``query`` methods

Configuration
-------------

- set pycsw's ``repository.source`` setting to the class which implements the custom repository:

.. code-block:: none

  [repository]
  mappings='path.to.repo_plugin.MyRepository'
