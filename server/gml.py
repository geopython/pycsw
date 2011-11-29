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
from owslib import crs

TYPES = ['gml:Point', 'gml:LineString', 'gml:Polygon', 'gml:Envelope']

DEFAULT_SRS = crs.Crs('urn:x-ogc:def:crs:EPSG:6.11:4326')

class Geometry(object):
    ''' base geometry class '''

    def __init__(self, element):
        ''' initialize geometry parser  '''

        self.type = None 
        self.wkt = None
        self.crs = None
        self._exml = element

        ''' return OGC WKT for GML geometry '''
    
        operand = element.xpath(
        '|'.join(TYPES), namespaces={'gml':'http://www.opengis.net/gml'})[0]

        if operand.attrib.has_key('srsName'):
            self.crs = crs.Crs(operand.attrib['srsName'])

        self.type = util.xmltag_split(operand.tag)

        if util.xmltag_split(operand.tag) == 'Point':
            self._get_point()
        elif util.xmltag_split(operand.tag) == 'LineString':
            self._get_linestring()
        elif util.xmltag_split(operand.tag) == 'Polygon':
            self._get_polygon()
        elif util.xmltag_split(operand.tag) == 'Envelope':
            self._get_envelope()

        # reproject data if needed    
        if self.crs and self.crs.code != 4326:
            self.wkt = self.transform(self.crs.code, DEFAULT_SRS.code)
        else:  # no reprojection
            self.crs = DEFAULT_SRS

    def _get_point(self):
        ''' Parse gml:Point '''
    
        tmp = self._exml.find(util.nspath_eval('gml:Point/gml:pos'))
    
        if tmp is None:
            raise RuntimeError, ('Invalid gml:Point geometry.  Missing gml:pos')
        else:
            xypoint = tmp.text.split()
            self.wkt = 'POINT(%s %s)' % (xypoint[0], xypoint[1])
    
    def _get_linestring(self):
        ''' Parse gml:LineString'''
    
        tmp = self._exml.find(util.nspath_eval('gml:LineString/gml:posList'))
    
        if tmp is None:
            raise RuntimeError, \
            ('Invalid gml:LineString geometry.  Missing gml:posList')
        else:
            self.wkt = 'LINESTRING(%s)' % _poslist2wkt(tmp.text)
    
    def _get_polygon(self):
        ''' Parse gml:Polygon'''
    
        tmp = self._exml.find('.//%s' % util.nspath_eval('gml:posList'))
    
        if tmp is None:
            raise RuntimeError, \
            ('Invalid gml:LineString geometry.  Missing gml:posList')
        else:
            self.wkt = 'POLYGON((%s))' % _poslist2wkt(tmp.text)
    
    def _get_envelope(self):
        ''' Parse gml:Envelope '''
    
        tmp = self._exml.find(util.nspath_eval('gml:Envelope/gml:lowerCorner'))
        if tmp is None:
            raise RuntimeError, \
            ('Invalid gml:Envelope geometry.  Missing gml:lowerCorner')
        else:
            lower_left = tmp.text
    
        tmp = self._exml.find(util.nspath_eval('gml:Envelope/gml:upperCorner'))
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
    
        self.wkt = util.bbox2wktpolygon('%s,%s,%s,%s' %
        (xymin[1], xymin[0], xymax[1], xymax[0]))
    
    def _poslist2wkt(poslist):
        ''' Repurpose gml:posList into WKT aware list '''
    
        tmp = poslist.split()
        poslist2 = []
    
        xlist = tmp[1::2]
        ylist = tmp[::2]
    
        for i, j in zip(xlist, ylist):
            poslist2.append('%s %s' % (i, j))

        return ', '.join(poslist2)
    
    def transform(self, src, dest):
        ''' transform coordinates from one CRS to another '''
    
        import pyproj
        from shapely.geometry import Point, LineString, Polygon
        from shapely.wkt import loads
    
        proj_src = pyproj.Proj(init='epsg:%s' % src)
        proj_dst = pyproj.Proj(init='epsg:%s' % dest)
    
        geom = loads(self.wkt)
    
        if geom.type == 'Point':
            newgeom = Point(pyproj.transform(proj_src, proj_dst, geom.x, geom.y))
            wkt2 = newgeom.wkt
    
        elif geom.type == 'LineString':
            vertices = []
            for vertice in list(geom.coords):
                newgeom = pyproj.transform(proj_src, proj_dst, vertice[0], vertice[1])
                vertices.append(newgeom)
    
            linestring = LineString(vertices)
    
            wkt2 = linestring.wkt
    
        elif geom.type == 'Polygon':
            vertices = []
            for vertice in list(geom.exterior.coords):
                newgeom = pyproj.transform(proj_src, proj_dst, vertice[0], vertice[1])
                vertices.append(newgeom)
    
            polygon = Polygon(vertices)
    
            wkt2 = polygon.wkt
    
        return wkt2
