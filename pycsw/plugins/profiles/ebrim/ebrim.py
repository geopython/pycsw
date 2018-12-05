# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
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
from pycsw.core.etree import etree
from pycsw.core import config, util
from pycsw.ogc.csw.csw2 import write_boundingbox
from pycsw.plugins.profiles import profile

from six import text_type


class EBRIM(profile.Profile):
    ''' EBRim class '''
    def __init__(self, model, namespaces, context):

        self.context = context

        self.namespaces = {
            'ebrim': 'http://www.opengis.net/cat/wrs/1.0',
            'rim': 'urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0',
            'wrs': 'http://www.opengis.net/cat/wrs/1.0'
        }

        self.repository = {
            'rim:RegistryObject': {
                'outputschema': 'urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0',
                'queryables': {},
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
            name='ebrim',
            version='1.0.1',
            title='ebRIM profile of CSW',
            url='http://portal.opengeospatial.org/files/?artifact_id=31137',
            namespace=self.namespaces['rim'],
            typename='rim:RegistryObject',
            outputschema=self.namespaces['rim'],
            prefixes=['rim'],
            model=model,
            core_namespaces=namespaces,
            added_namespaces=self.namespaces,
            repository=self.repository['rim:RegistryObject'])

    def extend_core(self, model, namespaces, config):
        ''' Extend core configuration '''

        self.ogc_schemas_base = config.get('server', 'ogc_schemas_base')

    def check_parameters(self, kvp):
        '''Check for Language parameter in GetCapabilities request'''
        return None

    def get_extendedcapabilities(self):
        ''' Add child to ows:OperationsMetadata Element '''
        return None

    def get_schemacomponents(self):
        ''' Return schema components as lxml.etree.Element list '''

        node = etree.Element(
        util.nspath_eval('csw:SchemaComponent', self.context.namespaces),
        schemaLanguage='XMLSCHEMA', targetNamespace=self.namespace)

        schema_file = os.path.join(self.context.pycsw_home, 'plugins',
                                   'profiles', 'ebrim', 'schemas', 'ogc',
                                   'csw', '2.0.2', 'profiles', 'ebrim',
                                   '1.0', 'csw-ebrim.xsd')

        schema = etree.parse(schema_file, self.context.parser).getroot()

        node.append(schema)

        return [node]

    def check_getdomain(self, kvp):
        '''Perform extra profile specific checks in the GetDomain request'''
        return None

    def write_record(self, result, esn, outputschema, queryables):
        ''' Return csw:SearchResults child as lxml.etree.Element '''

        identifier = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Identifier'])
        typename = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Typename'])

        if esn == 'full' and typename == 'rim:RegistryObject':
            # dump record as is and exit
            return etree.fromstring(util.getqattr(result, queryables['pycsw:XML']['dbcol']), self.context.parser)

        node = etree.Element(util.nspath_eval('rim:ExtrinsicObject', self.namespaces))
        node.attrib[util.nspath_eval('xsi:schemaLocation', self.context.namespaces)] = \
        '%s %s/csw/2.0.2/profiles/ebrim/1.0/csw-ebrim.xsd' % (self.namespaces['wrs'], self.ogc_schemas_base)

        node.attrib['id'] = identifier
        node.attrib['lid'] = identifier
        node.attrib['objectType'] = str(util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Type']))
        node.attrib['status'] = 'urn:oasis:names:tc:ebxml-regrep:StatusType:Submitted'

        etree.SubElement(node, util.nspath_eval('rim:VersionInfo', self.namespaces), versionName='')

        if esn in ['summary', 'full']:
            etree.SubElement(node, util.nspath_eval('rim:ExternalIdentifier', self.namespaces), value=identifier, identificationScheme='foo', registryObject=str(util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Relation'])), id=identifier)

            name = etree.SubElement(node, util.nspath_eval('rim:Name', self.namespaces))
            etree.SubElement(name, util.nspath_eval('rim:LocalizedString', self.namespaces), value=text_type(util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Title'])))

            description = etree.SubElement(node, util.nspath_eval('rim:Description', self.namespaces))
            etree.SubElement(description, util.nspath_eval('rim:LocalizedString', self.namespaces), value=text_type(util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Abstract'])))

            val = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:BoundingBox'])
            bboxel = write_boundingbox(val, self.context.namespaces)

            if bboxel is not None:
                bboxslot = etree.SubElement(node, util.nspath_eval('rim:Slot', self.namespaces),
                slotType='urn:ogc:def:dataType:ISO-19107:2003:GM_Envelope')

                valuelist = etree.SubElement(bboxslot, util.nspath_eval('rim:ValueList', self.namespaces))
                value = etree.SubElement(valuelist, util.nspath_eval('rim:Value', self.namespaces))
                value.append(bboxel)

            rkeywords = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Keywords'])
            if rkeywords is not None:
                subjectslot = etree.SubElement(node, util.nspath_eval('rim:Slot', self.namespaces),
                name='http://purl.org/dc/elements/1.1/subject')
                valuelist = etree.SubElement(subjectslot, util.nspath_eval('rim:ValueList', self.namespaces))
                for keyword in rkeywords.split(','):
                    etree.SubElement(valuelist,
                    util.nspath_eval('rim:Value', self.namespaces)).text = keyword

        return node
