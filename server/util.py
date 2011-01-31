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

import config

def get_version_integer(version):
    if version is not None:  # split and make integer
        a = version.split('.')
        if len(a) != 3:
            return -1
        try:
            return int(a[0]) * 10000 + int(a[1]) * 100 + int(a[2])
        except:
            return -1
    else:  # not a valid version string
         return -1

def nspath(path, ns='http://www.opengis.net/cat/csw/2.0.2'):

    """

    Prefix the given path with the given namespace identifier.
    
    Parameters
    ----------

    - path: ElementTree API Compatible path expression
    - ns: the XML namespace URI.

    """

    if ns is None or path is None:
        return -1

    components = []
    for component in path.split('/'):
        if component != '*':
            component = '{%s}%s' % (ns, component)
        components.append(component)
    return '/'.join(components)

def nspath_eval(xpath, mappings=config.namespaces):
    out = []
    for s in xpath.split('/'):
        ns, el = s.split(':')
        out.append('{%s}%s' % (mappings[ns],el))
    return '/'.join(out)

def bbox2polygon(bbox):
    # like '-180,-90,180,90'
    minx,miny,maxx,maxy=bbox.split(',')
    poly = []
    poly.append((float(minx),float(miny)))
    poly.append((float(minx),float(maxy)))
    poly.append((float(maxx),float(maxy)))
    poly.append((float(maxx),float(miny)))
    return poly

def point_inside_polygon(x,y,poly):
    # from http://www.ariel.com.au/a/python-point-int-poly.html
    n = len(poly)
    inside=False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside

def bbox_query(bbox_data,bbox_input):
    if bbox_data == 'None':
        return 'false'

    b1 = bbox2polygon(bbox_data)
    b2 = bbox2polygon(bbox_input)

    # check if any points of the dataset bbox are inside the query bbox
    for xy in b1:  # each pair
        if point_inside_polygon(xy[0],xy[1],b2):  # match
            return 'true'
    return 'false'

def anytext_query(xml, searchterm):
    # perform fulltext search against XML
    for el in xml.xpath('//text()'):  # all elements
        if el.lower().find(searchterm.lower()) != -1:
            return 'true'
    for att in xml.xpath('//attribute::*'):  # all attributes
        if att.lower().find(searchterm.lower()) != -1:
            return 'true'
    return 'false'
