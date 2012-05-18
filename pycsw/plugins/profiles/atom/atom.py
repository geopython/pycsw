# -*- coding: iso-8859-15 -*-
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
from pycsw import config, util
from pycsw.plugins.profiles import profile

class ATOM(profile.Profile):
    ''' Atom class '''
    def __init__(self, model, namespaces, context):

        self.context = context

        self.namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'georss': 'http://www.georss.org/georss'
        }

        self.repository = {
            'atom:entry': {
                'outputschema': 'http://www.w3.org/2005/Atom',
                'queryables': {
                    'SupportedAtomQueryables': {
                        'atom:id': {'xpath': 'atom:id', 'dbcol': self.context.md_core_model['mappings']['pycsw:Identifier']},
                        'atom:title': {'xpath': 'atom:title', 'dbcol': self.context.md_core_model['mappings']['pycsw:Title']},
                        'atom:author': {'xpath': 'atom:author', 'dbcol': self.context.md_core_model['mappings']['pycsw:Creator']},
                        'atom:category': {'xpath': 'atom:category', 'dbcol': self.context.md_core_model['mappings']['pycsw:Keywords']},
                        'atom:contributor': {'xpath': 'atom:contributor', 'dbcol': self.context.md_core_model['mappings']['pycsw:Contributor']},
                        'atom:rights': {'xpath': 'atom:rights', 'dbcol': self.context.md_core_model['mappings']['pycsw:AccessConstraints']},
                        'atom:source': {'xpath': 'atom:source', 'dbcol': self.context.md_core_model['mappings']['pycsw:Source']},
                        'atom:summary': {'xpath': 'atom:summary', 'dbcol': self.context.md_core_model['mappings']['pycsw:Abstract']},
                        'atom:updated': {'xpath': 'atom:updated', 'dbcol': self.context.md_core_model['mappings']['pycsw:Modified']},
                        'atom:published': {'xpath': 'atom:published', 'dbcol': self.context.md_core_model['mappings']['pycsw:PublicationDate']},
                        'atom:AnyText': {'xpath': 'atom:AnyText', 'dbcol': self.context.md_core_model['mappings']['pycsw:AnyText']},
                        'georss:where': {'xpath': 'georss:where', 'dbcol': self.context.md_core_model['mappings']['pycsw:BoundingBox']}
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

        profile.Profile.__init__(self,
            name='atom',
            version='1.0',
            title='Atom Syndication Format',
            url='http://tools.ietf.org/html/rfc4287',
            namespace=self.namespaces['atom'],
            typename='atom:entry',
            outputschema=self.namespaces['atom'],
            prefixes=['atom'],
            model=model,
            core_namespaces=namespaces,
            added_namespaces=self.namespaces,
            repository=self.repository['atom:entry'])

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
        util.nspath_eval('csw:SchemaComponent', self.context.namespaces),
        schemaLanguage='XMLSCHEMA', targetNamespace=self.namespace)

        schema = etree.parse(os.path.join(self.context.pycsw_home,
                 'plugins', 'profiles', 'atom',
                 'schemas', 'atom', 'atom.xsd')).getroot()
        node.append(schema)

        return [node]

    def check_getdomain(self, kvp):
        '''Perform extra profile specific checks in the GetDomain request'''
        return None

    def write_record(self, result, esn, outputschema, queryables):
        ''' Return csw:SearchResults child as lxml.etree.Element '''

        typename = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Typename'])

        if esn == 'full' and typename == 'atom:entry':
            # dump record as is and exit
            return etree.fromstring(util.getqattr(result, self.context.md_core_model['mappings']['pycsw:XML']))

        if typename == 'csw:Record':  # transform csw:Record -> atom:entry model mappings
            util.transform_mappings(queryables, self.repository['mappings']['csw:Record'])

        node = etree.Element(util.nspath_eval('atom:entry', self.namespaces))
        node.attrib[util.nspath_eval('xsi:schemaLocation', self.context.namespaces)] = \
        '%s %s?service=CSW&version=2.0.2&request=DescribeRecord&typename=atom:entry' % (self.namespaces['atom'], self.url)

        # author
        val = util.getqattr(result, queryables['atom:author']['dbcol'])
         
        if val:
            etree.SubElement(node, util.nspath_eval('atom:author', self.namespaces)).text = util.getqattr(result, queryables['atom:author']['dbcol'])

        # category
        val = util.getqattr(result, queryables['atom:category']['dbcol'])

        if val:
            for kw in val.split(','):
                etree.SubElement(node, util.nspath_eval('atom:category', self.namespaces)).text = kw


        for qval in ['contributor', 'id']:
            val = util.getqattr(result, queryables['atom:%s' % qval]['dbcol'])
            if val:
                etree.SubElement(node, util.nspath_eval('atom:%s' % qval, self.namespaces)).text = util.getqattr(result, queryables['atom:%s' % qval]['dbcol'])

        rlinks = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Links'])
        if rlinks:
            for link in rlinks.split('^'):
                linkset = link.split(',')
           
                url2 = etree.SubElement(node, util.nspath_eval('atom:link', self.namespaces), href=linkset[-1], type=linkset[2], title=linkset[1])

        etree.SubElement(node, util.nspath_eval('atom:link', self.namespaces), href='%s?service=CSW&version=2.0.2&request=GetRepositoryItem&id=%s' % (self.url, util.getqattr(result, queryables['atom:id']['dbcol'])))

        for qval in ['published', 'rights', 'source', 'summary', 'title', 'updated']:
            val = util.getqattr(result, queryables['atom:%s' % qval]['dbcol'])
            if val:
                etree.SubElement(node, util.nspath_eval('atom:%s' % qval, self.namespaces)).text = util.getqattr(result, queryables['atom:%s' % qval]['dbcol'])

        # bbox extent
        val = util.getqattr(result, queryables['georss:where']['dbcol'])
        bboxel = write_extent(val, self.context.namespaces)
        if bboxel is not None:
            node.append(bboxel)

        return node

def write_extent(bbox, nsmap):
    ''' Generate BBOX extent '''

    from shapely.wkt import loads

    if bbox is not None:
        if bbox.find('SRID') != -1:  # it's EWKT; chop off 'SRID=\d+;'
            bbox2 = loads(bbox.split(';')[-1])
        else:
            bbox2 = loads(bbox)
        where = etree.Element(util.nspath_eval('georss:where', nsmap))
        polygon = etree.SubElement(where, util.nspath_eval('gml:Polygon', nsmap), srsName='urn:x-ogc:def:crs:EPSG:6.11:4326')
        exterior = etree.SubElement(polygon, util.nspath_eval('gml:exterior', nsmap))
        lring = etree.SubElement(exterior, util.nspath_eval('gml:LinearRing', nsmap))
        poslist = etree.SubElement(lring, util.nspath_eval('gml:posList', nsmap)).text = \
        ' '.join(['%s %s' % (str(i[1]), str(i[0])) for i in list(bbox2.exterior.coords)])

        return where
    return None
