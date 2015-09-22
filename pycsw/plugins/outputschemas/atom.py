# -*- coding: iso-8859-15 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
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
from pycsw import util

NAMESPACE = 'http://www.w3.org/2005/Atom'
NAMESPACES = {'atom': NAMESPACE, 'georss': 'http://www.georss.org/georss'}

XPATH_MAPPINGS = {
    'pycsw:Identifier': 'atom:id',
    'pycsw:Title': 'atom:title',
    'pycsw:Creator': 'atom:author',
    'pycsw:Abstract': 'atom:summary',
    'pycsw:PublicationDate': 'atom:published',
    'pycsw:Keywords': 'atom:category',
    'pycsw:Contributor': 'atom:contributor',
    'pycsw:AccessConstraints': 'atom:rights',
    'pycsw:Modified': 'atom:updated',
    'pycsw:Source': 'atom:source',
}

def write_record(result, esn, context, url=None):
    ''' Return csw:SearchResults child as lxml.etree.Element '''

    typename = util.getqattr(result, context.md_core_model['mappings']['pycsw:Typename'])

    if esn == 'full' and typename == 'atom:entry':
        # dump record as is and exit
        return etree.fromstring(util.getqattr(result, context.md_core_model['mappings']['pycsw:XML']), context.parser)

    node = etree.Element(util.nspath_eval('atom:entry', NAMESPACES), nsmap=NAMESPACES)
    node.attrib[util.nspath_eval('xsi:schemaLocation', context.namespaces)] = \
            '%s http://www.kbcafe.com/rss/atom.xsd.xml' % NAMESPACES['atom']

    # author
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Creator'])
     
    if val:
        etree.SubElement(node, util.nspath_eval('atom:author', NAMESPACES)).text = val

    # category
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Keywords'])

    if val:
        for kw in val.split(','):
            etree.SubElement(node, util.nspath_eval('atom:category', NAMESPACES)).text = kw


    for qval in ['pycsw:Contributor', 'pycsw:Identifier']:
        val = util.getqattr(result, context.md_core_model['mappings'][qval])
        if val:
            etree.SubElement(node, util.nspath_eval(XPATH_MAPPINGS[qval], NAMESPACES)).text = val

    rlinks = util.getqattr(result, context.md_core_model['mappings']['pycsw:Links'])
    if rlinks:
        for link in rlinks.split('^'):
            linkset = link.split(',')
       
            url2 = etree.SubElement(node, util.nspath_eval('atom:link', NAMESPACES), href=linkset[-1], type=linkset[2], title=linkset[1])

    etree.SubElement(node, util.nspath_eval('atom:link', NAMESPACES), href='%s?service=CSW&version=2.0.2&request=GetRepositoryItem&id=%s' % (url, util.getqattr(result, context.md_core_model['mappings']['pycsw:Identifier'])))

    for qval in ['pycsw:PublicationDate', 'pycsw:AccessConstraints', 'pycsw:Source', 'pycsw:Abstract', 'pycsw:Title', 'pycsw:Modified']:
        val = util.getqattr(result, context.md_core_model['mappings'][qval])
        if val:
            etree.SubElement(node, util.nspath_eval(XPATH_MAPPINGS[qval], NAMESPACES)).text = val

    # bbox extent
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:BoundingBox'])
    bboxel = write_extent(val, context.namespaces)
    if bboxel is not None:
        node.append(bboxel)

    return node

def write_extent(bbox, nsmap):
    ''' Generate BBOX extent '''
    
    if bbox is not None:
        try:
            bbox2 = util.wkt2geom(bbox, bounds=False)
        except:
            return None

        where = etree.Element(util.nspath_eval('georss:where', NAMESPACES))
        polygon = etree.SubElement(where, util.nspath_eval('gml:Polygon', nsmap), srsName='urn:x-ogc:def:crs:EPSG:6.11:4326')
        exterior = etree.SubElement(polygon, util.nspath_eval('gml:exterior', nsmap))
        lring = etree.SubElement(exterior, util.nspath_eval('gml:LinearRing', nsmap))
        poslist = etree.SubElement(lring, util.nspath_eval('gml:posList', nsmap)).text = \
        ' '.join(['%s %s' % (str(i[1]), str(i[0])) for i in list(bbox2.exterior.coords)])
    
        return where
    return None
