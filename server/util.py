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

from lxml import etree
import config

def get_today_and_now():
    ''' Get the date, right now, in ISO8601 '''
    import time
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())

def get_version_integer(version):
    ''' Get an integer of the OGC version valud x.y.z '''
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
        if attrib == True:  # it's an XML attribute
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
    return tag.split('}')[1]

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

    from shapely.wkt import loads

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

    if result is True:
        return 'true'
    else:
        return 'false'

def query_anytext(xml, searchterm):
    ''' perform fulltext search against XML '''
    exml = etree.fromstring(xml)
    for element in exml.xpath('//text()'):  # all elements
        if element.lower().find(searchterm.lower()) != -1:
            return 'true'
    for att in exml.xpath('//attribute::*'):  # all attributes
        if att.lower().find(searchterm.lower()) != -1:
            return 'true'
    return 'false'

def query_xpath(xml, xpath_in, searchterm, matchcase=0):
    ''' perform search against XPath '''
    exml = etree.fromstring(xml)
    for xpath in exml.xpath(xpath_in, namespaces=config.NAMESPACES):
        if matchcase == 1:
            if xpath.text == searchterm:
                return 'true'
        else:
            if xpath.text.lower() == searchterm.lower():
                return 'true'
    return 'false'
