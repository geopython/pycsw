# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2026 Tom Kralidis
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

from copy import deepcopy
import logging

from owslib import crs as owslib_crs
from shapely import box
from shapely.geometry import shape
from sqlalchemy import text

from pygeofilter import ast
from pygeofilter.values import Envelope
from pygeofilter.backends.evaluator import handle
from pygeofilter.backends.sqlalchemy import filters
from pygeofilter.backends.sqlalchemy.evaluate import SQLAlchemyFilterEvaluator
from pygeofilter.parsers.fes.util import Element
from pygeofilter.parsers.fes.util import handle as fhandle
from pygeofilter.parsers.fes.v11 import FES11Parser

from pycsw.core.etree import etree
from pycsw.core.util import bbox2wktpolygon
from pycsw.ogc.gml.gml3 import DEFAULT_SRS

LOGGER = logging.getLogger(__name__)

GML_NAMESPACES = ('http://www.opengis.net/gml', 'http://www.opengis.net/gml/3.2')
# GML elements holding coordinates as whitespace-separated numbers
GML_COORDINATE_LISTS = ('pos', 'posList', 'lowerCorner', 'upperCorner')
# longitude/latitude, in the form pygml recognises (it swaps latitude-first
# polygons, lines and points itself, so the swapped geometry must say xy)
LONGITUDE_FIRST = 'urn:ogc:def:crs:OGC::CRS84'


def _gml_name(element):
    """Local name of a GML element, else None"""

    if element is None or not isinstance(element.tag, str):
        return None
    qname = etree.QName(element)
    return qname.localname if qname.namespace in GML_NAMESPACES else None


def _axis_order(srs_name):
    """Axis order ('xy' or 'yx') of a GML srsName, as gml3.Geometry reads it"""

    if not srs_name:
        return DEFAULT_SRS.axisorder
    try:
        return owslib_crs.Crs(srs_name).axisorder
    except Exception:
        LOGGER.debug(f'Unknown srsName {srs_name}: using the default axis order')
        return DEFAULT_SRS.axisorder


def _swap_xy(values, dimension):
    """Swap the first two values of each `dimension`-tuple"""

    for i in range(0, len(values) - 1, dimension):
        values[i], values[i + 1] = values[i + 1], values[i]
    return values


def gml_to_xy(filter_):
    """
    Return a copy of an OGC Filter whose GML geometries are all in x/y
    (longitude, latitude) order.

    pygeofilter takes GML coordinates as written, whatever the axis order of
    their CRS, while gml3.Geometry (used for database repositories) reads
    them in that order: latitude first for EPSG:4326, which is also the
    default when srsName is missing. Without this, a repository without a
    database searched a swapped box for such filters (e.g. from QGIS
    MetaSearch, which sends urn:ogc:def:crs:EPSG::4326).
    """

    if isinstance(filter_, (str, bytes)):
        root = etree.fromstring(filter_)
    else:
        root = deepcopy(filter_)

    for geometry in list(root.iter()):
        # the outermost GML element of each spatial operand
        if _gml_name(geometry) is None or _gml_name(geometry.getparent()) is not None:
            continue
        if _axis_order(geometry.get('srsName')) != 'yx':
            continue

        dimension = int(geometry.get('srsDimension', 2))
        for node in geometry.iter():
            name = _gml_name(node)
            if name in GML_COORDINATE_LISTS and node.text:
                node_dimension = int(node.get('srsDimension', dimension))
                node.text = ' '.join(_swap_xy(node.text.split(), node_dimension))
            elif name == 'coordinates' and node.text:  # GML 2: "y,x y,x"
                cs, ts = node.get('cs', ','), node.get('ts', ' ')
                node.text = ts.join(cs.join(_swap_xy(t.split(cs), len(t.split(cs))))
                                    for t in node.text.split(ts) if t)
            elif name == 'coord':  # GML 2: <gml:X/><gml:Y/>
                x = next((c for c in node if _gml_name(c) == 'X'), None)
                y = next((c for c in node if _gml_name(c) == 'Y'), None)
                if x is not None and y is not None:
                    x.text, y.text = y.text, x.text

        LOGGER.debug(f"Swapping axes of gml:{_gml_name(geometry)} in {geometry.get('srsName')}")
        geometry.set('srsName', LONGITUDE_FIRST)

    return root


class PycswFilterEvaluator(SQLAlchemyFilterEvaluator):
    def __init__(self, field_mapping=None, dbtype='sqlite',
                 undefined_as_null=None):
        super().__init__(field_mapping, undefined_as_null=undefined_as_null)
        self._pycsw_dbtype = dbtype

    @handle(ast.GeometryIntersects)
    def intersects(self, node, lhs, rhs):
        LOGGER.debug('Overriding INTERSECT filter handling')
        geometry = self.field_mapping['bbox'].key
        try:
            crs = node.crs
        except AttributeError:
            crs = 4326

        if isinstance(node.rhs, Envelope):
            wkt = box(node.rhs.x1, node.rhs.x2,
                      node.rhs.y1, node.rhs.y2, ccw=False).wkt
        else:
            wkt = shape(node.rhs.geometry).wkt

        if self._pycsw_dbtype == 'postgresql+postgis+native':
            return text(f"ST_Intersects({geometry}, 'SRID={crs};{wkt}')")
        else:
            return text(f"query_spatial({geometry}, '{wkt}', 'intersects', 'false') = 'true'")  # noqa

    @handle(ast.BBox)
    def bbox(self, node, lhs):
        LOGGER.debug('Overriding BBOX filter handling')
        geometry = self.field_mapping['bbox'].key
        crs = node.crs or 4326

        bbox_string = f'{node.minx},{node.miny},{node.maxx},{node.maxy}'
        wkt = bbox2wktpolygon(bbox_string)

        if self._pycsw_dbtype == 'postgresql+postgis+native':
            return text(f"ST_Intersects({geometry}, 'SRID={crs};{wkt}')")
        else:
            return text(f"query_spatial({geometry}, '{wkt}', 'bbox', 'false') = 'true'")  # noqa

    @handle(ast.Equal)
    def equal(self, node, lhs, rhs):
        list_props = [
            'dataset.keywords',
            'dataset.instrument'
        ]

        if str(lhs.prop) in list_props:
            LOGGER.debug(f'Overriding {lhs.prop} "=" with "ilike"')
            node.pattern = f'%{rhs}%'
            node.nocase = False
            node.not_ = False

            return self.ilike(node, lhs)

        return filters.runop(lhs, rhs, '=')

    @handle(ast.Like)
    def ilike(self, node, lhs):
        LOGGER.debug('Overriding ILIKE filter handling')
        LOGGER.debug(f'Term: {node.pattern}')
        print("DBTYPE", self._pycsw_dbtype)
        if (str(lhs.prop) == 'dataset.anytext' and
                self._pycsw_dbtype.startswith('postgres')):
            if '%' not in node.pattern:
                LOGGER.debug('Kicking into PostgreSQL FTS mode')
                return text("plainto_tsquery('english', :node_pattern') @@ anytext_tsvector").bindparams(node_pattern=node.pattern)  # noqa

        LOGGER.debug('Default ILIKE behaviour')
        return filters.like(
            lhs,
            node.pattern,
            not node.nocase,
            node.not_
        )


def to_filter(ast, dbtype, field_mapping=None):
    return PycswFilterEvaluator(field_mapping, dbtype).evaluate(ast)


class PycswCSWFES11Parser(FES11Parser):
    def parse(self, input_):
        # GML coordinates in the axis order of their CRS, as for database
        # repositories (see gml_to_xy)
        return FES11Parser().parse(gml_to_xy(input_))

#    @fhandle('BBOX')
#    def geometry_bbox(self, node: Element, lhs, rhs, crs=None):
#        minx = rhs.geometry['coordinates'][0][0][1]
#        miny = rhs.geometry['coordinates'][0][0][0]
#        maxx = rhs.geometry['coordinates'][0][2][1]
#        maxy = rhs.geometry['coordinates'][0][2][0]

#        return ast.BBox(lhs, minx, miny, maxx, maxy, crs)
