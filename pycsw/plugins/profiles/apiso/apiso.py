# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
# Copyright (c) 2015 Angelos Tzotsos
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
from pycsw.core import config, util
from pycsw.core.etree import etree
from pycsw.plugins.profiles import profile

CODELIST = 'http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml'
CODESPACE = 'ISOTC211/19115'

class APISO(profile.Profile):
    ''' APISO class '''
    def __init__(self, model, namespaces, context):
        self.context = context

        self.namespaces = {
            'apiso': 'http://www.opengis.net/cat/csw/apiso/1.0',
            'gco': 'http://www.isotc211.org/2005/gco',
            'gmd': 'http://www.isotc211.org/2005/gmd',
            'srv': 'http://www.isotc211.org/2005/srv',
            'xlink': 'http://www.w3.org/1999/xlink'
        }

        self.inspire_namespaces = {
            'inspire_ds': 'http://inspire.ec.europa.eu/schemas/inspire_ds/1.0',
            'inspire_common': 'http://inspire.ec.europa.eu/schemas/common/1.0'
        }


        self.repository = {
            'gmd:MD_Metadata': {
                'outputschema': 'http://www.isotc211.org/2005/gmd',
                'queryables': {
                    'SupportedISOQueryables': {
                        'apiso:Subject': {'xpath': 'gmd:identificationInfo/gmd:MD_Identification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString|gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode', 'dbcol': self.context.md_core_model['mappings']['pycsw:Keywords']},
                        'apiso:Title': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:Title']},
                        'apiso:Abstract': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:Abstract']},
                        'apiso:Format': {'xpath': 'gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:Format']},
                        'apiso:Identifier': {'xpath': 'gmd:fileIdentifier/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:Identifier']},
                        'apiso:Modified': {'xpath': 'gmd:dateStamp/gco:Date', 'dbcol': self.context.md_core_model['mappings']['pycsw:Modified']},
                        'apiso:Type': {'xpath': 'gmd:hierarchyLevel/gmd:MD_ScopeCode', 'dbcol': self.context.md_core_model['mappings']['pycsw:Type']},
                        'apiso:BoundingBox': {'xpath': 'apiso:BoundingBox', 'dbcol': self.context.md_core_model['mappings']['pycsw:BoundingBox']},
                        'apiso:CRS': {'xpath': 'concat("urn:ogc:def:crs:","gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:codeSpace/gco:CharacterString",":","gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:version/gco:CharacterString",":","gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gco:CharacterString")', 'dbcol': self.context.md_core_model['mappings']['pycsw:CRS']},
                        'apiso:AlternateTitle': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:alternateTitle/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:AlternateTitle']},
                        'apiso:RevisionDate': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="revision"]/gmd:date/gco:Date', 'dbcol': self.context.md_core_model['mappings']['pycsw:RevisionDate']},
                        'apiso:CreationDate': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="creation"]/gmd:date/gco:Date', 'dbcol': self.context.md_core_model['mappings']['pycsw:CreationDate']},
                        'apiso:PublicationDate': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="publication"]/gmd:date/gco:Date', 'dbcol': self.context.md_core_model['mappings']['pycsw:PublicationDate']},
                        'apiso:OrganisationName': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:OrganizationName']},
                        'apiso:HasSecurityConstraints': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_SecurityConstraints', 'dbcol': self.context.md_core_model['mappings']['pycsw:SecurityConstraints']},
                        'apiso:Language': {'xpath': 'gmd:language/gmd:LanguageCode|gmd:language/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:Language']},
                        'apiso:ParentIdentifier': {'xpath': 'gmd:parentIdentifier/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:ParentIdentifier']},
                        'apiso:KeywordType': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode', 'dbcol': self.context.md_core_model['mappings']['pycsw:KeywordType']},
                        'apiso:TopicCategory': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode', 'dbcol': self.context.md_core_model['mappings']['pycsw:TopicCategory']},
                        'apiso:ResourceLanguage': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:code/gmd:MD_LanguageTypeCode', 'dbcol': self.context.md_core_model['mappings']['pycsw:ResourceLanguage']},
                        'apiso:GeographicDescriptionCode': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicDescription/gmd:geographicIdentifier/gmd:MD_Identifier/gmd:code/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:GeographicDescriptionCode']},
                        'apiso:Denominator': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:equivalentScale/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer', 'dbcol': self.context.md_core_model['mappings']['pycsw:Denominator']},
                        'apiso:DistanceValue': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/gco:Distance', 'dbcol': self.context.md_core_model['mappings']['pycsw:DistanceValue']},
                        'apiso:DistanceUOM': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/gco:Distance/@uom', 'dbcol': self.context.md_core_model['mappings']['pycsw:DistanceUOM']},
                        'apiso:TempExtent_begin': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition', 'dbcol': self.context.md_core_model['mappings']['pycsw:TempExtent_begin']},
                        'apiso:TempExtent_end': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:endPosition', 'dbcol': self.context.md_core_model['mappings']['pycsw:TempExtent_end']},
                        'apiso:AnyText': {'xpath': '//', 'dbcol': self.context.md_core_model['mappings']['pycsw:AnyText']},
                        'apiso:ServiceType': {'xpath': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:serviceType/gco:LocalName', 'dbcol': self.context.md_core_model['mappings']['pycsw:ServiceType']},
                        'apiso:ServiceTypeVersion': {'xpath': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:serviceTypeVersion/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:ServiceTypeVersion']},
                        'apiso:Operation': {'xpath': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:operationName/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:Operation']},
                        'apiso:CouplingType': {'xpath': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:couplingType/srv:SV_CouplingType', 'dbcol': self.context.md_core_model['mappings']['pycsw:CouplingType']},
                        'apiso:OperatesOn': {'xpath': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:operatesOn/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:RS_Identifier/gmd:code/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:OperatesOn']},
                        'apiso:OperatesOnIdentifier': {'xpath': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:coupledResource/srv:SV_CoupledResource/srv:identifier/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:OperatesOnIdentifier']},
                        'apiso:OperatesOnName': {'xpath': 'gmd:identificationInfo/srv:SV_ServiceIdentification/srv:coupledResource/srv:SV_CoupledResource/srv:operationName/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:OperatesOnName']},
                    },
                    'AdditionalQueryables': {
                        'apiso:Degree': {'xpath': 'gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:pass/gco:Boolean', 'dbcol': self.context.md_core_model['mappings']['pycsw:Degree']},
                        'apiso:AccessConstraints': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_RestrictionCode', 'dbcol': self.context.md_core_model['mappings']['pycsw:AccessConstraints']},
                        'apiso:OtherConstraints': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:OtherConstraints']},
                        'apiso:Classification': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_ClassificationCode', 'dbcol': self.context.md_core_model['mappings']['pycsw:Classification']},
                        'apiso:ConditionApplyingToAccessAndUse': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:useLimitation/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:ConditionApplyingToAccessAndUse']},
                        'apiso:Lineage': {'xpath': 'gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:Lineage']},
                        'apiso:ResponsiblePartyRole': {'xpath': 'gmd:contact/gmd:CI_ResponsibleParty/gmd:role/gmd:CI_RoleCode', 'dbcol': self.context.md_core_model['mappings']['pycsw:ResponsiblePartyRole']},
                        'apiso:SpecificationTitle': {'xpath': 'gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification/gmd:CI_Citation/gmd:title/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:SpecificationTitle']},
                        'apiso:SpecificationDate': {'xpath': 'gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date', 'dbcol': self.context.md_core_model['mappings']['pycsw:SpecificationDate']},
                        'apiso:SpecificationDateType': {'xpath': 'gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode', 'dbcol': self.context.md_core_model['mappings']['pycsw:SpecificationDateType']},
                        'apiso:Creator': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName[gmd:role/gmd:CI_RoleCode/@codeListValue="originator"]/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:Creator']},
                        'apiso:Publisher': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName[gmd:role/gmd:CI_RoleCode/@codeListValue="publisher"]/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:Publisher']},
                        'apiso:Contributor': {'xpath': 'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName[gmd:role/gmd:CI_RoleCode/@codeListValue="contributor"]/gco:CharacterString', 'dbcol': self.context.md_core_model['mappings']['pycsw:Contributor']},
                        'apiso:Relation': {'xpath': 'gmd:identificationInfo/gmd:MD_Data_Identification/gmd:aggregationInfo', 'dbcol': self.context.md_core_model['mappings']['pycsw:Relation']}
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

        profile.Profile.__init__(self,
            name='apiso',
            version='1.0.0',
            title='ISO Metadata Application Profile',
            url='http://portal.opengeospatial.org/files/?artifact_id=21460',
            namespace=self.namespaces['gmd'],
            typename='gmd:MD_Metadata',
            outputschema=self.namespaces['gmd'],
            prefixes=['apiso', 'gmd'],
            model=model,
            core_namespaces=namespaces,
            added_namespaces=self.namespaces,
            repository=self.repository['gmd:MD_Metadata'])

    def extend_core(self, model, namespaces, config):
        ''' Extend core configuration '''

        # update INSPIRE vars
        self.context.namespaces.update(self.inspire_namespaces)

        # update harvest resource types with WMS, since WMS is not a typename,
        if 'Harvest' in model['operations']:
            model['operations']['Harvest']['parameters']['ResourceType']['values'].append('http://www.isotc211.org/schemas/2005/gmd/')

        # set INSPIRE config
        if config.has_section('metadata:inspire') and config.has_option('metadata:inspire', 'enabled') and config.get('metadata:inspire', 'enabled') == 'true':
            self.inspire_config = {}
            self.inspire_config['languages_supported'] = config.get('metadata:inspire', 'languages_supported')
            self.inspire_config['default_language'] = config.get('metadata:inspire', 'default_language')
            self.inspire_config['date'] = config.get('metadata:inspire', 'date')
            self.inspire_config['gemet_keywords'] = config.get('metadata:inspire', 'gemet_keywords')
            self.inspire_config['conformity_service'] = config.get('metadata:inspire', 'conformity_service')
            self.inspire_config['contact_name'] = config.get('metadata:inspire', 'contact_name')
            self.inspire_config['contact_email'] = config.get('metadata:inspire', 'contact_email')
            self.inspire_config['temp_extent'] = config.get('metadata:inspire', 'temp_extent')
        else:
            self.inspire_config = None

        self.ogc_schemas_base = config.get('server', 'ogc_schemas_base')
        self.url = config.get('server', 'url')

    def check_parameters(self, kvp):
        '''Check for Language parameter in GetCapabilities request'''

        if self.inspire_config is not None:
            result = None
            if 'language' not in kvp:
                self.inspire_config['current_language'] = self.inspire_config['default_language']
            else:
                if kvp['language'] not in self.inspire_config['languages_supported'].split(','):
                    text = 'Requested Language not supported, Supported languages: %s' % self.inspire_config['languages_supported']
                    return {'error': 'true', 'locator': 'language', 'code': 'InvalidParameterValue', 'text': text}
                else:
                    self.inspire_config['current_language'] = kvp['language']
                    return None
            return None
        return None

    def get_extendedcapabilities(self):
        ''' Add child to ows:OperationsMetadata Element '''

        if self.inspire_config is not None:

            ex_caps = etree.Element(
                util.nspath_eval('inspire_ds:ExtendedCapabilities', self.inspire_namespaces))

            ex_caps.attrib[util.nspath_eval('xsi:schemaLocation', self.context.namespaces)] = \
            '%s %s/inspire_ds.xsd' % \
            (self.inspire_namespaces['inspire_ds'], self.inspire_namespaces['inspire_ds'])

            # Resource Locator
            res_loc = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:ResourceLocator', self.inspire_namespaces))

            etree.SubElement(res_loc,
            util.nspath_eval('inspire_common:URL', self.inspire_namespaces)).text = '%sservice=CSW&version=2.0.2&request=GetCapabilities' % (util.bind_url(self.url))

            etree.SubElement(res_loc,
            util.nspath_eval('inspire_common:MediaType', self.inspire_namespaces)).text = 'application/xml'

            # Resource Type
            etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:ResourceType', self.inspire_namespaces)).text = 'service'

            # Temporal Reference
            temp_ref = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:TemporalReference', self.inspire_namespaces))

            temp_extent = etree.SubElement(temp_ref,
            util.nspath_eval('inspire_common:TemporalExtent', self.inspire_namespaces))

            val = self.inspire_config['temp_extent'].split('/')

            if len(val) == 1:
                etree.SubElement(temp_extent,
                util.nspath_eval('inspire_common:IndividualDate', self.inspire_namespaces)).text = val[0]

            else:
                interval_dates = etree.SubElement(temp_extent,
                util.nspath_eval('inspire_common:IntervalOfDates', self.inspire_namespaces))

                etree.SubElement(interval_dates,
                util.nspath_eval('inspire_common:StartingDate', self.inspire_namespaces)).text = val[0]

                etree.SubElement(interval_dates,
                util.nspath_eval('inspire_common:EndDate', self.inspire_namespaces)).text = val[1]

            # Conformity - service
            cfm = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:Conformity', self.inspire_namespaces))

            spec = etree.SubElement(cfm,
            util.nspath_eval('inspire_common:Specification', self.inspire_namespaces))

            spec.attrib[util.nspath_eval('xsi:type', self.context.namespaces)] =  'inspire_common:citationInspireInteroperabilityRegulation_eng'

            etree.SubElement(spec,
            util.nspath_eval('inspire_common:Title', self.inspire_namespaces)).text = 'COMMISSION REGULATION (EU) No 1089/2010 of 23 November 2010 implementing Directive 2007/2/EC of the European Parliament and of the Council as regards interoperability of spatial data sets and services'

            etree.SubElement(spec,
            util.nspath_eval('inspire_common:DateOfPublication', self.inspire_namespaces)).text = '2010-12-08'

            etree.SubElement(spec,
            util.nspath_eval('inspire_common:URI', self.inspire_namespaces)).text = 'OJ:L:2010:323:0011:0102:EN:PDF'

            spec_loc = etree.SubElement(spec,
            util.nspath_eval('inspire_common:ResourceLocator', self.inspire_namespaces))

            etree.SubElement(spec_loc,
            util.nspath_eval('inspire_common:URL', self.inspire_namespaces)).text = 'http://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=OJ:L:2010:323:0011:0102:EN:PDF'

            etree.SubElement(spec_loc,
            util.nspath_eval('inspire_common:MediaType', self.inspire_namespaces)).text = 'application/pdf'

            spec = etree.SubElement(cfm,
            util.nspath_eval('inspire_common:Degree', self.inspire_namespaces)).text = self.inspire_config['conformity_service']

            # Metadata Point of Contact
            poc = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:MetadataPointOfContact', self.inspire_namespaces))

            etree.SubElement(poc,
            util.nspath_eval('inspire_common:OrganisationName', self.inspire_namespaces)).text = self.inspire_config['contact_name']

            etree.SubElement(poc,
            util.nspath_eval('inspire_common:EmailAddress', self.inspire_namespaces)).text = self.inspire_config['contact_email']

            # Metadata Date
            etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:MetadataDate', self.inspire_namespaces)).text = self.inspire_config['date']

            # Spatial Data Service Type
            etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:SpatialDataServiceType', self.inspire_namespaces)).text = 'discovery'

            # Mandatory Keyword
            mkey = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:MandatoryKeyword', self.inspire_namespaces))

            mkey.attrib[util.nspath_eval('xsi:type', self.context.namespaces)] = 'inspire_common:classificationOfSpatialDataService'

            etree.SubElement(mkey,
            util.nspath_eval('inspire_common:KeywordValue', self.inspire_namespaces)).text = 'infoCatalogueService'

            # Gemet Keywords

            for gkw in self.inspire_config['gemet_keywords'].split(','):
                gkey = etree.SubElement(ex_caps,
                util.nspath_eval('inspire_common:Keyword', self.inspire_namespaces))

                gkey.attrib[util.nspath_eval('xsi:type', self.context.namespaces)] = 'inspire_common:inspireTheme_eng'

                ocv = etree.SubElement(gkey,
                util.nspath_eval('inspire_common:OriginatingControlledVocabulary', self.inspire_namespaces))

                etree.SubElement(ocv,
                util.nspath_eval('inspire_common:Title', self.inspire_namespaces)).text = 'GEMET - INSPIRE themes'

                etree.SubElement(ocv,
                util.nspath_eval('inspire_common:DateOfPublication', self.inspire_namespaces)).text = '2008-06-01'

                etree.SubElement(gkey,
                util.nspath_eval('inspire_common:KeywordValue', self.inspire_namespaces)).text = gkw

            # Languages
            slang = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:SupportedLanguages', self.inspire_namespaces))

            dlang = etree.SubElement(slang,
            util.nspath_eval('inspire_common:DefaultLanguage', self.inspire_namespaces))

            etree.SubElement(dlang,
            util.nspath_eval('inspire_common:Language', self.inspire_namespaces)).text = self.inspire_config['default_language']

            for l in self.inspire_config['languages_supported'].split(','):
                lang = etree.SubElement(slang,
                util.nspath_eval('inspire_common:SupportedLanguage', self.inspire_namespaces))

                etree.SubElement(lang,
                util.nspath_eval('inspire_common:Language', self.inspire_namespaces)).text = l

            clang = etree.SubElement(ex_caps,
            util.nspath_eval('inspire_common:ResponseLanguage', self.inspire_namespaces))
            etree.SubElement(clang,
            util.nspath_eval('inspire_common:Language', self.inspire_namespaces)).text = self.inspire_config['current_language']

            return ex_caps

    def get_schemacomponents(self):
        ''' Return schema components as lxml.etree.Element list '''

        node1 = etree.Element(
        util.nspath_eval('csw:SchemaComponent', self.context.namespaces),
        schemaLanguage='XMLSCHEMA', targetNamespace=self.namespace,
        parentSchema='gmd.xsd')

        schema_file = os.path.join(self.context.pycsw_home, 'plugins',
                                   'profiles', 'apiso', 'schemas', 'ogc',
                                   'iso', '19139', '20060504', 'gmd',
                                   'identification.xsd')

        schema = etree.parse(schema_file, self.context.parser).getroot()

        node1.append(schema)

        node2 = etree.Element(
        util.nspath_eval('csw:SchemaComponent', self.context.namespaces),
        schemaLanguage='XMLSCHEMA', targetNamespace=self.namespace,
        parentSchema='gmd.xsd')

        schema_file = os.path.join(self.context.pycsw_home, 'plugins',
                                   'profiles', 'apiso', 'schemas', 'ogc',
                                   'iso', '19139', '20060504', 'srv',
                                   'serviceMetadata.xsd')

        schema = etree.parse(schema_file, self.context.parser).getroot()

        node2.append(schema)

        return [node1, node2]

    def check_getdomain(self, kvp):
        '''Perform extra profile specific checks in the GetDomain request'''
        return None

    def write_record(self, result, esn, outputschema, queryables, caps=None):
        ''' Return csw:SearchResults child as lxml.etree.Element '''
        typename = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Typename'])
        is_iso_anyway = False

        xml_blob = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:XML'])
        if caps is None and xml_blob is not None and xml_blob.startswith(b'<gmd:MD_Metadata'):
            is_iso_anyway = True

        if (esn == 'full' and (typename == 'gmd:MD_Metadata' or is_iso_anyway)):
            # dump record as is and exit
            return etree.fromstring(xml_blob, self.context.parser)

        node = etree.Element(util.nspath_eval('gmd:MD_Metadata', self.namespaces))
        node.attrib[util.nspath_eval('xsi:schemaLocation', self.context.namespaces)] = \
        '%s %s/csw/2.0.2/profiles/apiso/1.0.0/apiso.xsd' % (self.namespace, self.ogc_schemas_base)

        # identifier
        idval = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Identifier'])

        identifier = etree.SubElement(node, util.nspath_eval('gmd:fileIdentifier', self.namespaces))
        etree.SubElement(identifier, util.nspath_eval('gco:CharacterString', self.namespaces)).text = idval

        if esn in ['summary', 'full']:
            # language
            val = util.getqattr(result, queryables['apiso:Language']['dbcol'])

            lang = etree.SubElement(node, util.nspath_eval('gmd:language', self.namespaces))
            etree.SubElement(lang, util.nspath_eval('gco:CharacterString', self.namespaces)).text = val

        # hierarchyLevel
        mtype = util.getqattr(result, queryables['apiso:Type']['dbcol']) or None

        if mtype is not None:
            if mtype == 'http://purl.org/dc/dcmitype/Dataset':
                mtype = 'dataset'
            hierarchy = etree.SubElement(node, util.nspath_eval('gmd:hierarchyLevel', self.namespaces))
            hierarchy.append(_write_codelist_element('gmd:MD_ScopeCode', mtype, self.namespaces))

        if esn in ['summary', 'full']:
            # contact
            contact = etree.SubElement(node, util.nspath_eval('gmd:contact', self.namespaces))
            if caps is not None:
                CI_resp = etree.SubElement(contact, util.nspath_eval('gmd:CI_ResponsibleParty', self.namespaces))
                if hasattr(caps.provider.contact, 'name'):
                    ind_name = etree.SubElement(CI_resp, util.nspath_eval('gmd:individualName', self.namespaces))
                    etree.SubElement(ind_name, util.nspath_eval('gco:CharacterString', self.namespaces)).text = caps.provider.contact.name
                if hasattr(caps.provider.contact, 'organization'):
                    if caps.provider.contact.organization is not None:
                        org_val = caps.provider.contact.organization
                    else:
                        org_val = caps.provider.name
                    org_name = etree.SubElement(CI_resp, util.nspath_eval('gmd:organisationName', self.namespaces))
                    etree.SubElement(org_name, util.nspath_eval('gco:CharacterString', self.namespaces)).text = org_val
                if hasattr(caps.provider.contact, 'position'):
                    pos_name = etree.SubElement(CI_resp, util.nspath_eval('gmd:positionName', self.namespaces))
                    etree.SubElement(pos_name, util.nspath_eval('gco:CharacterString', self.namespaces)).text = caps.provider.contact.position
                contact_info = etree.SubElement(CI_resp, util.nspath_eval('gmd:contactInfo', self.namespaces))
                ci_contact = etree.SubElement(contact_info, util.nspath_eval('gmd:CI_Contact', self.namespaces))
                if hasattr(caps.provider.contact, 'phone'):
                    phone = etree.SubElement(ci_contact, util.nspath_eval('gmd:phone', self.namespaces))
                    ci_phone = etree.SubElement(phone, util.nspath_eval('gmd:CI_Telephone', self.namespaces))
                    voice = etree.SubElement(ci_phone, util.nspath_eval('gmd:voice', self.namespaces))
                    etree.SubElement(voice, util.nspath_eval('gco:CharacterString', self.namespaces)).text = caps.provider.contact.phone
                    if hasattr(caps.provider.contact, 'fax'):
                        fax = etree.SubElement(ci_phone, util.nspath_eval('gmd:facsimile', self.namespaces))
                        etree.SubElement(fax, util.nspath_eval('gco:CharacterString', self.namespaces)).text = caps.provider.contact.fax
                address = etree.SubElement(ci_contact, util.nspath_eval('gmd:address', self.namespaces))
                ci_address = etree.SubElement(address, util.nspath_eval('gmd:CI_Address', self.namespaces))
                if hasattr(caps.provider.contact, 'address'):
                    delivery_point = etree.SubElement(ci_address, util.nspath_eval('gmd:deliveryPoint', self.namespaces))
                    etree.SubElement(delivery_point, util.nspath_eval('gco:CharacterString', self.namespaces)).text = caps.provider.contact.address
                if hasattr(caps.provider.contact, 'city'):
                    city = etree.SubElement(ci_address, util.nspath_eval('gmd:city', self.namespaces))
                    etree.SubElement(city, util.nspath_eval('gco:CharacterString', self.namespaces)).text = caps.provider.contact.city
                if hasattr(caps.provider.contact, 'region'):
                    admin_area = etree.SubElement(ci_address, util.nspath_eval('gmd:administrativeArea', self.namespaces))
                    etree.SubElement(admin_area, util.nspath_eval('gco:CharacterString', self.namespaces)).text = caps.provider.contact.region
                if hasattr(caps.provider.contact, 'postcode'):
                    postal_code = etree.SubElement(ci_address, util.nspath_eval('gmd:postalCode', self.namespaces))
                    etree.SubElement(postal_code, util.nspath_eval('gco:CharacterString', self.namespaces)).text = caps.provider.contact.postcode
                if hasattr(caps.provider.contact, 'country'):
                    country = etree.SubElement(ci_address, util.nspath_eval('gmd:country', self.namespaces))
                    etree.SubElement(country, util.nspath_eval('gco:CharacterString', self.namespaces)).text = caps.provider.contact.country
                if hasattr(caps.provider.contact, 'email'):
                    email = etree.SubElement(ci_address, util.nspath_eval('gmd:electronicMailAddress', self.namespaces))
                    etree.SubElement(email, util.nspath_eval('gco:CharacterString', self.namespaces)).text = caps.provider.contact.email

                contact_url = None
                if hasattr(caps.provider, 'url'):
                    contact_url = caps.provider.url
                if hasattr(caps.provider.contact, 'url') and caps.provider.contact.url is not None:
                    contact_url = caps.provider.contact.url

                if contact_url is not None:
                    online_resource = etree.SubElement(ci_contact, util.nspath_eval('gmd:onlineResource', self.namespaces))
                    gmd_linkage = etree.SubElement(online_resource, util.nspath_eval('gmd:linkage', self.namespaces))
                    etree.SubElement(gmd_linkage, util.nspath_eval('gmd:URL', self.namespaces)).text = contact_url

                if hasattr(caps.provider.contact, 'role'):
                    role = etree.SubElement(CI_resp, util.nspath_eval('gmd:role', self.namespaces))
                    role_val = caps.provider.contact.role
                    if role_val is None:
                        role_val = 'pointOfContact'
                    etree.SubElement(role, util.nspath_eval('gmd:CI_RoleCode', self.namespaces), codeListValue=role_val, codeList='%s#CI_RoleCode' % CODELIST).text = role_val
            else:
                val = util.getqattr(result, queryables['apiso:OrganisationName']['dbcol'])
                if val:
                    CI_resp = etree.SubElement(contact, util.nspath_eval('gmd:CI_ResponsibleParty', self.namespaces))
                    org_name = etree.SubElement(CI_resp, util.nspath_eval('gmd:organisationName', self.namespaces))
                    etree.SubElement(org_name, util.nspath_eval('gco:CharacterString', self.namespaces)).text = val

            # date
            val = util.getqattr(result, queryables['apiso:Modified']['dbcol'])
            date = etree.SubElement(node, util.nspath_eval('gmd:dateStamp', self.namespaces))
            if val and val.find('T') != -1:
                dateel = 'gco:DateTime'
            else:
                dateel = 'gco:Date'
            etree.SubElement(date, util.nspath_eval(dateel, self.namespaces)).text = val

            metadatastandardname = 'ISO19115'
            metadatastandardversion = '2003/Cor.1:2006'

            if mtype == 'service':
                metadatastandardname = 'ISO19119'
                metadatastandardversion = '2005/PDAM 1'

            # metadata standard name
            standard = etree.SubElement(node, util.nspath_eval('gmd:metadataStandardName', self.namespaces))
            etree.SubElement(standard, util.nspath_eval('gco:CharacterString', self.namespaces)).text = metadatastandardname

            # metadata standard version
            standardver = etree.SubElement(node, util.nspath_eval('gmd:metadataStandardVersion', self.namespaces))
            etree.SubElement(standardver, util.nspath_eval('gco:CharacterString', self.namespaces)).text = metadatastandardversion

        # title
        val = util.getqattr(result, queryables['apiso:Title']['dbcol']) or ''
        identification = etree.SubElement(node, util.nspath_eval('gmd:identificationInfo', self.namespaces))

        if mtype == 'service':
           restagname = 'srv:SV_ServiceIdentification'
        else:
           restagname = 'gmd:MD_DataIdentification'

        resident = etree.SubElement(identification, util.nspath_eval(restagname, self.namespaces), id=idval)
        tmp2 = etree.SubElement(resident, util.nspath_eval('gmd:citation', self.namespaces))
        tmp3 = etree.SubElement(tmp2, util.nspath_eval('gmd:CI_Citation', self.namespaces))
        tmp4 = etree.SubElement(tmp3, util.nspath_eval('gmd:title', self.namespaces))
        etree.SubElement(tmp4, util.nspath_eval('gco:CharacterString', self.namespaces)).text = val

        # creation date
        val = util.getqattr(result, queryables['apiso:CreationDate']['dbcol'])
        if val is not None:
            tmp3.append(_write_date(val, 'creation', self.namespaces))
        # publication date
        val = util.getqattr(result, queryables['apiso:PublicationDate']['dbcol'])
        if val is not None:
            tmp3.append(_write_date(val, 'publication', self.namespaces))
        # revision date
        val = util.getqattr(result, queryables['apiso:RevisionDate']['dbcol'])
        if val is not None:
            tmp3.append(_write_date(val, 'revision', self.namespaces))

        if esn in ['summary', 'full']:
            # abstract
            val = util.getqattr(result, queryables['apiso:Abstract']['dbcol']) or ''
            tmp = etree.SubElement(resident, util.nspath_eval('gmd:abstract', self.namespaces))
            etree.SubElement(tmp, util.nspath_eval('gco:CharacterString', self.namespaces)).text = val

            # keywords
            kw = util.getqattr(result, queryables['apiso:Subject']['dbcol'])
            if kw is not None:
                md_keywords = etree.SubElement(resident, util.nspath_eval('gmd:descriptiveKeywords', self.namespaces))
                md_keywords.append(write_keywords(kw, self.namespaces))

            # spatial resolution
            val = util.getqattr(result, queryables['apiso:Denominator']['dbcol'])
            if val:
                tmp = etree.SubElement(resident, util.nspath_eval('gmd:spatialResolution', self.namespaces))
                tmp2 = etree.SubElement(tmp, util.nspath_eval('gmd:MD_Resolution', self.namespaces))
                tmp3 = etree.SubElement(tmp2, util.nspath_eval('gmd:equivalentScale', self.namespaces))
                tmp4 = etree.SubElement(tmp3, util.nspath_eval('gmd:MD_RepresentativeFraction', self.namespaces))
                tmp5 = etree.SubElement(tmp4, util.nspath_eval('gmd:denominator', self.namespaces))
                etree.SubElement(tmp5, util.nspath_eval('gco:Integer', self.namespaces)).text = str(val)

            # resource language
            val = util.getqattr(result, queryables['apiso:ResourceLanguage']['dbcol'])
            tmp = etree.SubElement(resident, util.nspath_eval('gmd:language', self.namespaces))
            etree.SubElement(tmp, util.nspath_eval('gco:CharacterString', self.namespaces)).text = val

            # topic category
            val = util.getqattr(result, queryables['apiso:TopicCategory']['dbcol'])
            if val:
                for v in val.split(','):
                    tmp = etree.SubElement(resident, util.nspath_eval('gmd:topicCategory', self.namespaces))
                    etree.SubElement(tmp, util.nspath_eval('gmd:MD_TopicCategoryCode', self.namespaces)).text = val

        # bbox extent
        val = util.getqattr(result, queryables['apiso:BoundingBox']['dbcol'])
        bboxel = write_extent(val, self.namespaces)
        if bboxel is not None and mtype != 'service':
            resident.append(bboxel)

        # service identification

        if mtype == 'service':
            # service type
            # service type version
            val = util.getqattr(result, queryables['apiso:ServiceType']['dbcol'])
            val2 = util.getqattr(result, queryables['apiso:ServiceTypeVersion']['dbcol'])
            if val is not None:
                tmp = etree.SubElement(resident, util.nspath_eval('srv:serviceType', self.namespaces))
                etree.SubElement(tmp, util.nspath_eval('gco:LocalName', self.namespaces)).text = val
                tmp = etree.SubElement(resident, util.nspath_eval('srv:serviceTypeVersion', self.namespaces))
                etree.SubElement(tmp, util.nspath_eval('gco:CharacterString', self.namespaces)).text = val2

            kw = util.getqattr(result, queryables['apiso:Subject']['dbcol'])
            if kw is not None:
                srv_keywords = etree.SubElement(resident, util.nspath_eval('srv:keywords', self.namespaces))
                srv_keywords.append(write_keywords(kw, self.namespaces))

            if bboxel is not None:
                bboxel.tag = util.nspath_eval('srv:extent', self.namespaces)
                resident.append(bboxel)

            val = util.getqattr(result, queryables['apiso:CouplingType']['dbcol'])
            if val is not None:
                couplingtype = etree.SubElement(resident, util.nspath_eval('srv:couplingType', self.namespaces))
                etree.SubElement(couplingtype, util.nspath_eval('srv:SV_CouplingType', self.namespaces), codeListValue=val, codeList='%s#SV_CouplingType' % CODELIST).text = val

            if esn in ['summary', 'full']:
                # all service resources as coupled resources
                coupledresources = util.getqattr(result, queryables['apiso:OperatesOn']['dbcol'])
                operations = util.getqattr(result, queryables['apiso:Operation']['dbcol'])

                if coupledresources:
                    for val2 in coupledresources.split(','):
                        coupledres = etree.SubElement(resident, util.nspath_eval('srv:coupledResource', self.namespaces))
                        svcoupledres = etree.SubElement(coupledres, util.nspath_eval('srv:SV_CoupledResource', self.namespaces))
                        opname = etree.SubElement(svcoupledres, util.nspath_eval('srv:operationName', self.namespaces))
                        etree.SubElement(opname, util.nspath_eval('gco:CharacterString', self.namespaces)).text = _get_resource_opname(operations)
                        sid = etree.SubElement(svcoupledres, util.nspath_eval('srv:identifier', self.namespaces))
                        etree.SubElement(sid, util.nspath_eval('gco:CharacterString', self.namespaces)).text = val2

                # service operations
                if operations:
                    for i in operations.split(','):
                        oper = etree.SubElement(resident, util.nspath_eval('srv:containsOperations', self.namespaces))
                        tmp = etree.SubElement(oper, util.nspath_eval('srv:SV_OperationMetadata', self.namespaces))

                        tmp2 = etree.SubElement(tmp, util.nspath_eval('srv:operationName', self.namespaces))
                        etree.SubElement(tmp2, util.nspath_eval('gco:CharacterString', self.namespaces)).text = i

                        tmp3 = etree.SubElement(tmp, util.nspath_eval('srv:DCP', self.namespaces))
                        etree.SubElement(tmp3, util.nspath_eval('srv:DCPList', self.namespaces), codeList='%s#DCPList' % CODELIST, codeListValue='HTTPGet').text = 'HTTPGet'

                        tmp4 = etree.SubElement(tmp, util.nspath_eval('srv:DCP', self.namespaces))
                        etree.SubElement(tmp4, util.nspath_eval('srv:DCPList', self.namespaces), codeList='%s#DCPList' % CODELIST, codeListValue='HTTPPost').text = 'HTTPPost'

                        connectpoint = etree.SubElement(tmp, util.nspath_eval('srv:connectPoint', self.namespaces))
                        onlineres = etree.SubElement(connectpoint, util.nspath_eval('gmd:CI_OnlineResource', self.namespaces))
                        linkage = etree.SubElement(onlineres, util.nspath_eval('gmd:linkage', self.namespaces))
                        etree.SubElement(linkage, util.nspath_eval('gmd:URL', self.namespaces)).text = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Source'])

                # operates on resource(s)
                if coupledresources:
                    for i in coupledresources.split(','):
                        operates_on = etree.SubElement(resident, util.nspath_eval('srv:operatesOn', self.namespaces), uuidref=i)
                        operates_on.attrib[util.nspath_eval('xlink:href', self.namespaces)] = '%sservice=CSW&version=2.0.2&request=GetRecordById&outputschema=http://www.isotc211.org/2005/gmd&id=%s-%s' % (util.bind_url(self.url), idval, i)

        rlinks = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Links'])

        if rlinks:
            distinfo = etree.SubElement(node, util.nspath_eval('gmd:distributionInfo', self.namespaces))
            distinfo2 = etree.SubElement(distinfo, util.nspath_eval('gmd:MD_Distribution', self.namespaces))
            transopts = etree.SubElement(distinfo2, util.nspath_eval('gmd:transferOptions', self.namespaces))
            dtransopts = etree.SubElement(transopts, util.nspath_eval('gmd:MD_DigitalTransferOptions', self.namespaces))

            for link in rlinks.split('^'):
                linkset = link.split(',')
                online = etree.SubElement(dtransopts, util.nspath_eval('gmd:onLine', self.namespaces))
                online2 = etree.SubElement(online, util.nspath_eval('gmd:CI_OnlineResource', self.namespaces))

                linkage = etree.SubElement(online2, util.nspath_eval('gmd:linkage', self.namespaces))
                etree.SubElement(linkage, util.nspath_eval('gmd:URL', self.namespaces)).text = linkset[-1]

                protocol = etree.SubElement(online2, util.nspath_eval('gmd:protocol', self.namespaces))
                etree.SubElement(protocol, util.nspath_eval('gco:CharacterString', self.namespaces)).text = linkset[2]

                name = etree.SubElement(online2, util.nspath_eval('gmd:name', self.namespaces))
                etree.SubElement(name, util.nspath_eval('gco:CharacterString', self.namespaces)).text = linkset[0]

                desc = etree.SubElement(online2, util.nspath_eval('gmd:description', self.namespaces))
                etree.SubElement(desc, util.nspath_eval('gco:CharacterString', self.namespaces)).text = linkset[1]

        return node

def write_keywords(keywords, nsmap):
    """generate gmd:MD_Keywords construct"""
    md_keywords = etree.Element(util.nspath_eval('gmd:MD_Keywords', nsmap))
    for kw in keywords.split(','):
        keyword = etree.SubElement(md_keywords, util.nspath_eval('gmd:keyword', nsmap))
        etree.SubElement(keyword, util.nspath_eval('gco:CharacterString', nsmap)).text = kw
    return md_keywords

def write_extent(bbox, nsmap):
    ''' Generate BBOX extent '''

    if bbox is not None:
        try:
            bbox2 = util.wkt2geom(bbox)
        except:
            return None
        extent = etree.Element(util.nspath_eval('gmd:extent', nsmap))
        ex_extent = etree.SubElement(extent, util.nspath_eval('gmd:EX_Extent', nsmap))
        ge = etree.SubElement(ex_extent, util.nspath_eval('gmd:geographicElement', nsmap))
        gbb = etree.SubElement(ge, util.nspath_eval('gmd:EX_GeographicBoundingBox', nsmap))
        west = etree.SubElement(gbb, util.nspath_eval('gmd:westBoundLongitude', nsmap))
        east = etree.SubElement(gbb, util.nspath_eval('gmd:eastBoundLongitude', nsmap))
        south = etree.SubElement(gbb, util.nspath_eval('gmd:southBoundLatitude', nsmap))
        north = etree.SubElement(gbb, util.nspath_eval('gmd:northBoundLatitude', nsmap))

        etree.SubElement(west, util.nspath_eval('gco:Decimal', nsmap)).text = str(bbox2[0])
        etree.SubElement(south, util.nspath_eval('gco:Decimal', nsmap)).text = str(bbox2[1])
        etree.SubElement(east, util.nspath_eval('gco:Decimal', nsmap)).text = str(bbox2[2])
        etree.SubElement(north, util.nspath_eval('gco:Decimal', nsmap)).text = str(bbox2[3])
        return extent
    return None

def _write_date(dateval, datetypeval, nsmap):
    date1 = etree.Element(util.nspath_eval('gmd:date', nsmap))
    date2 = etree.SubElement(date1, util.nspath_eval('gmd:CI_Date', nsmap))
    date3 = etree.SubElement(date2, util.nspath_eval('gmd:date', nsmap))
    if dateval.find('T') != -1:
        dateel = 'gco:DateTime'
    else:
        dateel = 'gco:Date'
    etree.SubElement(date3, util.nspath_eval(dateel, nsmap)).text = dateval
    datetype = etree.SubElement(date2, util.nspath_eval('gmd:dateType', nsmap))
    datetype.append(_write_codelist_element('gmd:CI_DateTypeCode', datetypeval, nsmap))
    return date1

def _get_resource_opname(operations):
    for op in operations.split(','):
        if op in ['GetMap', 'GetFeature', 'GetCoverage', 'GetObservation']:
            return op
    return None

def _write_codelist_element(codelist_element, codelist_value, nsmap):
    namespace, codelist = codelist_element.split(':')

    element = etree.Element(util.nspath_eval(codelist_element, nsmap),
    codeSpace=CODESPACE, codeList='%s#%s' % (CODELIST, codelist),
    codeListValue=codelist_value)

    element.text = codelist_value

    return element
