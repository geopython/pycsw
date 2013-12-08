.. _repofilters:

Repository Filters
==================

pycsw has the ability to perform server side repository / database filters as a means to mask all CSW requests to query against a specific subset of the metadata repository, thus providing the ability to deploy multiple pycsw instances pointing to the same database in different ways via the ``repository.filter`` configuration option.

Repository filters are a convenient way to subset your repository at the server level without the hassle of creating proper database views.  For large repositories, it may be better to subset at the database level for performance.

Scenario: One Database, Many Views
----------------------------------

Imagine a sample database table of records (subset below for brevity):

.. csv-table::
  :header: identifier,parentidentifier,title,abstract

  1,33,foo1,bar1
  2,33,foo2,bar2
  3,55,foo3,bar3
  4,55,foo1,bar1
  5,21,foo5,bar5
  5,21,foo6,bar6

A default pycsw instance (with no ``repository.filters`` option) will always process CSW requests against the entire table.  So a CSW `GetRecords` filter like:

.. code-block:: xml

  <ogc:Filter>
      <ogc:PropertyIsEqualTo>
          <ogc:PropertyName>apiso:Title</ogc:PropertyName>
          <ogc:Literal>foo1</ogc:Literal>
      </ogc:PropertyIsEqualTo>
  </ogc:Filter>

...will return:

.. csv-table::
  :header: identifier,parentidentifier,title,abstract

  1,33,foo1,bar1
  4,55,foo1,bar1

Suppose you wanted to deploy another pycsw instance which serves metadata from the same database, but only from a specific subset.  Here we set the ``repository.filter`` option:

.. code-block:: text

  [repository]
  database=sqlite:///records.db
  filter=pycsw:ParentIdentifier = '33'

The same CSW `GetRecords` filter as per above then yields the following results:

.. csv-table::
  :header: identifier,parentidentifier,title,abstract

  1,33,foo1,bar1

Another example:

.. code-block:: text

  [repository]
  database=sqlite:///records.db
  filter=pycsw:ParentIdentifier != '33'

The same CSW `GetRecords` filter as per above then yields the following results:

.. csv-table::
  :header: identifier,parentidentifier,title,abstract

  4,55,foo1,bar1

The ``repository.filter`` option accepts all core queryables set in the pycsw core model (see ``pycsw.config.StaticContext.md_core_model`` for the complete list).
