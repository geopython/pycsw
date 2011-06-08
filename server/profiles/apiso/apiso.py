# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#                Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2011 Tom Kralidis
# Copyright (c) 2011 Angelos Tzotsos
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import os
from lxml import etree
from server import profile, config, util

NAMESPACES = {
    'apiso': 'http://www.opengis.net/cat/csw/apiso/1.0',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'srv': 'http://www.isotc211.org/2005/srv'
}

INSPIRE_NAMESPACES = {
    'inspire_ds': 'http://inspire.ec.europa.eu/schemas/inspire_ds/1.0',
    'inspire_common': 'http://inspire.ec.europa.eu/schemas/common/1.0'
}

CODELIST = 'http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml'
CODESPACE = 'ISOTC211/19115'

REPOSITORY = {
    'gmd:MD_Metadata': {
        'outputschema': 'http://www.isotc211.org/2005/gmd',
        'queryables': {
            'SupportedISOQueryables': {
                'apiso:Subject': 'gmd:identificationInfo/gmd:MD_Identification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString|gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode',
                'apiso:Title': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString',
                'apiso:Abstract': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString',
                'apiso:Format': 'gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name/gco:CharacterString',
                'apiso:Identifier': 'gmd:fileIdentifier/gco:CharacterString',
                'apiso:Modified': 'gmd:dateStamp/gco:Date',
                'apiso:Type': 'gmd:hierarchyLevel/gmd:MD_ScopeCode',
                'apiso:BoundingBox': 'bbox',
                'apiso:CRS': 'concat("urn:ogc:def:crs:","gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:codeSpace/gco:CharacterString",":","gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:version/gco:CharacterString",":","gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gco:CharacterString")',
                'apiso:AlternateTitle': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:alternateTitle/gco:CharacterString',
                'apiso:RevisionDate': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="revision"]/gmd:date/gco:Date',
                'apiso:CreationDate': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="creation"]/gmd:date/gco:Date',
                'apiso:PublicationDate': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="publication"]/gmd:date/gco:Date',
                'apiso:OrganisationName': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString',
                'apiso:HasSecurityConstraints': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_SecurityConstraints',
                'apiso:Language': 'gmd:language/gmd:LanguageCode|gmd:language/gco:CharacterString',
                'apiso:ParentIdentifier': 'gmd:parentIdentifier/gco:CharacterString',
                'apiso:KeywordType': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode',
                'apiso:TopicCategory': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode',
                'apiso:ResourceLanguage': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:code/gmd:MD_LanguageTypeCode',
                'apiso:GeographicDescriptionCode': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicDescription/gmd:geographicIdentifier/gmd:MD_Identifier/gmd:code/gco:CharacterString',
                'apiso:Denominator': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:equivalentScale/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer',
                'apiso:DistanceValue': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/gco:Distance',
                'apiso:DistanceUOM': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/gco:Distance/@uom',
                'apiso:TempExtent_begin': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition',
                'apiso:TempExtent_end': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:endPosition',
                'apiso:AnyText': 'xml',
                'apiso:ServiceType': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:serviceType/gco:LocalName',
                'apiso:ServiceTypeVersion': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:serviceTypeVersion/gco:CharacterString',
                'apiso:Operation': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:operationName/gco:CharacterString',
                'apiso:CouplingType': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:couplingType/srv:SV_CouplingType',
                'apiso:OperatesOn': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:operatesOn/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:RS_Identifier/gmd:code/gco:CharacterString',
                'apiso:OperatesOnIdentifier': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:coupledResource/srv:SV_CoupledResource/srv:identifier/gco:CharacterString',
                'apiso:OperatesOnName': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:coupledResource/srv:SV_CoupledResource/srv:operationName/gco:CharacterString'
            },
            'AdditionalQueryables': {
                'apiso:Degree': 'gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:pass/gco:Boolean',
                'apiso:AccessConstraints': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_RestrictionCode',
                'apiso:OtherConstraints': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints/gco:CharacterString',
                'apiso:Classification': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_ClassificationCode',
                'apiso:ConditionApplyingToAccessAndUse': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:useLimitation/gco:CharacterString',
                'apiso:Lineage': 'gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement/gco:CharacterString',
                'apiso:ResponsiblePartyRole': 'gmd:contact/gmd:CI_ResponsibleParty/gmd:role/gmd:CI_RoleCode',
                'apiso:SpecificationTitle': 'gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification/gmd:CI_Citation/gmd:title/gco:CharacterString',
                'apiso:SpecificationDate': 'gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date',
                'apiso:SpecificationDateType': 'gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode',
                'apiso:Creator': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName[gmd:role/gmd:CI_RoleCode/@codeListValue="originator"]/gco:CharacterString',
                'apiso:Publisher': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName[gmd:role/gmd:CI_RoleCode/@codeListValue="publisher"]/gco:CharacterString',
                'apiso:Contributor': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName[gmd:role/gmd:CI_RoleCode/@codeListValue="contributor"]/gco:CharacterString',
                'apiso:Relation': 'gmd:identificationInfo/gmd:MD_Data_Identification/gmd:aggregationInfo'
            }
        },
        'mappings': {
            'csw:Record': {
                # map APISO queryables to DC queryables
                'apiso:Title': 'dc:title',
                'apiso:Creator': 'dc:creator',
                'apiso:Subject': 'dc:subject',
                'apiso:Abstract': 'dct:abstract',
                'apiso:Publisher': 'dc:publisher',
                'apiso:Contributor': 'dc:contributor',
                'apiso:Modified': 'dct:modified',
                #'apiso:Date': 'dc:date',
                'apiso:Type': 'dc:type',
                'apiso:Format': 'dc:format',
                'apiso:Language': 'dc:language',
                'apiso:Relation': 'dc:relation',
                'apiso:AccessConstraints': 'dc:rights',
            }
        }
    }
}

class APISO(profile.Profile):
    ''' APISO class '''
    def __init__(self, model, namespaces):
        profile.Profile.__init__(self,
            name='apiso',
            version='1.0.0',
            title='ISO Metadata Application Profile',
            url='http://portal.opengeospatial.org/files/?artifact_id=21460',
            namespace=NAMESPACES['gmd'],
            typename='gmd:MD_Metadata',
            outputschema=NAMESPACES['gmd'],
            prefixes=['apiso', 'gmd'],
            model=model,
            core_namespaces=namespaces,
            added_namespaces=NAMESPACES,
            repository=REPOSITORY['gmd:MD_Metadata'])

    def extend_core(self, model, namespaces, config):
        ''' Extend core configuration '''

        # update INSPIRE vars
        namespaces.update(INSPIRE_NAMESPACES)

        # set INSPIRE config
        if config.has_key('metadata:inspire') and config['metadata:inspire'].has_key('enabled') and config['metadata:inspire']['enabled'] == 'true':
            self.inspire_config = config['metadata:inspire']
            self.url = config['server']['url']
            self.current_language = self.inspire_config['default_language']
        else:
            self.inspire_config = None

        self.ogc_schemas_base = config['server']['ogc_schemas_base']

    def check_parameters(self, kvp):
        '''Check for Language parameter in GetCapabilities request'''

        if self.inspire_config is not None:
            result = None
            if kvp.has_key('language') == False:
                self.current_language = self.inspire_config['default_language']
            else:
                if kvp['language'] not in self.inspire_config['languages_supported'].split(','):
                    text = 'Requested Language not supported, Supported languages: %s' % self.inspire_config['languages_supported']
                    return {'error': 'true', 'locator': 'language', 'code': 'InvalidParameterValue', 'text': text}
                else:
                    self.current_language=kvp['language']
                    return None
            return None
        return None

    def get_extendedcapabilities(self):
        ''' Add child to ows:OperationsMetadata Element '''

        if self.inspire_config is not None:

            ex_caps = etree.Element(
                util.nspath_eval('inspire_ds:ExtendedCapabilities'))

            ex_caps.attrib[util.nspath_eval('xsi:schemaLocation')] = \
            '%s %s/inspire_ds.xsd' % \
            (INSPIRE_NAMESPACES['inspire_ds'], INSPIRE_NAMESPACES['inspire_ds'])

            # Resource Locator
            res_loc = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:ResourceLocator'))

            etree.SubElement(res_loc,
            util.nspath_eval('inspire_common:URL')).text = '%s?service=CSW&version=2.0.2&request=GetCapabilities' % self.url

            etree.SubElement(res_loc,
            util.nspath_eval('inspire_common:MediaType')).text = 'application/xml'

            # Resource Type
            etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:ResourceType')).text = 'service'

            # Temporal Reference
            temp_ref = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:TemporalReference'))

            temp_extent = etree.SubElement(temp_ref,
            util.nspath_eval('inspire_common:TemporalExtent'))

            val = self.inspire_config['temp_extent'].split('/')

            if len(val) == 1:
                etree.SubElement(temp_extent,
                util.nspath_eval('inspire_common:IndividualDate')).text = val[0]

            else:
                interval_dates = etree.SubElement(temp_extent,
                util.nspath_eval('inspire_common:IntervalOfDates'))

                etree.SubElement(interval_dates,
                util.nspath_eval('inspire_common:StartingDate')).text = val[0]

                etree.SubElement(interval_dates,
                util.nspath_eval('inspire_common:EndDate')).text = val[1]

            # Conformity - service
            cfm = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:Conformity'))

            spec = etree.SubElement(cfm,
            util.nspath_eval('inspire_common:Specification'))

            spec.attrib[util.nspath_eval('xsi:type')] =  'inspire_common:citationInspireInteroperabilityRegulation_eng'

            etree.SubElement(spec,
            util.nspath_eval('inspire_common:Title')).text = 'COMMISSION REGULATION (EU) No 1089/2010 of 23 November 2010 implementing Directive 2007/2/EC of the European Parliament and of the Council as regards interoperability of spatial data sets and services'

            etree.SubElement(spec,
            util.nspath_eval('inspire_common:DateOfPublication')).text = '2010-12-08'

            etree.SubElement(spec,
            util.nspath_eval('inspire_common:URI')).text = 'OJ:L:2010:323:0011:0102:EN:PDF'

            spec_loc = etree.SubElement(spec,
            util.nspath_eval('inspire_common:ResourceLocator'))

            etree.SubElement(spec_loc,
            util.nspath_eval('inspire_common:URL')).text = 'http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=OJ:L:2010:323:0011:0102:EN:PDF'

            etree.SubElement(spec_loc,
            util.nspath_eval('inspire_common:MediaType')).text = 'application/pdf'

            spec = etree.SubElement(cfm,
            util.nspath_eval('inspire_common:Degree')).text = self.inspire_config['conformity_service']

            # Metadata Point of Contact
            poc = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:MetadataPointOfContact'))

            etree.SubElement(poc,
            util.nspath_eval('inspire_common:OrganisationName')).text = self.inspire_config['contact_name']

            etree.SubElement(poc,
            util.nspath_eval('inspire_common:EmailAddress')).text = self.inspire_config['contact_email']

            # Metadata Date
            etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:MetadataDate')).text = self.inspire_config['date']

            # Spatial Data Service Type
            etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:SpatialDataServiceType')).text = 'discovery'

            # Mandatory Keyword
            mkey = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:MandatoryKeyword'))

            mkey.attrib[util.nspath_eval('xsi:type')] = 'inspire_common:classificationOfSpatialDataService'

            etree.SubElement(mkey,
            util.nspath_eval('inspire_common:KeywordValue')).text = 'infoCatalogueService'

            # Gemet Keywords

            for gkw in self.inspire_config['gemet_keywords'].split(','):
                gkey = etree.SubElement(ex_caps,
                util.nspath_eval('inspire_common:Keyword'))

                gkey.attrib[util.nspath_eval('xsi:type')] = 'inspire_common:inspireTheme_eng'

                ocv = etree.SubElement(gkey,
                util.nspath_eval('inspire_common:OriginatingControlledVocabulary'))

                etree.SubElement(ocv,
                util.nspath_eval('inspire_common:Title')).text = 'GEMET - INSPIRE themes'

                etree.SubElement(ocv,
                util.nspath_eval('inspire_common:DateOfPublication')).text = '2008-06-01'

                etree.SubElement(gkey,
                util.nspath_eval('inspire_common:KeywordValue')).text = gkw

            # Languages
            slang = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:SupportedLanguages'))

            dlang = etree.SubElement(slang,
            util.nspath_eval('inspire_common:DefaultLanguage'))

            etree.SubElement(dlang,
            util.nspath_eval('inspire_common:Language')).text = self.inspire_config['default_language']

            for l in self.inspire_config['languages_supported'].split(','):
                lang = etree.SubElement(slang,
                util.nspath_eval('inspire_common:SupportedLanguage'))

                etree.SubElement(lang,
                util.nspath_eval('inspire_common:Language')).text = l

            clang = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:ResponseLanguage'))
            etree.SubElement(clang,
            util.nspath_eval('inspire_common:Language')).text = self.current_language

            return ex_caps

    def get_schemacomponents(self):
        ''' Return schema components as lxml.etree.Element list '''

        node1 = etree.Element(
        util.nspath_eval('csw:SchemaComponent'),
        schemaLanguage = 'XMLSCHEMA', targetNamespace = self.namespace,
        parentSchema = 'gmd.xsd')

        schema = etree.parse(os.path.join(
                'server', 'profiles', 'apiso',
                'etc', 'schemas', 'ogc', 'iso', '19139',
                '20060504', 'gmd', 'identification.xsd')).getroot()

        node1.append(schema)

        node2 = etree.Element(
        util.nspath_eval('csw:SchemaComponent'),
        schemaLanguage = 'XMLSCHEMA', targetNamespace = self.namespace,
        parentSchema = 'gmd.xsd')

        schema = etree.parse(os.path.join(
                'server', 'profiles', 'apiso',
                'etc', 'schemas', 'ogc', 'iso', '19139',
                '20060504', 'srv', 'serviceMetadata.xsd')).getroot()

        node2.append(schema)

        return [node1, node2]

    def check_getdomain(self, kvp):
        '''Perform extra profile specific checks in the GetDomain request'''
        return None

    def write_record(self, result, esn, outputschema, queryables):
        ''' Return csw:SearchResults child as lxml.etree.Element '''
        xml = etree.fromstring(result.xml)
        if outputschema == self.namespace:
            if esn == 'full':  # dump the full record
                node = xml
            else:  # it's a brief or summary record

                if result.typename == 'csw:Record':  # transform csw:Record -> gmd:MD_Metadata model mappings
                    dc2iso(queryables)

                node = etree.Element(util.nspath_eval('gmd:MD_Metadata'))
                node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
                '%s %s/csw/2.0.2/profiles/apiso/1.0.0/apiso.xsd' % (self.namespace, self.ogc_schemas_base)

                # identifier
                val = result.identifier

                identifier = etree.SubElement(node, util.nspath_eval('gmd:fileIdentifier'))
                etree.SubElement(identifier, util.nspath_eval('gco:ChracterString')).text = val

                if esn == 'summary':
                    # language
                    val = util.query_xpath(xml, queryables['apiso:Language'])

                    lang = etree.SubElement(node, util.nspath_eval('gmd:language'))
                    etree.SubElement(lang, util.nspath_eval('gco:ChracterString')).text = val

                # hierarchyLevel
                val = util.query_xpath(xml, queryables['apiso:Type'])

                if val is not None: 
                    hierarchy = etree.SubElement(node, util.nspath_eval('gmd:hierarchyLevel'),
                    codeList = '%s#MD_ScopeCode' % CODELIST,
                    codeListValue = val,
                    codeSpace = CODESPACE).text = val

                if esn == 'summary':
                    # contact
                    val = util.query_xpath(xml, queryables['apiso:OrganisationName'])
                    contact = etree.SubElement(node, util.nspath_eval('gmd:contact'))
                    CI_resp = etree.SubElement(contact, util.nspath_eval('gmd:CI_ResponsibleParty'))
                    org_name = etree.SubElement(CI_resp, util.nspath_eval('gmd:organisationName'))
                    etree.SubElement(org_name, util.nspath_eval('gco:ChracterString')).text = val
    
                    # date
                    val = util.query_xpath(xml, queryables['apiso:Modified'])
                    date = etree.SubElement(node, util.nspath_eval('gmd:dateStamp'))
                    etree.SubElement(date, util.nspath_eval('gco:Date')).text = val
    
                    # metadata standard name
                    standard = etree.SubElement(node, util.nspath_eval('gmd:metadataStandardName'))
                    etree.SubElement(standard, util.nspath_eval('gco:ChracterString')).text = 'ISO19115'
    
                    # metadata standard version
                    standardver = etree.SubElement(node, util.nspath_eval('gmd:metadataStandardName'))
                    etree.SubElement(standardver, util.nspath_eval('gco:ChracterString')).text = '2003/Cor.1:2006'

                # title
                val = util.query_xpath(xml, queryables['apiso:Title'])
                if not val:
                    val = ''
                identification = etree.SubElement(node, util.nspath_eval('gmd:identificationInfo'))
                tmp = etree.SubElement(identification, util.nspath_eval('gmd:MD_IdentificationInfo'))
                tmp2 = etree.SubElement(tmp, util.nspath_eval('gmd:citation'))
                tmp3 = etree.SubElement(tmp2, util.nspath_eval('gmd:CI_Citation'))
                tmp4 = etree.SubElement(tmp3, util.nspath_eval('gmd:title'))
                etree.SubElement(tmp4, util.nspath_eval('gco:CharacterString')).text = val.decode('utf8')

                if esn == 'summary':
                    # abstract
                    val = util.query_xpath(xml, queryables['apiso:Abstract'])
                    if not val:
                        val = ''
                    tmp = etree.SubElement(identification, util.nspath_eval('gmd:abstract'))
                    etree.SubElement(tmp, util.nspath_eval('gco:ChracterString')).text = val.decode('utf8')
    
                    # spatial resolution
                    val = util.query_xpath(xml, queryables['apiso:Denominator'])
                    tmp = etree.SubElement(identification, util.nspath_eval('gmd:spatialResolution'))
                    tmp2 = etree.SubElement(tmp, util.nspath_eval('gmd:spatialResolution'))
                    tmp3 = etree.SubElement(tmp2, util.nspath_eval('gmd:MD_Resolution'))
                    tmp4 = etree.SubElement(tmp3, util.nspath_eval('gmd:equivalentScale'))
                    tmp5 = etree.SubElement(tmp4, util.nspath_eval('gmd:MD_RepresentativeFraction'))
                    tmp6 = etree.SubElement(tmp5, util.nspath_eval('gmd:denominator'))
                    etree.SubElement(tmp6, util.nspath_eval('gco:ChracterString')).text = val
    
                    # resource language
                    val = util.query_xpath(xml, queryables['apiso:ResourceLanguage'])
                    tmp = etree.SubElement(identification, util.nspath_eval('gmd:language'))
                    etree.SubElement(tmp, util.nspath_eval('gco:CharacterString')).text = val
    
                    # topic category
                    val = util.query_xpath(xml, queryables['apiso:TopicCategory'])
                    if val:
                        for v in val.split(','):
                            tmp = etree.SubElement(identification, util.nspath_eval('gmd:topicCategory'))
                            etree.SubElement(tmp, util.nspath_eval('gmd:MD_TopicCategoryCode')).text = val

                # bbox extent
                val = result.bbox
                bboxel = write_extent(val)
                if bboxel is not None:
                    identification.append(bboxel)

                # service identification

                # service type
                # service type version
                val = util.query_xpath(xml, queryables['apiso:ServiceType'])
                val2 = util.query_xpath(xml, queryables['apiso:ServiceTypeVersion'])
                if (val is not None):
                    srv_identification = etree.SubElement(identification, util.nspath_eval('srv:SV_ServiceIdentification'))
                    tmp = etree.SubElement(srv_identification, util.nspath_eval('srv:serviceType'))
                    etree.SubElement(tmp, util.nspath_eval('gco:LocalName')).text = val
                    tmp = etree.SubElement(srv_identification, util.nspath_eval('srv:serviceTypeVersion'))
                    etree.SubElement(tmp, util.nspath_eval('gco:CharacterString')).text = val2

                if esn == 'summary':
                    # service operations
                    val = util.query_xpath(xml, queryables['apiso:Operation'])
                    if val:
                        temp_oper=val.split(',')
                        oper = etree.SubElement(srv_identification, util.nspath_eval('srv:containsOperations'))
                        for i in temp_oper:
                            tmp = etree.SubElement(oper, util.nspath_eval('srv:SV_OperationMetadata'))
                            tmp2 = etree.SubElement(tmp, util.nspath_eval('srv:operationName'))
                            etree.SubElement(tmp2, util.nspath_eval('gco:CharacterString')).text = i
        return node

    def transform2dcmappings(self, queryables):
        ''' Transform ISO mappings into csw:Record mappings '''

        for qbl in queryables:
            if qbl in REPOSITORY['gmd:MD_Metadata']['mappings']['csw:Record'].values():
                tmp = [k for k, v in REPOSITORY['gmd:MD_Metadata']['mappings']['csw:Record'].iteritems() if v == qbl][0]
                val = queryables[tmp]
                queryables[qbl] = val

def write_extent(bbox):
    ''' Generate BBOX extent '''

    from shapely.wkt import loads

    if bbox is not None:
        extent = etree.Element(util.nspath_eval('gmd:extent'))
        ex_extent = etree.SubElement(extent, util.nspath_eval('gmd:EX_Extent'))
        ge = etree.SubElement(ex_extent, util.nspath_eval('gmd:geographicElement'))
        gbb = etree.SubElement(ge, util.nspath_eval('gmd:EX_GeographicBoundingBox'))
        west = etree.SubElement(gbb, util.nspath_eval('gmd:westBoundLongitude'))
        east = etree.SubElement(gbb, util.nspath_eval('gmd:eastBoundLongitude'))
        north = etree.SubElement(gbb, util.nspath_eval('gmd:northBoundLatitude'))
        south = etree.SubElement(gbb, util.nspath_eval('gmd:southBoundLatitude'))

        bbox2 = loads(bbox).exterior.bounds

        etree.SubElement(west, util.nspath_eval('gco:Decimal')).text = str(bbox2[0])
        etree.SubElement(south, util.nspath_eval('gco:Decimal')).text = str(bbox2[1])
        etree.SubElement(east, util.nspath_eval('gco:Decimal')).text = str(bbox2[2])
        etree.SubElement(north, util.nspath_eval('gco:Decimal')).text = str(bbox2[3])
        return extent
    return None

def dc2iso(queryables):
    ''' Transform csw:Record mappings into APISO mappings '''
    for qbl in queryables.keys():
        if qbl in REPOSITORY['gmd:MD_Metadata']['mappings']['csw:Record'].keys():  # map to new XPath
            queryables[qbl] = REPOSITORY['gmd:MD_Metadata']['mappings']['csw:Record'][qbl]
