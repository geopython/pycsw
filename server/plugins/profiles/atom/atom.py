# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2012 Tom Kralidis
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
    'atom': 'http://www.w3.org/2005/Atom',
    'georss': 'http://www.georss.org/georss'
}

REPOSITORY = {
    'atom:entry': {
        'outputschema': 'http://www.w3.org/2005/Atom',
        'queryables': {
            'SupportedAtomQueryables': {
                'atom:id': {'xpath': 'atom:id', 'dbcol': config.MD_CORE_MODEL['mappings']['pycsw:Identifier']},
                'atom:title': {'xpath': 'atom:title', 'dbcol': config.MD_CORE_MODEL['mappings']['pycsw:Title']},
                'atom:author': {'xpath': 'atom:author', 'dbcol': config.MD_CORE_MODEL['mappings']['pycsw:Creator']},
                'atom:category': {'xpath': 'atom:category', 'dbcol': config.MD_CORE_MODEL['mappings']['pycsw:Keywords']},
                'atom:contributor': {'xpath': 'atom:contributor', 'dbcol': config.MD_CORE_MODEL['mappings']['pycsw:Contributor']},
                'atom:rights': {'xpath': 'atom:rights', 'dbcol': config.MD_CORE_MODEL['mappings']['pycsw:AccessConstraints']},
                'atom:source': {'xpath': 'atom:source', 'dbcol': config.MD_CORE_MODEL['mappings']['pycsw:Source']},
                'atom:summary': {'xpath': 'atom:summary', 'dbcol': config.MD_CORE_MODEL['mappings']['pycsw:Abstract']},
                'atom:updated': {'xpath': 'atom:updated', 'dbcol': config.MD_CORE_MODEL['mappings']['pycsw:Modified']},
                'atom:published': {'xpath': 'atom:published', 'dbcol': config.MD_CORE_MODEL['mappings']['pycsw:PublicationDate']},
                'atom:AnyText': {'xpath': 'atom:AnyText', 'dbcol': config.MD_CORE_MODEL['mappings']['pycsw:AnyText']},
                'georss:where': {'xpath': 'georss:where', 'dbcol': config.MD_CORE_MODEL['mappings']['pycsw:BoundingBox']}
            }
        },
        'mappings': {
            'csw:Record': {
                # map Atom queryables to DC queryables
                'atom:id': 'dc:identifier',
                'atom:title': 'dc:title',
                'atom:author': 'dc:creator',
                'atom:category': 'dc:subject',
                'atom:contributor': 'dc:contributor',
                'atom:rights': 'dc:rights',
                'atom:source': 'dc:source',
                'atom:summary': 'dct:abstract',
                'atom:updated': 'dct:modified',
                'atom:AnyText': 'csw:AnyText',
                'georss:where': 'ows:BoundingBox'
            }
        }
    }
}

class ATOM(profile.Profile):
    ''' Atom class '''
    def __init__(self, model, namespaces):
        profile.Profile.__init__(self,
            name='atom',
            version='1.0',
            title='Atom Syndication Format',
            url='http://tools.ietf.org/html/rfc4287',
            namespace=NAMESPACES['atom'],
            typename='atom:entry',
            outputschema=NAMESPACES['atom'],
            prefixes=['atom'],
            model=model,
            core_namespaces=namespaces,
            added_namespaces=NAMESPACES,
            repository=REPOSITORY['atom:entry'])

    def extend_core(self, model, namespaces, config):
        ''' Extend core configuration '''
        self.url = config.get('server', 'url') 

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
        schemaLanguage='XMLSCHEMA', targetNamespace=self.namespace)

        schema = etree.parse(os.path.join(
                'server', 'plugins', 'profiles', 'atom',
                'etc', 'schemas', 'atom', 'atom.xsd')).getroot()
        node.append(schema)

        return [node]

    def check_getdomain(self, kvp):
        '''Perform extra profile specific checks in the GetDomain request'''
        return None

    def write_record(self, result, esn, outputschema, queryables):
        ''' Return csw:SearchResults child as lxml.etree.Element '''

        typename = util.getqattr(result, config.MD_CORE_MODEL['mappings']['pycsw:Typename'])

        if esn == 'full' and typename == 'atom:entry':
            # dump record as is and exit
            return etree.fromstring(util.getqattr(result, config.MD_CORE_MODEL['mappings']['pycsw:XML']))

        if typename == 'csw:Record':  # transform csw:Record -> atom:entry model mappings
            util.transform_mappings(queryables, REPOSITORY['atom:entry']['mappings']['csw:Record'])

        node = etree.Element(util.nspath_eval('atom:entry'))
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s?service=CSW&version=2.0.2&request=DescribeRecord&typename=atom:entry' % (NAMESPACES['atom'], self.url)

        # author
        val = util.getqattr(result, queryables['atom:author']['dbcol'])
         
        if val:
            etree.SubElement(node, util.nspath_eval('atom:author')).text = util.getqattr(result, queryables['atom:author']['dbcol'])

        # category
        val = util.getqattr(result, queryables['atom:category']['dbcol'])

        if val:
            for kw in val.split(','):
                etree.SubElement(node, util.nspath_eval('atom:category')).text = kw


        for qval in ['contributor', 'id']:
            val = util.getqattr(result, queryables['atom:%s' % qval]['dbcol'])
            if val:
                etree.SubElement(node, util.nspath_eval('atom:%s' % qval)).text = util.getqattr(result, queryables['atom:%s' % qval]['dbcol'])

        rlinks = util.getqattr(result, config.MD_CORE_MODEL['mappings']['pycsw:Links'])
        if rlinks:
            for link in rlinks.split('^'):
                linkset = link.split(',')
           
                url2 = etree.SubElement(node, util.nspath_eval('atom:link'), href=linkset[-1], type=linkset[2], title=linkset[1])

        etree.SubElement(node, util.nspath_eval('atom:link'), href='%s?service=CSW&version=2.0.2&request=GetRepositoryItem&id=%s' % (self.url, util.getqattr(result, queryables['atom:id']['dbcol'])))

        for qval in ['published', 'rights', 'source', 'summary', 'title', 'updated']:
            val = util.getqattr(result, queryables['atom:%s' % qval]['dbcol'])
            if val:
                etree.SubElement(node, util.nspath_eval('atom:%s' % qval)).text = util.getqattr(result, queryables['atom:%s' % qval]['dbcol'])

        # bbox extent
        val = util.getqattr(result, queryables['georss:where']['dbcol'])
        bboxel = write_extent(val)
        if bboxel is not None:
            node.append(bboxel)

        return node

def write_extent(bbox):
    ''' Generate BBOX extent '''

    from shapely.wkt import loads

    if bbox is not None:
        if bbox.find('SRID') != -1:  # it's EWKT; chop off 'SRID=\d+;'
            bbox2 = loads(bbox.split(';')[-1])
        else:
            bbox2 = loads(bbox)
        where = etree.Element(util.nspath_eval('georss:where'))
        polygon = etree.SubElement(where, util.nspath_eval('gml:Polygon'), srsName='urn:x-ogc:def:crs:EPSG:6.11:4326')
        exterior = etree.SubElement(polygon, util.nspath_eval('gml:exterior'))
        lring = etree.SubElement(exterior, util.nspath_eval('gml:LinearRing'))
        poslist = etree.SubElement(lring, util.nspath_eval('gml:posList')).text = \
        ' '.join(['%s %s' % (str(i[1]), str(i[0])) for i in list(bbox2.exterior.coords)])

        return where
    return None
