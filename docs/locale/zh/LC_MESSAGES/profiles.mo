��    +      t              �     �  �   �  S   v  T   �  C     �   c  L   �  �   F  �     6   �  A   �  �   )  !   �  $   �  �     �   �  �   `	     C
  z   b
  +  �
  H   	  9   R     �     �     �     �     �  (   �  #        9     B  v   R     �     �     �     �  �   �  �   �  c   3  c   �  �   �  Q  �  o  �     n  �   �  S     T   k  C   �  �     L   �  �   �  �   �  6   Q  A   �  �   �  !   n  $   �  �   �  �   [  �        �  z     +  ~  H   �  9   �     -     ;     R     d     {  (   �  #   �     �     �  v   �     j     s     �     �  �   �  �   *  c   �  c   8   �   �   Q  M!   **[metadata:inspire]** **conformity_service**: the level of INSPIRE conformance for spatial data sets and services (``conformant``, ``notConformant``, ``notEvaluated``) **contact_email**: the email address of entity responsible for the INSPIRE metadata **contact_organization**: the organization name responsible for the INSPIRE metadata **date**: date of INSPIRE metadata offering (in `ISO 8601`_ format) **default_language**: the default language (see http://inspire.ec.europa.eu/schemas/common/1.0/enums/enum_eng.xsd, simpleType ``euLanguageISO6392B``) **enabled**: whether to enable the INSPIRE extension (``true`` or ``false``) **gemet_keywords**: a comma-seperated keyword list of `GEMET INSPIRE theme keywords`_ about the service (see http://inspire.ec.europa.eu/schemas/common/1.0/enums/enum_eng.xsd, complexType ``inspireTheme_eng``) **languages_supported**: supported languages (see http://inspire.ec.europa.eu/schemas/common/1.0/enums/enum_eng.xsd, simpleType ``euLanguageISO6392B``) **outputschema**: ``http://www.isotc211.org/2005/gmd`` **outputschema**: ``urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0`` **temp_extent**: temporal extent of the service (in `ISO 8601`_ format).  Either a single date (i.e. ``yyyy-mm-dd``), or an extent (i.e. ``yyyy-mm-dd/yyyy-mm-dd``) **typename**: ``gmd:MD_Metadata`` **typename**: ``rim:RegistryObject`` A testing interface is available in ``tests/index.html`` which contains tests specific to APISO to demonstrate functionality.  See :ref:`tests` for more information. A testing interface is available in ``tests/index.html`` which contains tests specific to ebRIM to demonstrate functionality.  See :ref:`tests` for more information. APISO includes an extension for enabling `INSPIRE Discovery Services 3.0`_ support.  To enable the INSPIRE extension to APISO, create a ``[metadata:inspire]`` section in the main configuration with ``enabled`` set to ``true``. Abstract Base Class Definition All profile code must be instantiated as a subclass of ``profile.Profile``.  Below is an example to add a ``Foo`` profile: All profiles are disabled by default.  To specify profiles at runtime, set the ``server.profiles`` value in the :ref:`configuration` to the name of the package (in the ``pycsw/plugins/profiles`` directory).  To enable multiple profiles, specify as a comma separated value (see :ref:`configuration`). All profiles must be placed in the ``pycsw/plugins/profiles`` directory. CSW-ebRIM Registry Service - Part 1: ebRIM profile of CSW Configuration Enabling APISO Support Enabling Profiles Enabling ebRIM Support INSPIRE Extension ISO Metadata Application Profile (1.0.0) No extra configuration is required. Overview Profile Plugins Profiles must add examples to the :ref:`tests` interface, which must provide example requests specific to the profile. Querying Requirements Supported Profiles Testing The CSW-ebRIM Registry Service is a profile of CSW 2.0.2 which enables discovery of geospatial metadata following the ebXML information model. The ISO Metadata Application Profile (APISO) is a profile of CSW 2.0.2 which enables discovery of geospatial metadata following ISO 19139:2007 and ISO 19119:2005/PDAM 1. To enable APISO support, add ``apiso`` to ``server.profiles`` as specified in :ref:`configuration`. To enable ebRIM support, add ``ebrim`` to ``server.profiles`` as specified in :ref:`configuration`. Your profile plugin class (``FooProfile``) must implement all methods as per ``profile.Profile``.  Profile methods must always return ``lxml.etree.Element`` types, or ``None``. pycsw allows for the implementation of profiles to the core standard. Profiles allow specification of additional metadata format types (i.e. ISO 19139:2007, NASA DIF, INSPIRE, etc.) to the repository, which can be queried and presented to the client.  pycsw supports a plugin architecture which allows for runtime loading of Python code. Project-Id-Version: pycsw 2.0-dev
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2015-11-23 21:42+0800
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language-Team: zh <LL@li.org>
Plural-Forms: nplurals=2; plural=(n != 1)
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 1.3
 **[metadata:inspire]** **conformity_service**: the level of INSPIRE conformance for spatial data sets and services (``conformant``, ``notConformant``, ``notEvaluated``) **contact_email**: the email address of entity responsible for the INSPIRE metadata **contact_organization**: the organization name responsible for the INSPIRE metadata **date**: date of INSPIRE metadata offering (in `ISO 8601`_ format) **default_language**: the default language (see http://inspire.ec.europa.eu/schemas/common/1.0/enums/enum_eng.xsd, simpleType ``euLanguageISO6392B``) **enabled**: whether to enable the INSPIRE extension (``true`` or ``false``) **gemet_keywords**: a comma-seperated keyword list of `GEMET INSPIRE theme keywords`_ about the service (see http://inspire.ec.europa.eu/schemas/common/1.0/enums/enum_eng.xsd, complexType ``inspireTheme_eng``) **languages_supported**: supported languages (see http://inspire.ec.europa.eu/schemas/common/1.0/enums/enum_eng.xsd, simpleType ``euLanguageISO6392B``) **outputschema**: ``http://www.isotc211.org/2005/gmd`` **outputschema**: ``urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0`` **temp_extent**: temporal extent of the service (in `ISO 8601`_ format).  Either a single date (i.e. ``yyyy-mm-dd``), or an extent (i.e. ``yyyy-mm-dd/yyyy-mm-dd``) **typename**: ``gmd:MD_Metadata`` **typename**: ``rim:RegistryObject`` A testing interface is available in ``tests/index.html`` which contains tests specific to APISO to demonstrate functionality.  See :ref:`tests` for more information. A testing interface is available in ``tests/index.html`` which contains tests specific to ebRIM to demonstrate functionality.  See :ref:`tests` for more information. APISO includes an extension for enabling `INSPIRE Discovery Services 3.0`_ support.  To enable the INSPIRE extension to APISO, create a ``[metadata:inspire]`` section in the main configuration with ``enabled`` set to ``true``. Abstract Base Class Definition All profile code must be instantiated as a subclass of ``profile.Profile``.  Below is an example to add a ``Foo`` profile: All profiles are disabled by default.  To specify profiles at runtime, set the ``server.profiles`` value in the :ref:`configuration` to the name of the package (in the ``pycsw/plugins/profiles`` directory).  To enable multiple profiles, specify as a comma separated value (see :ref:`configuration`). All profiles must be placed in the ``pycsw/plugins/profiles`` directory. CSW-ebRIM Registry Service - Part 1: ebRIM profile of CSW Configuration Enabling APISO Support Enabling Profiles Enabling ebRIM Support INSPIRE Extension ISO Metadata Application Profile (1.0.0) No extra configuration is required. Overview Profile Plugins Profiles must add examples to the :ref:`tests` interface, which must provide example requests specific to the profile. Querying Requirements Supported Profiles Testing The CSW-ebRIM Registry Service is a profile of CSW 2.0.2 which enables discovery of geospatial metadata following the ebXML information model. The ISO Metadata Application Profile (APISO) is a profile of CSW 2.0.2 which enables discovery of geospatial metadata following ISO 19139:2007 and ISO 19119:2005/PDAM 1. To enable APISO support, add ``apiso`` to ``server.profiles`` as specified in :ref:`configuration`. To enable ebRIM support, add ``ebrim`` to ``server.profiles`` as specified in :ref:`configuration`. Your profile plugin class (``FooProfile``) must implement all methods as per ``profile.Profile``.  Profile methods must always return ``lxml.etree.Element`` types, or ``None``. pycsw allows for the implementation of profiles to the core standard. Profiles allow specification of additional metadata format types (i.e. ISO 19139:2007, NASA DIF, INSPIRE, etc.) to the repository, which can be queried and presented to the client.  pycsw supports a plugin architecture which allows for runtime loading of Python code. 