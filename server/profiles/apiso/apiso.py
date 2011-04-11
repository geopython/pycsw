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
from server import profile, config, core_queryables, util

NAMESPACES = {
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd'
}

CODELIST = 'http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml'
CODESPACE = 'ISOTC211/19115'

class APISO(profile.Profile):
    def __init__(self):
        profile.Profile.__init__(self, 'apiso', '1.0.0', 'ISO Metadata Application Profile', 'http://portal.opengeospatial.org/files/?artifact_id=21460', NAMESPACES['gmd'], 'gmd:MD_Metadata', NAMESPACES['gmd'])
        self.config=config.get_config(os.path.join('server', 'profiles', 'apiso', 'apiso.cfg'))
        
        self.corequeryables = core_queryables.CoreQueryables(self.config)
        

    def extend_core(self, model, namespaces, databases):
        ''' Extend core configuration '''

        # model
        model['operations']['DescribeRecord']['parameters']['typeName']['values'].append(self.typename)
        model['operations']['GetRecords']['parameters']['outputSchema']['values'].append(self.outputschema)
        model['operations']['GetRecords']['parameters']['typeNames']['values'].append(self.typename)
        model['operations']['GetRecordById']['parameters']['outputSchema']['values'].append(self.outputschema)
        model['constraints']['IsoProfiles'] = {}
        model['constraints']['IsoProfiles']['values'] = [self.namespace]
        model['operations']['GetRecords']['constraints']['SupportedISOQueryables'] = {
                        'values': ['apiso:Title','apiso:Abstract','apiso:Subject','apiso:RevisionDate','apiso:AlternateTitle','apiso:CreationDate','apiso:PublicationDate','apiso:OrganisationName','apiso:HasSecurityConstraints','apiso:Language','apiso:ResourceIdentifier','apiso:ParentIdentifier','apiso:KeywordType','apiso:AnyText', 'apiso:BoundingBox']
                    }
        model['operations']['GetRecords']['constraints']['AdditionalQueryables'] = {
                        'values': ['apiso:TopicCategory','apiso:ResourceLanguage','apiso:GeographicDescriptionCode','apiso:Denominator','apiso:DistanceValue','apiso:DistanceUOM','apiso:TempExtent_begin', 'apiso:TempExtent_end']
                    }

        # namespaces 
        namespaces.update(NAMESPACES)

        # databases
        databases[self.typename] = {}
        databases[self.typename]['db'] = self.config['repository']['db']
        databases[self.typename]['db_table'] = self.config['repository']['db_table']

    def get_extendedcapabilities(self):
        ''' Add child to ows:ExtendedCapabilities Element '''
        extended_capabilities = etree.Element(
                util.nspath_eval('ows:ExtendedCapabilities'))
        return extended_capabilities

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
        check = {}
        if (kvp.has_key('propertyname') is False or
            kvp.has_key('parametername') is True):
            text = 'GetDomain request must only have a PropertyName parameter \
            in APISO. ParameterName is not supported'
            check = {'error': 'true',  'locator': 'propertyname',\
                'code': 'InvalidParameterValue',  'text': text}
        return check
    

    def write_record(self, result, esn, outputschema):
        if outputschema == self.namespace:
            if esn == 'full':
                xml = getattr(result,
                self.corequeryables.mappings['apiso:AnyText']['obj_attr'])

                node = etree.fromstring(xml)

            elif esn == 'brief':
                node = etree.Element(util.nspath_eval('gmd:MD_Metadata'))
                node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
                '%s http://schemas.opengis.net/iso/19139/20060504/gmd/gmd.xsd' % self.namespace 

                # identifier
                val = getattr(result, self.corequeryables.mappings['apiso:Identifier']['obj_attr'])

                identifier = etree.SubElement(node, util.nspath_eval('gmd:fileIdentifier'))
                tmp = etree.SubElement(identifier, util.nspath_eval('gco:ChracterString')).text = val

                # hierarchyLevel
                val = getattr(result, self.corequeryables.mappings['apiso:Type']['obj_attr'])

                hierarchy = etree.SubElement(node, util.nspath_eval('gmd:hierarchyLevel'),
                codeList = '%s#MD_ScopeCode' % CODELIST,
                codeListValue = val,
                codeSpace = CODESPACE).text = val
                
                # title
                val = getattr(result, self.corequeryables.mappings['apiso:Title']['obj_attr'])
                identification = etree.SubElement(node, util.nspath_eval('gmd:identificationInfo'))
                tmp = etree.SubElement(identification, util.nspath_eval('gmd:MD_IdentificationInfo'))
                tmp2 = etree.SubElement(tmp, util.nspath_eval('gmd:citation'))
                tmp3 = etree.SubElement(tmp2, util.nspath_eval('gmd:CI_Citation'))
                tmp4 = etree.SubElement(tmp3, util.nspath_eval('gmd:title'))
                etree.SubElement(tmp4, util.nspath_eval('gco:CharacterString')).text = val

                # bbox extent
                val = getattr(result, self.corequeryables.mappings['apiso:BoundingBox']['obj_attr'])
                extent = etree.SubElement(identification, util.nspath_eval('gmd:extent'))
                tmp = etree.SubElement(extent, util.nspath_eval('gmd:EX_Extent'))
                tmp2 = etree.SubElement(tmp, util.nspath_eval('gmd:geographicElement'))
                tmp3 = etree.SubElement(tmp2, util.nspath_eval('gmd:EX_GeographicBoundingBox'))
                west = etree.SubElement(tmp3, util.nspath_eval('gmd:westBoundLongitude'))
                east = etree.SubElement(tmp3, util.nspath_eval('gmd:eastBoundLongitude'))
                north = etree.SubElement(tmp3, util.nspath_eval('gmd:northBoundLatitude'))
                south = etree.SubElement(tmp3, util.nspath_eval('gmd:southBoundLatitude'))

                bbox = val.split(',')
                etree.SubElement(west, util.nspath_eval('gco:Decimal')).text = bbox[0]
                etree.SubElement(south, util.nspath_eval('gco:Decimal')).text = bbox[1]
                etree.SubElement(east, util.nspath_eval('gco:Decimal')).text = bbox[2]
                etree.SubElement(north, util.nspath_eval('gco:Decimal')).text = bbox[3]
        else:
            node = etree.Element('TODO')
        return node
