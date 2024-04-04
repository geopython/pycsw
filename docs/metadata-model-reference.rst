.. _metadata-model-reference:

Metadata Model Reference
========================

pycsw's metadata repository model is designed to support queryable elements as well full-text search.  The model
is rooted in ISO 19115 and is updated as required to be able to support additional metadata models in a generic
fashion.

Overview
--------

Model Crosswalk
---------------

.. list-table:: pycsw model
   :widths: 20 20 20 20 20 20 20 20
   :class: metadata-model-table
   :header-rows: 1

   * - Database column
     - pycsw mapping name
     - Queryable name
     - ISO 19115 (XPath)
     - CSW Record/Dublin Core (XPath)
     - OGC API - Records (JSONPath)
     - STAC (JSONPath)
     - Description
   * - ``identifier``
     - ``pycsw:Identifier``
     - ``apiso:Identifier``
     - ``gmd:fileIdentifier/gco:CharacterString``
     - ``dc:identifier``
     - ``id``
     - ``id``
     - Record identifier (Primary key)
   * - ``typename``
     - ``pycsw:Typename``
     - 
     - 
     - 
     - 
     - 
     - CSW typename (e.g. ``csw:Record``, ``gmd:MD_Metadata``), see also ref:`existing-repository-requirements`
   * - ``schema``
     - ``pycsw:Schema``
     - 
     - 
     - 
     - 
     - 
     - Schema namespace, i.e. http://www.opengis.net/cat/csw/2.0.2, http://www.isotc211.org/2005/gmd, http://www.opengis.net/spec/ogcapi-records-1/1.0/req/record-core
   * - ``mdsource``
     - ``pycsw:MdSource``
     - 
     - 
     - 
     - 
     - 
     - Origin of resource, either ``local`` (default), or URL to location of record/resource/service
   * - ``insert_date``
     - ```pycsw:InsertDate``
     - 
     - 
     - 
     -
     - 
     - Date of insertion of the metadata record, see also ref:`existing-repository-requirements`
   * - ``xml``
     - ``pycsw:XML``
     - 
     - 
     - 
     - 
     - 
     - Raw XML metadata as it was inserted into the repository.  Note that this field is deprecated for the ``metadata`` field, and will be removed in a future release, see also ref:`existing-repository-requirements`
   * - ``metadata``
     - ``pycsw:Metadata``
     - 
     - 
     - 
     - 
     - 
     - Raw metadata payload (replaces ``xml`` field, supports any metadata type [JSON, XML, etc.]), see also ref:`existing-repository-requirements`
   * - ``metadata_type``
     - pycsw:MetadataType
     - 
     - 
     - 
     - 
     - 
     - Media type of the metadata payload (``application/xml`` [default], ``application/json`` for OGC API - Records and STAC)
   * - ``anytext``
     - ``pycsw:AnyText``
     - ``apiso:AnyText``
     - ``//text()`` (``csw:AnyText`` [queryable only, not a returnable])
     - ``//text()`` (``csw:AnyText`` [queryable only, not a returnable])
     - ``q=`` (for API)
     - ``q=`` (for API)
     - Bag of metadata element and attributes content ONLY, no XML tags or JSON element names, see also :ref:`existing-repository-requirements`
   * - ``language``
     - ``pycsw:Language``
     - ``apiso:Language``
     - ``gmd:language/gmd:LanguageCode``, ``gmd:language/gco:CharacterString``
     - ``dc:language``
     - ``properties.language``
     - ``properties.language``
     - 
   * - ``title``
     - ``pycsw:Title``
     - ``apiso:Title``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString``
     - ``dc:title``
     - ``properties.title``
     - ``properties.title``
     - 
   * - ``abstract``
     - ``pycsw:Abstract``
     - ``apiso:Abstract``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString``
     - ``dct:abstract``
     - ``properties.description``
     - ``properties.description``
     - 
   * - ``edition``
     - ``pycsw:Edition``
     - ``apiso:Edition``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:edition/gco:CharacterString``
     - 
     - 
     - 
     - 
   * - ``keywords``
     - ``pycsw:Keywords``
     - ``apiso:Subject``
     - ``gmd:identificationInfo/gmd:MD_Identification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString``, ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode``
     - ``dc:subject``
     - ``properties.keywords``
     - 
     - CSV of keywords, see also :ref:`existing-repository-requirements`
   * - ``keywordstype``
     - ``pycsw:KeywordType``
     - ``apiso:KeywordType``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode``
     - 
     - 
     - 
     - 
   * - ``themes``
     - ``pycsw:Themes``
     - 
     - 
     - 
     - ``properties.themes``
     - 
     - JSON list of concepts/schemes, see also :ref:`existing-repository-requirements`
   * - ``format``
     - ``pycsw:Format``
     - ``apiso:Format``
     - ``gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name/gco:CharacterString``
     - ``dc:format``
     - ``properties.formats``
     - 
     - 
   * - ``source``
     - ``pycsw:Source``
     - 
     - 
     - ``dc:source``
     - ``properties.externalIds``
     - 
     - 
   * - ``date``
     - ``pycsw:Date``
     - 
     - 
     - ``dc:date``
     - ``time``
     - ``properties.datetime``
     - 
   * - ``date_modified``
     - ``pycsw:Modified``
     - ``apiso:Modified``
     - ``gmd:dateStamp/gco:Date``
     - ``dct:modified``
     - ``properties.updated``
     - ``properties.updated``
     - 
   * - ``type``
     - ``pycsw:Type``
     - ``apiso:Type``
     - ``gmd:hierarchyLevel/gmd:MD_ScopeCode``
     - ``dc:type``
     - ``properties.type``
     - 
     - 
   * - ``wkt_geometry``
     - ``pycsw:BoundingBox``
     - ``apiso:BoundingBox``
     - ``apiso:BoundingBox``
     - ``ows:BoundingBox``
     - ``geometry``
     - ``geometry``
     - WKT/EWKT of geometry
   * - ``crs``
     - ``pycsw:CRS``
     - ``apiso:CRS``
     - ``gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:codeSpace/gco:CharacterString``, ``gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:version/gco:CharacterString``, ``gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gco:CharacterString``
     - ``dct:spatial``
     - 
     - 
     - 
   * - ``title_alternate``
     - ``pycsw:AlternateTitle``
     - ``apiso:AlternateTitle``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:alternateTitle/gco:CharacterString``
     - ``dct:alternative``
     - 
     - 
     - 
   * - ``date_revision``
     - ``pycsw:RevisionDate``
     - ``apiso:RevisionDate``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="revision"]/gmd:date/gco:Date``
     - 
     - ``properties.updated``
     - ``properties.updated``
     - 
   * - ``date_creation``
     - ``pycsw:CreationDate``
     - ``apiso:CreationDate``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="creation"]/gmd:date/gco:Date``
     - 
     - ``properties.created``
     - ``properties.created``
     - 
   * - ``date_publication``
     - ``pycsw:PublicationDate``
     - ``apiso:PublicationDate``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="publication"]/gmd:date/gco:Date``
     - 
     - 
     - 
     - 
   * - ``organization``
     - ``pycsw:OrganizationName``
     - ``apiso:OrganisationName``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString``
     - 
     - 
     - 
     - 
   * - ``securityconstraints``
     - ``pycsw:SecurityConstraints``
     - ``apiso:HasSecurityConstraints``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_SecurityConstraints``
     - 
     - 
     - 
     - 
   * - ``parentidentifier``
     - ``pycsw:ParentIdentifier``
     - ``apiso:ParentIdentifier``
     - ``gmd:parentIdentifier/gco:CharacterString``
     - 
     - ``collection``
     - ``collection``
     - 
   * - ``topicategory``
     - ``pycsw:TopicCategory``
     - ``apiso:TopicCategory``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode``
     - 
     - 
     - 
     - 
   * - ``resourcelanguage``
     - ``pycsw:ResourceLanguage``
     - ``apiso:ResourceLanguage``
     - ``md:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:code/gmd:MD_LanguageTypeCode``
     - 
     - 
     - 
     - 
   * - ``geodescode``
     - ``pycsw:GeographicDescriptionCode``
     - ``apiso:GeographicDescriptionCode``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicDescription/gmd:geographicIdentifier/gmd:MD_Identifier/gmd:code/gco:CharacterString``
     - 
     - 
     - 
     - 
   * - ``denominator``
     - ``pycsw:Denominator``
     - ``apiso:Denominator``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:equivalentScale/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer``
     - 
     - 
     - 
     - 
   * - ``distancevalue``
     - ``pycsw:DistanceValue``
     - ``apiso:DistanceValue``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/gco:Distance``
     - 
     - 
     - 
     - 
   * - ``distanceuom``
     - ``pycsw:DistanceUOM``
     - ``apiso:DistanceUOM``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/gco:Distance/@uom``
     - 
     - 
     - 
     - 
   * - ``time_begin``
     - ``pycsw:TempExtent_begin``
     - ``apiso:TempExtent_begin``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition``
     - 
     - ``properties.extent.temporal.interval[0]``
     - ``properties.start_datetime``
     - 
   * - ``time_end``
     - ``pycsw:TempExtent_end``
     - ``apiso:TempExtent_end``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:endPosition``
     - 
     - ``properties.extent.temporal.interval[1]``
     - ``properties.end_datetime``
     - 
   * - ``servicetype``
     - ``pycsw:ServiceType``
     - ``apiso:ServiceType``
     - ``gmd:identificationInfo/srv:SV_ServiceIdentification/srv:serviceType/gco:LocalName``
     - 
     - 
     - 
     - 
   * - ``servicetypeversion``
     - ``pycsw:ServiceTypeVersion``
     - ``apiso:ServiceTypeVersion``
     - ``gmd:identificationInfo/srv:SV_ServiceIdentification/srv:serviceTypeVersion/gco:CharacterString``
     - 
     - 
     - 
     - 
   * - ``operation``
     - ``pycsw:Operation``
     - ``apiso:Operation``
     - ``gmd:identificationInfo/srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:operationName/gco:CharacterString``
     - 
     - 
     - 
     - 
   * - ``couplingtype``
     - ``pycsw:CouplingType``
     - ``apiso:CouplingType``
     - ``gmd:identificationInfo/srv:SV_ServiceIdentification/srv:couplingType/srv:SV_CouplingType``
     - 
     - 
     - 
     - 
   * - ``operateson``
     - ``pycsw:OperatesOn``
     - ``apiso:OperatesOn``
     - ``gmd:identificationInfo/srv:SV_ServiceIdentification/srv:operatesOn/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:RS_Identifier/gmd:code/gco:CharacterString``
     - 
     - 
     - 
     - 
   * - ``operatesonidentifier``
     - ``pycsw:OperatesOnIdentifier``
     - ``apiso:OperatesOnIdentifier``
     - ``gmd:identificationInfo/srv:SV_ServiceIdentification/srv:coupledResource/srv:SV_CoupledResource/srv:identifier/gco:CharacterString``
     - 
     - 
     - 
     - 
   * - ``operatesoname``
     - ``pycsw:OperatesOnName``
     - ``apiso:OperatesOnName``
     - ``gmd:identificationInfo/srv:SV_ServiceIdentification/srv:coupledResource/srv:SV_CoupledResource/srv:operationName/gco:CharacterString``
     - 
     - 
     - 
     - 
   * - ``degree``
     - ``pycsw:Degree``
     - ``apiso:Degree``
     - ``gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:pass/gco:Boolean``
     - 
     - 
     - 
     - 
   * - ``accessconstraints``
     - ``pycsw:AccessConstraints``
     - ``apiso:AccessConstraints``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_RestrictionCode``
     - ``dc:rights``
     - 
     - 
     - 
   * - ``otherconstraints``
     - ``pycsw:OtherConstraints``
     - ``apiso:OtherConstraints``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints/gco:CharacterString``
     - 
     - ``properties.license``
     - 
     - 
   * - ``classification``
     - ``pycsw:Classification``
     - ``apiso:Classification``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_ClassificationCode``
     - 
     - 
     - 
     - 
   * - ``conditionapplyingtoaccessanduse``
     - ``pycsw:ConditionApplyingToAccessAndUse``
     - ``apiso:ConditionApplyingToAccessAndUse``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:useLimitation/gco:CharacterString``
     - 
     - 
     - 
     - 
   * - ``lineage``
     - ``pycsw:Lineage``
     - ``apiso:Lineage``
     - ``gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement/gco:CharacterString``
     - 
     - 
     - 
     - 
   * - ``responsiblepartyrole``
     - ``pycsw:ResponsiblePartyRole``
     - ``apiso:ResponsiblePartyRole``
     - ``gmd:contact/gmd:CI_ResponsibleParty/gmd:role/gmd:CI_RoleCode``
     - 
     - 
     - 
     - 
   * - ``specificationtitle``
     - ``pycsw:SpecificationTitle``
     - ``apiso:SpecificationTitle``
     - ``gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification/gmd:CI_Citation/gmd:title/gco:CharacterString``
     - 
     - 
     - 
     - 
   * - ``specificationdate``
     - ``pycsw:SpecificationDate``
     - ``apiso:SpecificationDate``
     - ``gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date``
     - 
     - 
     - 
     - 
   * - ``specificationdatetype``
     - ``pycsw:SpecificationDateType``
     - ``apiso:SpecificationDateType``
     - ``gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode``
     - 
     - 
     - 
     - 
   * - ``creator``
     - ``pycsw:Creator``
     - ``apiso:Creator``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName[gmd:role/gmd:CI_RoleCode/@codeListValue="originator"]/gco:CharacterString``
     - ``dc:creator``
     - ``properties.providers``
     - 
     - 
   * - ``publisher``
     - ``pycsw:Publisher``
     - ``apiso:Publisher``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName[gmd:role/gmd:CI_RoleCode/@codeListValue="publisher"]/gco:CharacterString``
     - ``dc:publisher``
     - ``properties.providers``
     - 
     - 
   * - ``contributor``
     - ``pycsw:Contributor``
     - ``apiso:Contributor``
     - ``gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName[gmd:role/gmd:CI_RoleCode/@codeListValue="contributor"]/gco:CharacterString``
     - ``dc:contributor``
     - ``properties.providers``
     - 
     - 
   * - ``relation``
     - ``pycsw:Relation``
     - ``apiso:Relation``
     - ``gmd:identificationInfo/gmd:MD_Data_Identification/gmd:aggregationInfo``
     - ``dc:relation``
     - 
     - 
     - 
   * - ``platform``
     - ``pycsw:Platform``
     - ``apiso:Platform``
     - ``gmi:acquisitionInfo/gmi:MI_AcquisitionInformation/gmi:platform/gmi:MI_Platform/gmi:identifier``
     - 
     - 
     - 
     - 
   * - ``instrument``
     - ``pycsw:Instrument``
     - ``apiso:Instrument``
     - ``gmi:acquisitionInfo/gmi:MI_AcquisitionInformation/gmi:platform/gmi:MI_Platform/gmi:instrument/gmi:MI_Instrument/gmi:identifier``
     - 
     - 
     - 
     - 
   * - ``sensortype``
     - ``pycsw:SensorType``
     - ``apiso:SensorType``
     - ``gmi:acquisitionInfo/gmi:MI_AcquisitionInformation/gmi:platform/gmi:MI_Platform/gmi:instrument/gmi:MI_Instrument/gmi:type``
     - 
     - 
     - 
     - 
   * - ``cloudcover``
     - ``pycsw:CloudCover``
     - ``apiso:CloudCover``
     - ``gmd:contentInfo/gmd:MD_ImageDescription/gmd:cloudCoverPercentage``
     - 
     - 
     - 
     - 
   * - ``bands``
     - ``pycsw:Bands``
     - ``apiso:Bands``
     - ``gmd:contentInfo/gmd:MD_ImageDescription/gmd:dimension/MD_Band/@id``
     - 
     - 
     - 
     - JSON list of band information, see also :ref:`existing-repository-requirements` 
   * - ``links``
     - ``pycsw:Links``
     - 
     - 
     - 
     - ``links``
     - ``links``, ``assets``
     - List of dicts with properties: ``name``, ``description``, ``protocol``, ``url``, see also :ref:`existing-repository-requirements`
   * - ``contacts``
     - ``pycsw:Contacts``
     - 
     - ``//gmd:CI_ResponsibleParty`` 
     - 
     - ``properties.providers``
     - 
     - List of dicts with properties: name, organization, address, postcode, city, region, country, email, phone, fax, onlineresource, position, role
