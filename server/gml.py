# -*- coding: ISO-8859-15 -*-
''' GML support'''
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

import util

def get_geometry(geom, geomtypes):
    ''' return OGC WKT for GML geometry '''

    operand = geom.xpath(
    '|'.join(geomtypes), namespaces={'gml':'http://www.opengis.net/gml'})

    if util.xmltag_split(operand[0].tag) == 'Point':
        return _get_point(geom)
    elif util.xmltag_split(operand[0].tag) == 'LineString':
        return _get_linestring(geom)
    elif util.xmltag_split(operand[0].tag) == 'Polygon':
        return _get_polygon(geom)
    elif util.xmltag_split(operand[0].tag) == 'Envelope':
        return _get_envelope(geom)

def _get_point(geom):
    ''' Parse gml:Point '''

    tmp = geom.find(util.nspath_eval('gml:Point/gml:pos'))

    if tmp is None:
        raise RuntimeError, ('Invalid gml:Point geometry.  Missing gml:pos')
    else:
        xypoint = tmp.text.split(' ')
        return 'POINT(%s %s)' % (xypoint[0], xypoint[1])

def _get_linestring(geom):
    ''' Parse gml:LineString'''

    tmp = geom.find(util.nspath_eval('gml:LineString/gml:posList'))

    if tmp is None:
        raise RuntimeError, \
        ('Invalid gml:LineString geometry.  Missing gml:posList')
    else:
        return 'LINESTRING(%s)' % _poslist2wkt(tmp.text)

def _get_polygon(geom):
    ''' Parse gml:Polygon'''

    tmp = geom.find('.//%s' % util.nspath_eval('gml:posList'))

    if tmp is None:
        raise RuntimeError, \
        ('Invalid gml:LineString geometry.  Missing gml:posList')
    else:
        return 'POLYGON((%s))' % _poslist2wkt(tmp.text)

def _get_envelope(geom):
    ''' Parse gml:Envelope '''

    tmp = geom.find(util.nspath_eval('gml:Envelope/gml:lowerCorner'))
    if tmp is None:
        raise RuntimeError, \
        ('Invalid gml:Envelope geometry.  Missing gml:lowerCorner')
    else:
        lower_left = tmp.text

    tmp = geom.find(util.nspath_eval('gml:Envelope/gml:upperCorner'))
    if tmp is None:
        raise RuntimeError, \
        ('Invalid gml:Envelope geometry.  Missing gml:upperCorner')
    else:
        upper_right = tmp.text

    xymin = lower_left.split()
    xymax = upper_right.split()

    if len(xymin) != 2 or len(xymax) != 2:
        raise RuntimeError, \
       ('Invalid gml:Envelope geometry. \
       gml:lowerCorner and gml:upperCorner must hold both lat and long.')

    return util.bbox2wktpolygon('%s,%s,%s,%s' %
    (xymin[1], xymin[0], xymax[1], xymax[0]))

def _poslist2wkt(poslist):
    ''' Repurpose gml:posList into WKT aware list '''

    tmp = poslist.split(' ')
    poslist2 = []

    xlist = tmp[1::2]
    ylist = tmp[::2]

    for i, j in zip(xlist, ylist):
        poslist2.append('%s %s' % (i, j))

    return ', '.join(poslist2)
