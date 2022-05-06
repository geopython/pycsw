# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2021 Tom Kralidis
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

from sqlalchemy import text

from pygeofilter import ast
from pygeofilter.backends.evaluator import handle
from pygeofilter.backends.sqlalchemy import filters
from pygeofilter.backends.sqlalchemy.evaluate import SQLAlchemyFilterEvaluator

from pycsw.core.util import bbox2wktpolygon


class PycswFilterEvaluator(SQLAlchemyFilterEvaluator):
    def __init__(self, field_mapping=None, dbtype='sqlite'):
        super().__init__(field_mapping)
        self._pycsw_dbtype = dbtype

    @handle(ast.BBox)
    def bbox(self, node, lhs):
        geometry = self.field_mapping['bbox'].key
        crs = node.crs or 4326

        bbox_string = f'{node.minx},{node.miny},{node.maxx},{node.maxy}'
        wkt = bbox2wktpolygon(bbox_string)

        if self._pycsw_dbtype == 'postgresql+postgis+native':
            return text(f"ST_Intersects({geometry}, 'SRID={crs};{wkt}')")
        else:
            return text(f"query_spatial({geometry}, '{wkt}', 'bbox', 'false') = 'true'")  # noqa

    @handle(ast.Like)
    def like(self, node, lhs):
        return filters.like(
            lhs,
            node.pattern,
            node.nocase,
            node.not_,
        )


def to_filter(ast, dbtype, field_mapping=None):
    return PycswFilterEvaluator(field_mapping, dbtype).evaluate(ast)
