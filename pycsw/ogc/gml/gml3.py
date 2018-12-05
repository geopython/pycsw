# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
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

from six.moves import zip
import logging
from owslib import crs

from pycsw.core import util
from pycsw.core.etree import etree

LOGGER = logging.getLogger(__name__)

TYPES = ['gml:Point', 'gml:LineString', 'gml:Polygon', 'gml:Envelope']

DEFAULT_SRS = crs.Crs('urn:x-ogc:def:crs:EPSG:6.11:4326')


def _poslist2wkt(poslist, axisorder):
    """Repurpose gml:posList into WKT aware list"""

    tmp = poslist.split()
    poslist2 = []

    xlist = tmp[1::2]
    ylist = tmp[::2]

    if axisorder == 'yx':
        for i, j in zip(ylist, xlist):
            poslist2.append('%s %s' % (i, j))
    else:
        for i, j in zip(xlist, ylist):
            poslist2.append('%s %s' % (i, j))

    return ', '.join(poslist2)


class Geometry(object):
    """base geometry class"""

    def __init__(self, element, nsmap):
        """initialize geometry parser"""

        self.nsmap = nsmap
        self.type = None
        self.wkt = None
        self.crs = None
        self._exml = element

        # return OGC WKT for GML geometry

        operand = element.xpath(
            '|'.join(TYPES),
            namespaces={'gml': 'http://www.opengis.net/gml'})[0]

        if 'srsName' in operand.attrib:
            LOGGER.debug('geometry srsName detected')
            self.crs = crs.Crs(operand.attrib['srsName'])
        else:
            LOGGER.debug('setting default geometry srsName %s', DEFAULT_SRS)
            self.crs = DEFAULT_SRS

        self.type = etree.QName(operand).localname

        if self.type == 'Point':
            self._get_point()
        elif self.type == 'LineString':
            self._get_linestring()
        elif self.type == 'Polygon':
            self._get_polygon()
        elif self.type == 'Envelope':
            self._get_envelope()
        else:
            raise RuntimeError('Unsupported geometry type (Must be one of %s)'
                               % ','.join(TYPES))

        # reproject data if needed
        if self.crs is not None and self.crs.code not in [4326, 'CRS84']:
            LOGGER.info('transforming geometry to 4326')
            try:
                self.wkt = self.transform(self.crs.code, DEFAULT_SRS.code)
            except Exception as err:
                LOGGER.exception('Coordinate transformation error')
                raise RuntimeError('Reprojection error: Invalid srsName')

    def _get_point(self):
        """Parse gml:Point"""

        tmp = self._exml.find(util.nspath_eval('gml:Point/gml:pos',
                                               self.nsmap))

        if tmp is None:
            raise RuntimeError('Invalid gml:Point geometry.  Missing gml:pos')
        else:
            xypoint = tmp.text.split()
            if self.crs.axisorder == 'yx':
                self.wkt = 'POINT(%s %s)' % (xypoint[1], xypoint[0])
            else:
                self.wkt = 'POINT(%s %s)' % (xypoint[0], xypoint[1])

    def _get_linestring(self):
        """Parse gml:LineString"""

        tmp = self._exml.find(util.nspath_eval('gml:LineString/gml:posList',
                                               self.nsmap))

        if tmp is None:
            raise RuntimeError('Invalid gml:LineString geometry.\
                               Missing gml:posList')
        else:
            self.wkt = 'LINESTRING(%s)' % _poslist2wkt(tmp.text,
                                                       self.crs.axisorder)

    def _get_polygon(self):
        """Parse gml:Polygon"""

        tmp = self._exml.find('.//%s' % util.nspath_eval('gml:posList',
                                                         self.nsmap))

        if tmp is None:
            raise RuntimeError('Invalid gml:LineString geometry.\
                               Missing gml:posList')
        else:
            self.wkt = 'POLYGON((%s))' % _poslist2wkt(tmp.text,
                                                      self.crs.axisorder)

    def _get_envelope(self):
        """Parse gml:Envelope"""

        tmp = self._exml.find(util.nspath_eval('gml:Envelope/gml:lowerCorner',
                                               self.nsmap))
        if tmp is None:
            raise RuntimeError('Invalid gml:Envelope geometry.\
                               Missing gml:lowerCorner')
        else:
            lower_left = tmp.text

        tmp = self._exml.find(util.nspath_eval('gml:Envelope/gml:upperCorner',
                                               self.nsmap))
        if tmp is None:
            raise RuntimeError('Invalid gml:Envelope geometry.\
                               Missing gml:upperCorner')
        else:
            upper_right = tmp.text

        llmin = lower_left.split()
        urmax = upper_right.split()

        if len(llmin) < 2 or len(urmax) < 2:
            raise RuntimeError('Invalid gml:Envelope geometry. \
            gml:lowerCorner and gml:upperCorner must hold at least x and y')

        if self.crs.axisorder == 'yx':
            self.wkt = util.bbox2wktpolygon('%s,%s,%s,%s' % (llmin[1],
                                            llmin[0], urmax[1], urmax[0]))
        else:
            self.wkt = util.bbox2wktpolygon('%s,%s,%s,%s' % (llmin[0],
                                            llmin[1], urmax[0], urmax[1]))

    def transform(self, src, dest):
        """transform coordinates from one CRS to another"""

        import pyproj
        from shapely.geometry import Point, LineString, Polygon
        from shapely.wkt import loads

        LOGGER.info('Transforming geometry from %s to %s', src, dest)

        vertices = []

        try:
            proj_src = pyproj.Proj(init='epsg:%s' % src)
        except:
            raise RuntimeError('Invalid source projection')

        try:
            proj_dst = pyproj.Proj(init='epsg:%s' % dest)
        except:
            raise RuntimeError('Invalid destination projection')

        geom = loads(self.wkt)

        if geom.type == 'Point':
            newgeom = Point(pyproj.transform(proj_src, proj_dst,
                            geom.x, geom.y))
            wkt2 = newgeom.wkt

        elif geom.type == 'LineString':
            for vertice in list(geom.coords):
                newgeom = pyproj.transform(proj_src, proj_dst,
                                           vertice[0], vertice[1])
                vertices.append(newgeom)

            linestring = LineString(vertices)

            wkt2 = linestring.wkt

        elif geom.type == 'Polygon':
            for vertice in list(geom.exterior.coords):
                newgeom = pyproj.transform(proj_src, proj_dst,
                                           vertice[0], vertice[1])
                vertices.append(newgeom)

            polygon = Polygon(vertices)

            wkt2 = polygon.wkt

        return wkt2
