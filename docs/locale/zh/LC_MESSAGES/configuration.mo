��    N      �              �     �               0  �   =  8   
  2   C  8   v  <   �  =   �  ?   *  A   j  2   �  ;   �  @     ?   \  x  �  N   
  G   d
  y   �
  �   &  �   �  �   a  �   �  �   �  e   9  b   �  +     D   .  T   s  9   �  O       R  2   b  }   �  .     `   B  G   �  �   �  9   �  m     c   �  i   �  3   X  1   �  �   �  �   ?  �   �  �   �  y   �  )   �     %     6     :     =     @     D  �   ]  8   �  [  .     �     �     �     �     �  �   �     �  c   �  �     u   �  e   F     �     �     �  &  �  �   �      �!  o  �!     3#     A#     U#     f#  �   s#  8   @$  2   y$  8   �$  <   �$  =   "%  ?   `%  A   �%  2   �%  ;   &  @   Q&  ?   �&  x  �&  N   K(  G   �(  y   �(  �   \)  �   �)  �   �*  �   .+  �   �+  e   o,  b   �,  +   8-  D   d-  T   �-  9   �-  O   8.    �.  2   �/  }   �/  .   I0  `   x0  G   �0  �   !1  9   2  m   R2  c   �2  i   $3  3   �3  1   �3  �   �3  �   u4  �   �4  �   �5  y   �6  )   17     [7     l7     p7     s7     v7     z7  �   �7  8   +8  [  d8     �:     �:     �:     �:     ;  �   ";     �;  c   �;  �   R<  u   =  e   |=     �=     �=     �=  &  >  �   -?     �?   **[manager]** **[metadata:main]** **[repository]** **[server]** **allowed_ips**: comma delimited list of IP addresses (e.g. 192.168.0.103), wildcards (e.g. 192.168.0.*) or CIDR notations (e.g. 192.168.100.0/24) allowed to perform transactions (see :ref:`transactions`) **contact_address**: the address of the provider contact **contact_city**: the city of the provider contact **contact_country**: the country of the provider contact **contact_email**: the email address of the provider contact **contact_fax**: the facsimile number of the provider contact **contact_hours**: the hours of service to contact the provider **contact_instructions**: the how to contact the provider contact **contact_name**: the name of the provider contact **contact_phone**: the phone number of the provider contact **contact_position**: the position title of the provider contact **contact_postalcode**: the postal code of the provider contact **contact_role**: the role of the provider contact as per the `ISO 19115 CI_RoleCode codelist <http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode>`_).  Accepted values are ``author``, ``processor``, ``publisher``, ``custodian``, ``pointOfContact``, ``distributor``, ``user``, ``resourceProvider``, ``originator``, ``owner``, ``principalInvestigator`` **contact_stateorprovince**: the province or territory of the provider contact **contact_url**: the URL to more information about the provider contact **csw_harvest_pagesize**: when harvesting other CSW servers, the number of records per request to page by (default is 10) **database**: the full file path to the metadata database, in database URL format (see http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls) **domaincounts**: for GetDomain operations, whether to provide frequency counts for values.  Accepted values are ``true`` and ``False``. Default is ``false`` **domainquerytype**: for GetDomain operations, how to output domain values.  Accepted values are ``list`` and ``range`` (min/max). Default is ``list`` **encoding**: the content type encoding (e.g. ``ISO-8859-1``, see https://docs.python.org/2/library/codecs.html#standard-encodings).  Default value is 'UTF-8' **federatedcatalogues**: comma delimited list of CSW endpoints to be used for distributed searching, if requested by the client (see :ref:`distributedsearching`) **filter**: server side database filter to apply as mask to all CSW requests (see :ref:`repofilters`) **gzip_compresslevel**: gzip compression level, lowest is ``1``, highest is ``9``.  Default is off **home**: the full filesystem path to pycsw **identification_abstract**: some descriptive text about the service **identification_accessconstraints**: access constraints associated with the service **identification_fees**: fees associated with the service **identification_keywords**: comma delimited list of keywords about the service **identification_keywords_type**: keyword type as per the `ISO 19115 MD_KeywordTypeCode codelist <http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_KeywordTypeCode>`_).  Accepted values are ``discipline``, ``temporal``, ``place``, ``theme``, ``stratum`` **identification_title**: the title of the service **language**: the ISO 639-1 language and ISO 3166-1 alpha2 country code of the service (e.g. ``en-CA``, ``fr-CA``, ``en-US``) **logfile**: the full file path to the logfile **loglevel**: the logging level (see http://docs.python.org/library/logging.html#logging-levels) **mappings**: custom repository mappings (see :ref:`custom_repository`) **maxrecords**: the maximum number of records to return by default.  This value is enforced if a CSW's client's ``maxRecords`` parameter is greater than ``server.maxrecords`` to limit capacity.  See :ref:`maxrecords-handling` for more information **mimetype**: the MIME type when returning HTTP responses **ogc_schemas_base**: base URL of OGC XML schemas tree file structure (default is http://schemas.opengis.net) **pretty_print**: whether to pretty print the output (``true`` or ``false``).  Default is ``false`` **profiles**: comma delimited list of profiles to load at runtime (default is none).  See :ref:`profiles` **provider_name**: the name of the service provider **provider_url**: the URL of the service provider **smtp_host**: SMTP host for processing ``csw:ResponseHandler`` parameter via outgoing email requests (default is ``localhost``) **source**: the source of this repository only if not local (e.g. :ref:`geonode`, :ref:`odc`).  Supported values are ``geonode``, ``odc`` **spatial_ranking**: parameter that enables (``true`` or ``false``) ranking of spatial query results as per `K.J. Lanfear 2006 - A Spatial Overlay Ranking Method for a Geospatial Search of Text Objects  <http://pubs.usgs.gov/of/2006/1279/2006-1279.pdf>`_. **table**: the table name for metadata records (default is ``records``).  If you are using PostgreSQL with a DB schema other than ``public``, qualify the table like ``myschema.table`` **transactions**: whether to enable transactions (``true`` or ``false``).  Default is ``false`` (see :ref:`transactions`) **url**: the URL of the resulting service 10 (CSW default) 100 14 20 200 Alternate Configurations Another option is to write a simple wrapper (e.g. ``csw-foo.sh``), which provides the same functionality and can be deployed without restarting Apache: Apache must be restarted after changes to ``httpd.conf`` By default, pycsw loads ``default.cfg`` at runtime.  To load an alternate configuration, modify ``csw.py`` to point to the desired configuration.  Alternatively, pycsw supports explicitly specifiying a configuration by appending ``config=/path/to/default.cfg`` to the base URL of the service (e.g. ``http://localhost/pycsw/csw.py?config=tests/suites/default/default.cfg&service=CSW&version=2.0.2&request=GetCapabilities``).  When the ``config`` parameter is passed by a CSW client, pycsw will override the default configuration location and subsequent settings with those of the specified configuration. Configuration Environment Variables GetRecords.maxRecords Hiding the Location MaxRecords Handling One option is using Apache's ``Alias`` and ``SetEnvIf`` directives.  For example, given the base URL ``http://localhost/pycsw/csw.py?config=foo.cfg``, set the following in Apache's ``httpd.conf``: Result See :ref:`administration` for connecting your metadata repository and supported information models. Some deployments with alternate configurations prefer not to advertise the base URL with the ``config=`` approach.  In this case, there are many options to advertise the base URL. The The following describes how ``maxRecords`` is handled by the configuration when handling ``GetRecords`` requests: This also provides the functionality to deploy numerous CSW servers with a single pycsw installation. Wrapper Script none passed none set pycsw will use the configuration as set in the ``PYCSW_CONFIG`` environment variable in the same manner as if it was specified in the base URL.  Note that the configuration value ``server.url`` value must match the ``Request_URI`` value so as to advertise correctly in pycsw's Capabilities XML. pycsw's runtime configuration is defined by ``default.cfg``.  pycsw ships with a sample configuration (``default-sample.cfg``).  Copy the file to ``default.cfg`` and edit the following: server.maxrecords Project-Id-Version: pycsw 2.0-dev
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
 **[manager]** **[metadata:main]** **[repository]** **[server]** **allowed_ips**: comma delimited list of IP addresses (e.g. 192.168.0.103), wildcards (e.g. 192.168.0.*) or CIDR notations (e.g. 192.168.100.0/24) allowed to perform transactions (see :ref:`transactions`) **contact_address**: the address of the provider contact **contact_city**: the city of the provider contact **contact_country**: the country of the provider contact **contact_email**: the email address of the provider contact **contact_fax**: the facsimile number of the provider contact **contact_hours**: the hours of service to contact the provider **contact_instructions**: the how to contact the provider contact **contact_name**: the name of the provider contact **contact_phone**: the phone number of the provider contact **contact_position**: the position title of the provider contact **contact_postalcode**: the postal code of the provider contact **contact_role**: the role of the provider contact as per the `ISO 19115 CI_RoleCode codelist <http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode>`_).  Accepted values are ``author``, ``processor``, ``publisher``, ``custodian``, ``pointOfContact``, ``distributor``, ``user``, ``resourceProvider``, ``originator``, ``owner``, ``principalInvestigator`` **contact_stateorprovince**: the province or territory of the provider contact **contact_url**: the URL to more information about the provider contact **csw_harvest_pagesize**: when harvesting other CSW servers, the number of records per request to page by (default is 10) **database**: the full file path to the metadata database, in database URL format (see http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls) **domaincounts**: for GetDomain operations, whether to provide frequency counts for values.  Accepted values are ``true`` and ``False``. Default is ``false`` **domainquerytype**: for GetDomain operations, how to output domain values.  Accepted values are ``list`` and ``range`` (min/max). Default is ``list`` **encoding**: the content type encoding (e.g. ``ISO-8859-1``, see https://docs.python.org/2/library/codecs.html#standard-encodings).  Default value is 'UTF-8' **federatedcatalogues**: comma delimited list of CSW endpoints to be used for distributed searching, if requested by the client (see :ref:`distributedsearching`) **filter**: server side database filter to apply as mask to all CSW requests (see :ref:`repofilters`) **gzip_compresslevel**: gzip compression level, lowest is ``1``, highest is ``9``.  Default is off **home**: the full filesystem path to pycsw **identification_abstract**: some descriptive text about the service **identification_accessconstraints**: access constraints associated with the service **identification_fees**: fees associated with the service **identification_keywords**: comma delimited list of keywords about the service **identification_keywords_type**: keyword type as per the `ISO 19115 MD_KeywordTypeCode codelist <http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_KeywordTypeCode>`_).  Accepted values are ``discipline``, ``temporal``, ``place``, ``theme``, ``stratum`` **identification_title**: the title of the service **language**: the ISO 639-1 language and ISO 3166-1 alpha2 country code of the service (e.g. ``en-CA``, ``fr-CA``, ``en-US``) **logfile**: the full file path to the logfile **loglevel**: the logging level (see http://docs.python.org/library/logging.html#logging-levels) **mappings**: custom repository mappings (see :ref:`custom_repository`) **maxrecords**: the maximum number of records to return by default.  This value is enforced if a CSW's client's ``maxRecords`` parameter is greater than ``server.maxrecords`` to limit capacity.  See :ref:`maxrecords-handling` for more information **mimetype**: the MIME type when returning HTTP responses **ogc_schemas_base**: base URL of OGC XML schemas tree file structure (default is http://schemas.opengis.net) **pretty_print**: whether to pretty print the output (``true`` or ``false``).  Default is ``false`` **profiles**: comma delimited list of profiles to load at runtime (default is none).  See :ref:`profiles` **provider_name**: the name of the service provider **provider_url**: the URL of the service provider **smtp_host**: SMTP host for processing ``csw:ResponseHandler`` parameter via outgoing email requests (default is ``localhost``) **source**: the source of this repository only if not local (e.g. :ref:`geonode`, :ref:`odc`).  Supported values are ``geonode``, ``odc`` **spatial_ranking**: parameter that enables (``true`` or ``false``) ranking of spatial query results as per `K.J. Lanfear 2006 - A Spatial Overlay Ranking Method for a Geospatial Search of Text Objects  <http://pubs.usgs.gov/of/2006/1279/2006-1279.pdf>`_. **table**: the table name for metadata records (default is ``records``).  If you are using PostgreSQL with a DB schema other than ``public``, qualify the table like ``myschema.table`` **transactions**: whether to enable transactions (``true`` or ``false``).  Default is ``false`` (see :ref:`transactions`) **url**: the URL of the resulting service 10 (CSW default) 100 14 20 200 Alternate Configurations Another option is to write a simple wrapper (e.g. ``csw-foo.sh``), which provides the same functionality and can be deployed without restarting Apache: Apache must be restarted after changes to ``httpd.conf`` By default, pycsw loads ``default.cfg`` at runtime.  To load an alternate configuration, modify ``csw.py`` to point to the desired configuration.  Alternatively, pycsw supports explicitly specifiying a configuration by appending ``config=/path/to/default.cfg`` to the base URL of the service (e.g. ``http://localhost/pycsw/csw.py?config=tests/suites/default/default.cfg&service=CSW&version=2.0.2&request=GetCapabilities``).  When the ``config`` parameter is passed by a CSW client, pycsw will override the default configuration location and subsequent settings with those of the specified configuration. Configuration Environment Variables GetRecords.maxRecords Hiding the Location MaxRecords Handling One option is using Apache's ``Alias`` and ``SetEnvIf`` directives.  For example, given the base URL ``http://localhost/pycsw/csw.py?config=foo.cfg``, set the following in Apache's ``httpd.conf``: Result See :ref:`administration` for connecting your metadata repository and supported information models. Some deployments with alternate configurations prefer not to advertise the base URL with the ``config=`` approach.  In this case, there are many options to advertise the base URL. The The following describes how ``maxRecords`` is handled by the configuration when handling ``GetRecords`` requests: This also provides the functionality to deploy numerous CSW servers with a single pycsw installation. Wrapper Script none passed none set pycsw will use the configuration as set in the ``PYCSW_CONFIG`` environment variable in the same manner as if it was specified in the base URL.  Note that the configuration value ``server.url`` value must match the ``Request_URI`` value so as to advertise correctly in pycsw's Capabilities XML. pycsw's runtime configuration is defined by ``default.cfg``.  pycsw ships with a sample configuration (``default-sample.cfg``).  Copy the file to ``default.cfg`` and edit the following: server.maxrecords 