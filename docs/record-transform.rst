.. _record-transform:

Record Transform
================

pycsw supports a configurable record transform hook that allows post-processing
of metadata records before they are serialized into any output format.  This
provides a single, unified intervention point that applies to all supported
protocols and output formats:

- OGC API - Records (JSON and HTML)
- OGC API - Records (application/xml)
- CSW 2.0.2 and CSW 3.0 (XML, all output schemas and profiles)

Common use cases include:

- Removing internal or private keywords before returning records to clients
- Redacting sensitive field values
- Normalizing or enriching output fields

Configuration
-------------

Set ``server.record_transform`` in the pycsw configuration file to the path of
a Python file or a dotted module name:

.. code-block:: yaml

   server:
       record_transform: /etc/pycsw/transform.py

The referenced file or module must define a callable named ``record_transform``.

Docker
------

The transform file can be injected into a container using a bind mount:

.. code-block:: yaml

   # docker-compose.yml
   services:
     pycsw:
       volumes:
         - ./my_transform.py:/etc/pycsw/transform.py

Writing a transform
-------------------

The ``record_transform`` callable receives a pycsw record object (a SQLAlchemy
ORM instance whose attributes correspond to the pycsw core metadata model) and
must return the same object (optionally modified).

How serialization works determines which fields you need to modify:

.. list-table::
   :header-rows: 1
   :widths: 35 35 30

   * - Output format
     - Reads from
     - What to modify
   * - OGC API JSON
     - Individual fields
     - ``record.keywords``, ``record.title``, …
   * - OGC API HTML
     - Individual fields
     - ``record.keywords``, ``record.title``, …
   * - OGC API ``application/xml``
     - ``record.xml``
     - ``record.xml``
   * - CSW XML
     - Individual fields (see note)
     - ``record.keywords``, ``record.title``, …
   * - CSW JSON
     - Individual fields
     - ``record.keywords``, ``record.title``, …

.. note::

   **CSW XML exception:** when ``elementSetName=full`` is requested and
   ``record.xml`` contains a native ISO format (ISO 19139 or ISO 19115-3),
   pycsw returns ``record.xml`` directly instead of re-serializing from
   individual fields.  In that case, modify ``record.xml`` as well to affect
   those responses.

**Modifying ORM fields**

Changing ORM attributes is sufficient for OGC API JSON, OGC API HTML, and all
CSW responses, because those serializers read directly from the record object's
fields:

.. code-block:: python

   # /etc/pycsw/transform.py

   def record_transform(record):
       """Remove keywords prefixed with '_internal_' from all responses."""
       if record.keywords:
           record.keywords = ','.join(
               kw for kw in record.keywords.split(',')
               if not kw.strip().startswith('_internal_')
           )
       return record

Available record attributes follow the pycsw core metadata model (see
:ref:`metadata-model-reference`).  Common attributes include ``identifier``,
``title``, ``abstract``, ``keywords``, ``themes``, ``links``, and
``contacts``.

**Modifying the raw XML blob**

OGC API ``application/xml`` responses are served directly from ``record.xml``
— the original XML document as it was ingested — rather than re-serialized
from ORM fields.  ``record.xml`` may contain ISO 19139, Dublin Core, or any
other format that was submitted at ingest time.

To filter these responses the transform must also parse and rewrite
``record.xml`` using the namespace and element structure of the ingested
format.  The following example handles **ISO 19139** records:

.. code-block:: python

   # /etc/pycsw/transform.py (ISO 19139 example)

   from lxml import etree

   _PREFIXES = ('source:', 'catalog:', 'organisation:', 'transaction:', 'sub_organisation:')

   _NS = {
       'gmd': 'http://www.isotc211.org/2005/gmd',
       'gco': 'http://www.isotc211.org/2005/gco',
   }

   def record_transform(record):
       # Filter the flat keyword column (OGC API JSON/HTML, CSW XML)
       if record.keywords:
           record.keywords = ','.join(
               kw for kw in record.keywords.split(',')
               if not kw.strip().startswith(_PREFIXES)
           )

       # Filter the raw XML blob (OGC API application/xml; CSW ISO full)
       if record.xml:
           try:
               xml_in = record.xml if isinstance(record.xml, bytes) else record.xml.encode('utf-8')
               root = etree.fromstring(xml_in)
               for md_kw in root.findall('.//gmd:MD_Keywords', _NS):
                   for kw_el in md_kw.findall('gmd:keyword', _NS):
                       cs = kw_el.find('gco:CharacterString', _NS)
                       if cs is not None and cs.text and cs.text.strip().startswith(_PREFIXES):
                           md_kw.remove(kw_el)
                   if not md_kw.findall('gmd:keyword', _NS):
                       parent = md_kw.getparent()
                       if parent is not None:
                           parent.getparent().remove(parent)
               record.xml = etree.tostring(root, encoding='unicode')
           except Exception:
               pass

       return record

For Dublin Core records, keywords are stored in ``dc:subject`` elements and
the namespace handling must be adapted accordingly.

.. warning::

   **Security and trust model**

   The transform file is executed as Python code with the same OS privileges as
   the pycsw process.  It has unrestricted access to the filesystem, network,
   environment variables, and the database.

   pycsw itself never commits the SQLAlchemy session after a read request, so
   ordinary attribute modifications (``record.keywords = …``) do not persist to
   the database in normal usage. However, a transform function **can** access
   the live session via ``sqlalchemy.orm.object_session(record)`` and call
   ``session.commit()`` explicitly, which **does** write to the database.

   Treat the transform file as trusted administrator code — equivalent to
   pycsw's own application code.  It must be controlled exclusively by the
   system administrator and must never be loaded from an untrusted source or
   influenced by API clients.

Using a dotted module path
--------------------------

If the transform module is installed as a Python package and is accessible on
the ``PYTHONPATH``, you may also specify it as a dotted module path:

.. code-block:: yaml

   server:
       record_transform: mypackage.transforms.record_transform
