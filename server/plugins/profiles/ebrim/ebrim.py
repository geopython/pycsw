# -*- coding: iso-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2011 Tom Kralidis
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
from server import config, server, util
from server.plugins.profiles import profile

class EbrimStaticContext(object):

    def __init__(self):
        self.NAMESPACES = {
            'rim': 'urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0',
            'wrs': 'http://www.opengis.net/cat/wrs/1.0'
        }

        self.REPOSITORY = {
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

class EBRIM(profile.Profile):
    ''' EBRIM class '''
    def __init__(self, model, namespaces, globalstaticcontext):
        self.globalstaticcontext = globalstaticcontext
        self.staticcontext = EbrimStaticContext()

        profile.Profile.__init__(self,
            name='ebrim',
            version='1.0.1',
            title='ebRIM profile of CSW',
            url='http://portal.opengeospatial.org/files/?artifact_id=31137',
            namespace=self.staticcontext.NAMESPACES['rim'],
            typename='rim:RegistryObject',
            outputschema=self.staticcontext.NAMESPACES['rim'],
            prefixes=['rim'],
            model=model,
            core_namespaces=namespaces,
            added_namespaces=self.staticcontext.NAMESPACES,
            repository=self.staticcontext.REPOSITORY['rim:RegistryObject'])

    def nspath_eval(self, astr):
        return util.nspath_eval(astr, self.globalstaticcontext)

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
        self.nspath_eval('csw:SchemaComponent'),
        schemaLanguage = 'XMLSCHEMA', targetNamespace = self.namespace)

        schema = etree.parse(os.path.join(
                'server', 'plugins', 'profiles', 'ebrim',
                'etc', 'schemas', 'ogc', 'csw', '2.0.2',
                'profiles', 'ebrim', '1.0', 'csw-ebrim.xsd')).getroot()

        node.append(schema)

        return [node]

    def check_getdomain(self, kvp):
        '''Perform extra profile specific checks in the GetDomain request'''
        return None

    def write_record(self, result, esn, outputschema, queryables):
        ''' Return csw:SearchResults child as lxml.etree.Element '''

        identifier = util.getqattr(result, self.globalstaticcontext.MD_CORE_MODEL['mappings']['pycsw:Identifier'])
        typename = util.getqattr(result, self.globalstaticcontext.MD_CORE_MODEL['mappings']['pycsw:Typename'])

        if esn == 'full' and typename == 'rim:RegistryObject':
            # dump record as is and exit
            return etree.fromstring(util.getqattr(result, queryables['pycsw:XML']['dbcol']))

        if typename == 'csw:Record':  # transform csw:Record -> rim:RegistryObject model mappings
            util.transform_mappings(queryables, self.staticcontext.REPOSITORY['rim:RegistryObject']['mappings']['csw:Record'])

        node = etree.Element(self.nspath_eval('rim:ExtrinsicObject'))
        node.attrib[self.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/profiles/ebrim/1.0/csw-ebrim.xsd' % (self.staticcontext.NAMESPACES['wrs'], self.ogc_schemas_base)

        node.attrib['id'] = identifier
        node.attrib['lid'] = identifier
        node.attrib['objectType'] = str(util.getqattr(result, self.globalstaticcontext.MD_CORE_MODEL['mappings']['pycsw:Type']))
        node.attrib['status'] = 'urn:oasis:names:tc:ebxml-regrep:StatusType:Submitted'

        etree.SubElement(node, self.nspath_eval('rim:VersionInfo'), versionName='')

        if esn == 'summary':
            etree.SubElement(node, self.nspath_eval('rim:ExternalIdentifier'), value=identifier, identificationScheme='foo', registryObject=str(util.getqattr(result, self.globalstaticcontext.MD_CORE_MODEL['mappings']['pycsw:Relation'])), id=identifier)

            name = etree.SubElement(node, self.nspath_eval('rim:Name'))
            etree.SubElement(name, self.nspath_eval('rim:LocalizedString'), value=unicode(util.getqattr(result, queryables['pycsw:Title']['dbcol'])))

            description = etree.SubElement(node, self.nspath_eval('rim:Description'))
            etree.SubElement(description, self.nspath_eval('rim:LocalizedString'), value=unicode(util.getqattr(result, queryables['pycsw:Abstract']['dbcol'])))

            val = util.getqattr(result, self.globalstaticcontext.MD_CORE_MODEL['mappings']['pycsw:BoundingBox'])
            bboxel = server.write_boundingbox(val)

            if bboxel is not None:
                bboxslot = etree.SubElement(node, self.nspath_eval('rim:Slot'),
                slotType='urn:ogc:def:dataType:ISO-19107:2003:GM_Envelope')

                valuelist = etree.SubElement(bboxslot, self.nspath_eval('rim:ValueList'))
                value = etree.SubElement(valuelist, self.nspath_eval('rim:Value'))
                value.append(bboxel)

            rkeywords = util.getqattr(result, self.globalstaticcontext.MD_CORE_MODEL['mappings']['pycsw:Keywords'])
            if rkeywords is not None:
                subjectslot = etree.SubElement(node, self.nspath_eval('rim:Slot'),
                name='http://purl.org/dc/elements/1.1/subject')
                valuelist = etree.SubElement(subjectslot, self.nspath_eval('rim:ValueList'))
                for keyword in rkeywords.split(','):
                    etree.SubElement(valuelist,
                    self.nspath_eval('rim:Value')).text = keyword

        return node
