# -*- coding: ISO-8859-15 -*-
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
from server import profile, config, util

NAMESPACES = {
    'fgdc': 'http://www.opengis.net/cat/csw/csdgm'
}

REPOSITORY = {
    'fgdc:metadata': {
        'outputschema': 'http://www.opengis.net/cat/csw/csdgm',
        'queryables': {
            'SupportedFGDCQueryables': {
                'fgdc:Title': 'idinfo/citation/citinfo/title',
                'fgdc:Originator': 'idinfo/citation/citeinfo/origin',
                'fgdc:Publisher': 'idinfo/citation/citeinfo/publinfo/publish',
                'fgdc:Abstract': 'idinfo/descript/abstract',
                'fgdc:Purpose': 'idinfo/descript/purpose',
                'fgdc:GeospatialPresentationForm': 'idinfo/citation/citeinfo/geoform',
                'fgdc:PublicationDate': 'idinfo/citation/citeinfo/pubdate',
                'fgdc:ThemeKeywords': 'idinfo/keywords/theme/themekey',
                'fgdc:Progress': 'idinfo/status/progress',
                'fgdc:BeginDate': 'idinfo/timeperd/timeinfo/rngdates/begdate',
                'fgdc:EndDate': 'idinfo/timeperd/timeinfo/rngdates/enddate',
                'fgdc:Origin': 'idinfo/citation/citeinfo/origin',
                'fgdc:Contributor': 'idinfo/datacred',
                'fgdc:AccessConstraints': 'idinfo/accconst',
                'fgdc:Modified': 'metainfo/metd',
                'fgdc:Type': 'idinfo/spdoinfo/direct',
                'fgdc:Format': 'distinfo/stdorder/digform/digtinfo/formname',
                'fgdc:Source': 'lineage/srcinfo/srccite/citeinfo/title',
                'fgdc:Relation': 'idinfo/citation/citeinfo/onlink',
                'fgdc:Envelope': 'bbox',
                'fgdc:AnyText': 'xml'
            }
        },
        'mappings': {
            'csw:Record': {
                # map DIF queryables to DC queryables
                'fgdc:Title': 'dc:title',
                'fgdc:Origin': 'dc:creator',
                'fgdc:Publisher': 'dc:publisher',
                'fgdc:Contributor': 'dc:contributor',
                'fgdc:AccessConstraints': 'dc:rights',
                'fgdc:ThemeKeywords': 'dc:subject',
                'fgdc:Abstract': 'dct:abstract',
                'fgdc:Type': 'dct:abstract',
                'fgdc:Format': 'dc:format',
                'fgdc:Source': 'dc:source',
                'fgdc:Relation': 'dc:relation'
            }
        }
    }
}

class FGDC(profile.Profile):
    ''' FGDC class '''
    def __init__(self, model, namespaces):
        profile.Profile.__init__(self,
            name='fgdc',
            version='0.0.12',
            title='FGDC CSDGM Application Profile for CSW 2.0',
            url='http://portal.opengeospatial.org/files/?artifact_id=16936',
            namespace=NAMESPACES['fgdc'],
            typename='fgdc:metadata',
            outputschema=NAMESPACES['fgdc'],
            prefixes=['fgdc'],
            model=model,
            core_namespaces=namespaces,
            added_namespaces=NAMESPACES,
            repository=REPOSITORY['fgdc:metadata'])

    def extend_core(self, model, namespaces, config):
        ''' Extend core configuration '''
        return None

    def check_parameters(self, kvp):
        '''Perform extra parameters checking '''
        return None

    def get_extendedcapabilities(self):
        ''' Add child to ows:OperationsMetadata Element '''
        return None

    def get_schemacomponents(self):
        ''' Return schema components as lxml.etree.Element list '''

        node = etree.Element(
        util.nspath_eval('csw:SchemaComponent'),
        schemaLanguage = 'XMLSCHEMA', targetNamespace = self.namespace)

        schema = etree.parse(os.path.join(
                'server', 'profiles', 'fgdc',
                'etc', 'schemas', 'fgdc', 'fgdc-std-001-1998.xsd')).getroot()
        node.append(schema)

        return [node]

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

                if esn == 'brief':
                  elname = 'fgdc:BriefRecord'
                else:
                  elname = 'fgdc:SummaryRecord'

                if result.typename == 'csw:Record':  # transform csw:Record -> fgdc:metadata model mappings
                    util.transform_mappings(queryables, REPOSITORY['fgdc:metadata']['mappings']['csw:Record'])

                node = etree.Element(util.nspath_eval(elname))
                node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
                '%s http://www.fgdc.gov/metadata/fgdc-std-001-1998.xsd' % self.namespace

                # title
                val = util.query_xpath(xml, queryables['fgdc:Title'])
                if not val:
                    val = ''
                etree.SubElement(node, util.nspath_eval('fgdc:title')).text = val.decode('utf8')

                # identifier
                etree.SubElement(node, util.nspath_eval('fgdc:recordID')).text = result.identifier

                if esn == 'brief':
                    return node
        return node

def write_extent(bbox):
    ''' Generate BBOX extent '''

    from shapely.wkt import loads

    if bbox is not None:
        bbox2 = loads(bbox).exterior.bounds
        extent = etree.Element(util.nspath_eval('fgdc:bounding'))
        etree.SubElement(extent, util.nspath_eval('fgdc:westbc')).text = str(bbox2[0])
        etree.SubElement(extent, util.nspath_eval('fgdc:eastbc')).text = str(bbox2[2])
        etree.SubElement(extent, util.nspath_eval('fgdc:northbc')).text = str(bbox2[3])
        etree.SubElement(extent, util.nspath_eval('fgdc:southbc')).text = str(bbox2[1])
        return extent
    return None
