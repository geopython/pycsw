# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2025 Tom Kralidis
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

import logging

from sqlalchemy import text

from pygeofilter import ast
from pygeofilter.backends.evaluator import handle
from pygeofilter.backends.sqlalchemy import filters
from pygeofilter.backends.sqlalchemy.evaluate import SQLAlchemyFilterEvaluator
from pygeofilter.parsers.fes.util import Element
from pygeofilter.parsers.fes.util import handle as fhandle
from pygeofilter.parsers.fes.v11 import FES11Parser

from pycsw.core.util import bbox2wktpolygon

LOGGER = logging.getLogger(__name__)


class PycswFilterEvaluator(SQLAlchemyFilterEvaluator):
    def __init__(self, field_mapping=None, dbtype='sqlite',
                 undefined_as_null=None):
        super().__init__(field_mapping, undefined_as_null=undefined_as_null)
        self._pycsw_dbtype = dbtype

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

    @handle(ast.Like)
    def ilike(self, node, lhs):
        LOGGER.debug('Overriding ILIKE filter handling')
        LOGGER.debug(f'Term: {node.pattern}')
        if (str(lhs.prop) == 'dataset.anytext' and
                self._pycsw_dbtype.startswith('postgres')):
            if '%' not in node.pattern:
                LOGGER.debug('Kicking into PostgreSQL FTS mode')
                return text(f"plainto_tsquery('english', '{node.pattern}') @@ anytext_tsvector")  # noqa

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
        return FES11Parser().parse(input_)

    @fhandle('BBOX')
    def geometry_bbox(self, node: Element, lhs, rhs, crs=None):
        minx = rhs.geometry['coordinates'][0][0][1]
        miny = rhs.geometry['coordinates'][0][0][0]
        maxx = rhs.geometry['coordinates'][0][2][1]
        maxy = rhs.geometry['coordinates'][0][2][0]

        return ast.BBox(lhs, minx, miny, maxx, maxy, crs)
