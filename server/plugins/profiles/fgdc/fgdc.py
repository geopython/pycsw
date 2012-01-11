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
from server import config, util
from server.plugins.profiles import profile

NAMESPACES = {
    'fgdc': 'http://www.opengis.net/cat/csw/csdgm'
}

REPOSITORY = {
    'fgdc:metadata': {
        'outputschema': 'http://www.opengis.net/cat/csw/csdgm',
        'queryables': {
            'SupportedFGDCQueryables': {
                'fgdc:Title': {'xpath': 'idinfo/citation/citinfo/title', 'dbcol': 'title'},
                'fgdc:Originator': {'xpath': 'idinfo/citation/citeinfo/origin', 'dbcol': 'creator'},
                'fgdc:Publisher': {'xpath': 'idinfo/citation/citeinfo/publinfo/publish', 'dbcol': 'publisher'},
                'fgdc:Abstract': {'xpath': 'idinfo/descript/abstract', 'dbcol': 'abstract'},
                'fgdc:Purpose': {'xpath': 'idinfo/descript/purpose', 'dbcol': 'abstract'},
                'fgdc:GeospatialPresentationForm': {'xpath': 'idinfo/citation/citeinfo/geoform', 'dbcol': 'format'},
                'fgdc:PublicationDate': {'xpath': 'idinfo/citation/citeinfo/pubdate', 'dbcol': 'date_publication'},
                'fgdc:ThemeKeywords': {'xpath': 'idinfo/keywords/theme/themekey', 'dbcol': 'keywords'},
                'fgdc:Progress': {'xpath': 'idinfo/status/progress', 'dbcol': 'relation'},
                'fgdc:BeginDate': {'xpath': 'idinfo/timeperd/timeinfo/rngdates/begdate', 'dbcol': 'time_begin'},
                'fgdc:EndDate': {'xpath': 'idinfo/timeperd/timeinfo/rngdates/enddate', 'dbcol': 'time_end'},
                'fgdc:Origin': {'xpath': 'idinfo/citation/citeinfo/origin', 'dbcol': 'creator'},
                'fgdc:Contributor': {'xpath': 'idinfo/datacred', 'dbcol': 'contributor'},
                'fgdc:AccessConstraints': {'xpath': 'idinfo/accconst', 'dbcol': 'accessconstraints'},
                'fgdc:Modified': {'xpath': 'metainfo/metd', 'dbcol': 'date_modified'},
                'fgdc:Type': {'xpath': 'spdoinfo/direct', 'dbcol': 'type'},
                'fgdc:Format': {'xpath': 'distinfo/stdorder/digform/digtinfo/formname', 'dbcol': 'format'},
                'fgdc:Source': {'xpath': 'lineage/srcinfo/srccite/citeinfo/title', 'dbcol': 'source'},
                'fgdc:Relation': {'xpath': 'idinfo/citation/citeinfo/onlink', 'dbcol': 'relation'},
                'fgdc:Envelope': {'xpath': 'bbox', 'dbcol': 'wkt_geometry'},
                'fgdc:AnyText': {'xpath': 'xml', 'dbcol': 'anytext'}
            }
        },
        'mappings': {
            'csw:Record': {
                # map FGDC queryables to DC queryables
                'fgdc:Title': 'dc:title',
                'fgdc:Origin': 'dc:creator',
                'fgdc:Publisher': 'dc:publisher',
                'fgdc:Contributor': 'dc:contributor',
                'fgdc:AccessConstraints': 'dc:rights',
                'fgdc:ThemeKeywords': 'dc:subject',
                'fgdc:Abstract': 'dct:abstract',
                'fgdc:Type': 'dc:type',
                'fgdc:Format': 'dc:format',
                'fgdc:Source': 'dc:source',
                'fgdc:Relation': 'dc:relation',
                'fgdc:Modified': 'dct:modified',
                'fgdc:Envelope': 'ows:BoundingBox'
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
                'server', 'plugins', 'profiles', 'fgdc',
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

            if result.typename == 'csw:Record':  # transform csw:Record -> fgdc:metadata model mappings
                util.transform_mappings(queryables, REPOSITORY['fgdc:metadata']['mappings']['csw:Record'])

            if esn == 'full':  # dump the record, as is, and exit
                return xml

            node = etree.Element('metadata')
            node.attrib[util.nspath_eval('xsi:noNamespaceSchemaLocation')] = \
            'http://www.fgdc.gov/metadata/fgdc-std-001-1998.xsd'

            idinfo = etree.SubElement(node, 'idinfo')
            # identifier
            etree.SubElement(idinfo, 'datasetid').text = result.identifier

            citation = etree.SubElement(idinfo, 'citation')
            citeinfo = etree.SubElement(citation, 'citeinfo')

            # title
            val = getattr(result, queryables['fgdc:Title']['dbcol'])
            etree.SubElement(citeinfo, 'title').text = val

            # publisher
            publinfo = etree.SubElement(citeinfo, 'publinfo')
            val = getattr(result, queryables['fgdc:Publisher']['dbcol']) or ''
            etree.SubElement(publinfo, 'publish').text = val

            # origin
            val = getattr(result, queryables['fgdc:Origin']['dbcol']) or ''
            etree.SubElement(citeinfo, 'origin').text = val

            # keywords
            val = getattr(result, queryables['fgdc:ThemeKeywords']['dbcol'])
            if val:
                keywords = etree.SubElement(idinfo, 'keywords')
                theme = etree.SubElement(keywords, 'theme')
                for v in val.split(','):
                    etree.SubElement(theme, 'themekey').text = v

            # abstract
            descript = etree.SubElement(idinfo, 'descript')
            val = getattr(result, queryables['fgdc:Abstract']['dbcol']) or ''
            etree.SubElement(descript, 'abstract').text = val

            # contributor
            val = getattr(result, queryables['fgdc:Contributor']['dbcol']) or ''
            etree.SubElement(idinfo, 'datacred').text = val

            # direct
            spdoinfo = etree.SubElement(idinfo, 'spdoinfo')
            val = getattr(result, queryables['fgdc:Type']['dbcol']) or ''
            etree.SubElement(spdoinfo, 'direct').text = val

            # formname
            distinfo = etree.SubElement(node, 'distinfo')
            stdorder = etree.SubElement(distinfo, 'stdorder')
            digform = etree.SubElement(stdorder, 'digform')
            digtinfo = etree.SubElement(digform, 'digtinfo')
            val = getattr(result, queryables['fgdc:Format']['dbcol']) or ''
            etree.SubElement(digtinfo, 'formname').text = val
            etree.SubElement(citeinfo, 'geoform').text = val

            # source
            lineage = etree.SubElement(node, 'lineage')
            srcinfo = etree.SubElement(lineage, 'srcinfo')
            srccite = etree.SubElement(srcinfo, 'srccite')
            sciteinfo = etree.SubElement(srccite, 'citeinfo')
            val = getattr(result, queryables['fgdc:Source']['dbcol']) or ''
            etree.SubElement(sciteinfo, 'title').text = val

            # onlink
            val = getattr(result, queryables['fgdc:Relation']['dbcol']) or ''
            etree.SubElement(citeinfo, 'onlink').text = val

            # bbox extent
            val = getattr(result, queryables['fgdc:Envelope']['dbcol'])
            bboxel = write_extent(val)
            if bboxel is not None:
                node.append(bboxel)

            # metd
            metainfo = etree.SubElement(node, 'metainfo')
            val = getattr(result, queryables['fgdc:Modified']['dbcol']) or ''
            etree.SubElement(metainfo, 'metd').text = val

        return node

def write_extent(bbox):
    ''' Generate BBOX extent '''

    from shapely.wkt import loads

    if bbox is not None:
        bbox2 = loads(bbox).envelope.bounds
        spdom = etree.Element('spdom')
        bounding = etree.SubElement(spdom, 'bounding')
        etree.SubElement(bounding, 'westbc').text = str(bbox2[0])
        etree.SubElement(bounding, 'eastbc').text = str(bbox2[2])
        etree.SubElement(bounding, 'northbc').text = str(bbox2[3])
        etree.SubElement(bounding, 'southbc').text = str(bbox2[1])
        return spdom
    return None
