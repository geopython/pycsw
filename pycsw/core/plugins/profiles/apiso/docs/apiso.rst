.. _apiso:

ISO Metadata Application Profile (1.0.0)
----------------------------------------

Overview
^^^^^^^^
The ISO Metadata Application Profile (APISO) is a profile of CSW 2.0.2 which enables discovery of geospatial metadata following ISO 19139:2007 and ISO 19119:2005/PDAM 1.

Configuration
^^^^^^^^^^^^^

No extra configuration is required.

Querying
^^^^^^^^

 * **typename**: ``gmd:MD_Metadata``
 * **outputschema**: ``http://www.isotc211.org/2005/gmd``

Enabling APISO Support
^^^^^^^^^^^^^^^^^^^^^^

To enable APISO support, add ``apiso`` to ``server.profiles`` as specified in :ref:`configuration`.

Testing
^^^^^^^

A testing interface is available in ``tests/index.html`` which contains tests specific to APISO to demonstrate functionality.  See :ref:`tests` for more information.

INSPIRE Extension
-----------------

Overview
^^^^^^^^

APISO includes an extension for enabling `INSPIRE Discovery Services 3.0`_ support.  To enable the INSPIRE extension to APISO, create a ``[metadata:inspire]`` section in the main configuration with ``enabled`` set to ``true``.

Configuration
^^^^^^^^^^^^^

**[metadata:inspire]**

- **enabled**: whether to enable the INSPIRE extension (``true`` or ``false``)
- **languages_supported**: supported languages (see http://inspire.ec.europa.eu/schemas/common/1.0/enums/enum_eng.xsd, simpleType ``euLanguageISO6392B``)
- **default_language**: the default language (see http://inspire.ec.europa.eu/schemas/common/1.0/enums/enum_eng.xsd, simpleType ``euLanguageISO6392B``)
- **date**: date of INSPIRE metadata offering (in `ISO 8601`_ format)
- **gemet_keywords**: a comma-seperated keyword list of `GEMET INSPIRE theme keywords`_ about the service (see http://inspire.ec.europa.eu/schemas/common/1.0/enums/enum_eng.xsd, complexType ``inspireTheme_eng``)
- **conformity_service**: the level of INSPIRE conformance for spatial data sets and services (``conformant``, ``notConformant``, ``notEvaluated``)
- **contact_organization**: the organization name responsible for the INSPIRE metadata
- **contact_email**: the email address of entity responsible for the INSPIRE metadata
- **temp_extent**: temporal extent of the service (in `ISO 8601`_ format).  Either a single date (i.e. ``yyyy-mm-dd``), or an extent (i.e. ``yyyy-mm-dd/yyyy-mm-dd``)

.. _`INSPIRE Discovery Services 3.0`: http://inspire.jrc.ec.europa.eu/documents/Network_Services/TechnicalGuidance_DiscoveryServices_v3.0.pdf
.. _`GEMET INSPIRE theme keywords`: http://www.eionet.europa.eu/gemet/inspire_themes
.. _`ISO 8601`: http://en.wikipedia.org/wiki/ISO_8601
