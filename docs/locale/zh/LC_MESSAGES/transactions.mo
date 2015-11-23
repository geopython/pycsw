��    1      �              ,  <   -  ;   j  h   �  U        e     q  s   v  �   �  a   �  �   �     y  
   �  	   �     �  	   �     �     �     �     �     �     �     �               )  0   B     s  �          �   '  W  �  O   3
     �
  $   �
  $   �
  (   �
  (   �
  "   &  "   I     l     �     �  $   �     �  "     ]   #  �  �     O  o  S  <   �  ;      h   <  U   �     �       s     �   �  a     �   z       
     	   "     ,  	   4     >     O     ]     k     y     �     �     �     �     �  0   �     	  �        �  �   �  W  q  O   �       $      $   E  (   j  (   �  "   �  "   �          !     @  $   _     �  "  �  ]   �  �       �   **Delete**: deletes can be made against a ``csw:Constraint`` **Insert**: full XML documents can be inserted as per CSW-T **Update**: updates can be made as full record updates or record properties against a ``csw:Constraint`` Additional metadata models are supported by enabling the appropriate :ref:`profiles`. Dublin Core FGDC For CSW-T deployments, it is strongly advised that this directory reside in an area that is not accessible by HTTP. For ``csw:ResponseHandler`` values using the ``mailto:`` protocol, you must have ``server.smtp_host`` set in your :ref:`configuration <configuration>`. For transactions and harvesting, pycsw supports the following metadata resource types by default: For transactions to be functional when using SQLite3, the SQLite3 database file (**and its parent directory**) must be fully writable.  For example: Harvest Harvesting ISO 19139 ISO GMI Namespace OGC Web Services OGC:CSW 2.0.2 OGC:SOS 1.0.0 OGC:SOS 2.0.0 OGC:WCS 1.0.0 OGC:WFS 1.1.0 OGC:WMS 1.1.1 OGC:WPS 1.0.0 Resource Type Supported Resource Types The :ref:`tests` contain CSW-T request examples. Transaction Transaction operation results can be sent by email (via ``mailto:``) or ftp (via ``ftp://``) if the Transaction request specifies ``csw:ResponseHandler``. Transactions When harvesting OGC web services, requests can provide the base URL of the service as part of the Harvest request.  pycsw will construct a ``GetCapabilities`` request dynamically. When harvesting other CSW servers, pycsw pages through the entire CSW in default increments of 10.  This value can be modified via the ``manager.csw_harvest_pagesize`` :ref:`configuration <configuration>` option.  It is strongly advised to use the ``csw:ResponseHandler`` parameter for harvesting large CSW catalogues to prevent HTTP timeouts. Your server must be able to make outgoing HTTP requests for this functionality. `WAF`_ ``http://www.isotc211.org/2005/gmd`` ``http://www.isotc211.org/2005/gmi`` ``http://www.opengis.net/cat/csw/2.0.2`` ``http://www.opengis.net/cat/csw/csdgm`` ``http://www.opengis.net/sos/1.0`` ``http://www.opengis.net/sos/2.0`` ``http://www.opengis.net/wcs`` ``http://www.opengis.net/wfs`` ``http://www.opengis.net/wms`` ``http://www.opengis.net/wps/1.0.0`` ``urn:geoss:urn`` pycsw has the ability to process CSW Harvest and Transaction requests (CSW-T).  Transactions are disabled by default; to enable, ``manager.transactions`` must be set to ``true``.  Access to transactional functionality is limited to IP addresses which must be set in ``manager.allowed_ips``. pycsw supports 3 modes of the ``Transaction`` operation (``Insert``, ``Update``, ``Delete``): pycsw supports the CSW-T ``Harvest`` operation.  Records which are harvested require to setup a cronjob to periodically refresh records in the local repository.  A sample cronjob is available in ``etc/harvest-all.cron`` which points to ``pycsw-admin.py`` (you must specify the correct path to your configuration).  Harvest operation results can be sent by email (via ``mailto:``) or ftp (via ``ftp://``) if the Harvest request specifies ``csw:ResponseHandler``. yes Project-Id-Version: pycsw 2.0-dev
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
 **Delete**: deletes can be made against a ``csw:Constraint`` **Insert**: full XML documents can be inserted as per CSW-T **Update**: updates can be made as full record updates or record properties against a ``csw:Constraint`` Additional metadata models are supported by enabling the appropriate :ref:`profiles`. Dublin Core FGDC For CSW-T deployments, it is strongly advised that this directory reside in an area that is not accessible by HTTP. For ``csw:ResponseHandler`` values using the ``mailto:`` protocol, you must have ``server.smtp_host`` set in your :ref:`configuration <configuration>`. For transactions and harvesting, pycsw supports the following metadata resource types by default: For transactions to be functional when using SQLite3, the SQLite3 database file (**and its parent directory**) must be fully writable.  For example: Harvest Harvesting ISO 19139 ISO GMI Namespace OGC Web Services OGC:CSW 2.0.2 OGC:SOS 1.0.0 OGC:SOS 2.0.0 OGC:WCS 1.0.0 OGC:WFS 1.1.0 OGC:WMS 1.1.1 OGC:WPS 1.0.0 Resource Type Supported Resource Types The :ref:`tests` contain CSW-T request examples. Transaction Transaction operation results can be sent by email (via ``mailto:``) or ftp (via ``ftp://``) if the Transaction request specifies ``csw:ResponseHandler``. Transactions When harvesting OGC web services, requests can provide the base URL of the service as part of the Harvest request.  pycsw will construct a ``GetCapabilities`` request dynamically. When harvesting other CSW servers, pycsw pages through the entire CSW in default increments of 10.  This value can be modified via the ``manager.csw_harvest_pagesize`` :ref:`configuration <configuration>` option.  It is strongly advised to use the ``csw:ResponseHandler`` parameter for harvesting large CSW catalogues to prevent HTTP timeouts. Your server must be able to make outgoing HTTP requests for this functionality. `WAF`_ ``http://www.isotc211.org/2005/gmd`` ``http://www.isotc211.org/2005/gmi`` ``http://www.opengis.net/cat/csw/2.0.2`` ``http://www.opengis.net/cat/csw/csdgm`` ``http://www.opengis.net/sos/1.0`` ``http://www.opengis.net/sos/2.0`` ``http://www.opengis.net/wcs`` ``http://www.opengis.net/wfs`` ``http://www.opengis.net/wms`` ``http://www.opengis.net/wps/1.0.0`` ``urn:geoss:urn`` pycsw has the ability to process CSW Harvest and Transaction requests (CSW-T).  Transactions are disabled by default; to enable, ``manager.transactions`` must be set to ``true``.  Access to transactional functionality is limited to IP addresses which must be set in ``manager.allowed_ips``. pycsw supports 3 modes of the ``Transaction`` operation (``Insert``, ``Update``, ``Delete``): pycsw supports the CSW-T ``Harvest`` operation.  Records which are harvested require to setup a cronjob to periodically refresh records in the local repository.  A sample cronjob is available in ``etc/harvest-all.cron`` which points to ``pycsw-admin.py`` (you must specify the correct path to your configuration).  Harvest operation results can be sent by email (via ``mailto:``) or ftp (via ``ftp://``) if the Harvest request specifies ``csw:ResponseHandler``. yes 