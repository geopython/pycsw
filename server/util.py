# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2010 Tom Kralidis
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

import time
from lxml import etree
import config
from shapely.wkt import loads

def get_today_and_now():
    ''' Get the date, right now, in ISO8601 '''
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())

def get_time_iso2unix(isotime):
    ''' Convert ISO8601 to UNIX timestamp '''
    return int(time.mktime(time.strptime(
    isotime, '%Y-%m-%dT%H:%M:%SZ'))) - time.timezone

def get_version_integer(version):
    ''' Get an integer of the OGC version value x.y.z '''
    if version is not None:  # split and make integer
        xyz = version.split('.')
        if len(xyz) != 3:
            return -1
        try:
            return int(xyz[0]) * 10000 + int(xyz[1]) * 100 + int(xyz[2])
        except Exception, err:
            raise RuntimeError('%s' % str(err))
    else:  # not a valid version string
        return -1

def find_exml(val, attrib=False):
    ''' Test that the XML value exists, return value, else return None '''
    if val is not None:
        if attrib:  # it's an XML attribute
            return val
        else:  # it's an XML value
            return val.text
    else:
        return None

def nspath_eval(xpath):
    ''' Return an etree friendly xpath '''
    out = []
    for chunks in xpath.split('/'):
        namespace, element = chunks.split(':')
        out.append('{%s}%s' % (config.NAMESPACES[namespace], element))
    return '/'.join(out)

def xmltag_split(tag):
    ''' Return XML element bare tag name (without prefix) '''
    try:
        return tag.split('}')[1]
    except:
        return tag

def xmltag_split2(tag, namespaces, colon=False):
    ''' Return XML namespace prefix of element '''
    try:
        nsuri = tag.split('}')[0].split('{')[1]
        nsprefix = [key for key, value in namespaces.iteritems() \
        if value == nsuri]
        value = nsprefix[0]
        if colon:
            return '%s:' % nsprefix[0]
        else:
            return nsprefix[0]
    except:
        return ''

def bbox2wktpolygon(bbox):
    ''' Return OGC WKT Polygon of a simple bbox string '''
    tmp = bbox.split(',')
    minx = float(tmp[0])
    miny = float(tmp[1])
    maxx = float(tmp[2])
    maxy = float(tmp[3])
    return 'POLYGON((%.2f %.2f, %.2f %.2f, %.2f %.2f, %.2f %.2f, %.2f %.2f))' \
    % (minx, miny, minx, maxy, maxx, maxy, maxx, miny, minx, miny)

def query_spatial(bbox_data_wkt, bbox_input_wkt, predicate, distance):
    ''' perform spatial query '''

    if bbox_data_wkt is None or bbox_input_wkt is None:
        return 'false'

    if predicate in ['beyond', 'dwithin'] and distance == 'false':
        return 'false'

    bbox1 = loads(bbox_data_wkt)
    bbox2 = loads(bbox_input_wkt)

    # map query to Shapely Binary Predicates:
    if predicate == 'bbox':
        result = bbox1.intersects(bbox2)
    elif predicate == 'beyond':
        result = bbox1.distance(bbox2) > float(distance)
    elif predicate == 'contains':
        result = bbox1.contains(bbox2)
    elif predicate == 'crosses':
        result = bbox1.crosses(bbox2)
    elif predicate == 'disjoint':
        result = bbox1.disjoint(bbox2)
    elif predicate == 'dwithin':
        result = bbox1.distance(bbox2) <= float(distance)
    elif predicate == 'equals':
        result = bbox1.equals(bbox2)
    elif predicate == 'intersects':
        result = bbox1.intersects(bbox2)
    elif predicate == 'overlaps':
        if bbox1.intersects(bbox2) and not bbox1.touches(bbox2):
            result = True
        else:
            result = False
    elif predicate == 'touches':
        result = bbox1.touches(bbox2)
    elif predicate == 'within':
        result = bbox1.within(bbox2)
    else:
        raise RuntimeError, ('Invalid spatial query predicate: %s' % predicate)

    if result:
        return 'true'
    else:
        return 'false'

def update_xpath(xml, recprop):
    ''' Update XML document XPath values '''

    if isinstance(xml, unicode):  # not lxml serialized yet
        xml = etree.fromstring(xml)

    recprop = eval(recprop)
    try:
        nodes = xml.xpath(recprop['rp']['xpath'], namespaces=config.NAMESPACES)
        if len(nodes) > 0:  # matches
            for node1 in nodes:
                if node1.text != recprop['value']:  # values differ, update
                    node1.text = recprop['value']
    except Exception, err:
        raise RuntimeError, ('ERROR: %s' % str(err))
    return etree.tostring(xml)

def transform_mappings(queryables, typename, reverse=False):
    ''' transform metadata model mappings '''
    if reverse:  # from csw:Record
        for qbl in queryables.keys():
            if qbl in typename.values():
                tmp = [k for k, v in typename.iteritems() if v == qbl][0]
                val = queryables[tmp]
                queryables[qbl] = {}
                queryables[qbl]['xpath'] = val['xpath']
                queryables[qbl]['dbcol'] = val['dbcol']
    else:  # to csw:Record
        for qbl in queryables.keys():
            if qbl in typename.keys():
                queryables[qbl] = queryables[qbl]

def get_anytext(xml):
    ''' get all element and attribute data from an XML document '''

    if isinstance(xml, unicode) or isinstance(xml, str):  # not serialized yet
        xml = etree.fromstring(xml)
    return '%s %s' % (' '.join([value for value in xml.xpath('//text()')]),
    ' '.join([value for value in xml.xpath('//attribute::*')]))

def exml2json(element, namespaces):
    ''' Convert an lxml object to JSON
        From:
        https://bitbucket.org/smulloni/pesterfish/src/1578db946d74/pesterfish.py
    '''
   
    d=dict(tag='%s%s' % \
    (xmltag_split2(element.tag, namespaces, True), xmltag_split(element.tag)))
    if element.text:
        if element.text.find('\n') == -1:
            d['text']=element.text
    if element.attrib:
        d['attributes']=dict(('%s%s' %(xmltag_split2(k, namespaces, True), \
        xmltag_split(k)),f(v) if hasattr(v,'keys') else v) \
        for k,v in element.attrib.items())
    children=element.getchildren()
    if children:
        d['children']=map(lambda x: exml2json(x, namespaces), children)
    return d
