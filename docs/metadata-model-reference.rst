.. _metadata-model-reference:

Metadata Model Reference
========================

Overview
--------

Model Crosswalk
---------------

.. list-table:: pycsw model
   :widths: 20 20 20 20 20 20 20
   :header-rows: 1
   * - Database column
     - Mapping name
     - Queryable name
     - ISO 19115 (XPath)
     - CSW Record/Dublin Core (XPath)
     - OGC API - Records (JSONPath)
     - STAC (JSONPath)
   * - identifier
     - pycsw:Identifier
     - apiso:Identifier
     - gmd:fileIdentifier/gco:CharacterString
     - 
     - record.id
     - item.id