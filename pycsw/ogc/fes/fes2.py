# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2024 Tom Kralidis
# Copyright (c) 2015 Angelos Tzotsos
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

from pycsw.core import util
from pycsw.core.etree import etree
from pycsw.ogc.gml import gml32

LOGGER = logging.getLogger(__name__)

MODEL = {
    'Conformance': {
        'values': [
            'ImplementsQuery',
            'ImplementsAdHocQuery',
            'ImplementsFunctions',
            'ImplementsResourceld',
            'ImplementsMinStandardFilter',
            'ImplementsStandardFilter',
            'ImplementsMinSpatialFilter',
            'ImplementsSpatialFilter',
            'ImplementsMinTemporalFilter',
            'ImplementsTemporalFilter',
            'ImplementsVersionNav',
            'ImplementsSorting',
            'ImplementsExtendedOperators',
            'ImplementsMinimumXPath',
            'ImplementsSchemaElementFunc'
        ]
    },
    'GeometryOperands': {
        'values': gml32.TYPES
    },
    'SpatialOperators': {
        'values': ['BBOX', 'Beyond', 'Contains', 'Crosses', 'Disjoint',
        'DWithin', 'Equals', 'Intersects', 'Overlaps', 'Touches', 'Within']
    },
    'ComparisonOperators': {
        'fes20:PropertyIsBetween': {'opname': 'PropertyIsBetween', 'opvalue': 'and'},
        'fes20:PropertyIsEqualTo': {'opname': 'PropertyIsEqualTo', 'opvalue': '='},
        'fes20:PropertyIsGreaterThan': {'opname': 'PropertyIsGreaterThan', 'opvalue': '>'},
        'fes20:PropertyIsGreaterThanOrEqualTo': {
            'opname': 'PropertyIsGreaterThanOrEqualTo', 'opvalue': '>='},
        'fes20:PropertyIsLessThan': {'opname': 'PropertyIsLessThan', 'opvalue': '<'},
        'fes20:PropertyIsLessThanOrEqualTo': {
            'opname': 'PropertyIsLessThanOrEqualTo', 'opvalue': '<='},
        'fes20:PropertyIsLike': {'opname': 'PropertyIsLike', 'opvalue': 'like'},
        'fes20:PropertyIsNotEqualTo': {'opname': 'PropertyIsNotEqualTo', 'opvalue': '!='},
        'fes20:PropertyIsNull': {'opname': 'PropertyIsNull', 'opvalue': 'is null'},
    },
    'Functions': {
        'length': {'returns': 'xs:string'},
        'lower': {'returns': 'xs:string'},
        'ltrim': {'returns': 'xs:string'},
        'rtrim': {'returns': 'xs:string'},
        'trim': {'returns': 'xs:string'},
        'upper': {'returns': 'xs:string'},
    },
    'Ids': {
        'values': ['csw30:id']
    }
}
