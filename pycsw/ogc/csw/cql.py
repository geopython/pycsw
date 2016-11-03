# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2016 Tom Kralidis
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

from pycsw.core.etree import etree
from pycsw.core import util
from pycsw.ogc.fes.fes1 import MODEL as fes1_model

LOGGER = logging.getLogger(__name__)


def cql2fes1(cql, namespaces):
    """transforms Common Query Language (CQL) query into OGC fes1 syntax"""

    filters = []
    tmp_list = []
    logical_op = None

    LOGGER.debug('CQL: %s', cql)

    if ' or ' in cql:
        logical_op = etree.Element(util.nspath_eval('ogc:Or', namespaces))
        tmp_list = cql.split(' or ')
    elif ' OR ' in cql:
        logical_op = etree.Element(util.nspath_eval('ogc:Or', namespaces))
        tmp_list = cql.split(' OR ')
    elif ' and ' in cql:
        logical_op = etree.Element(util.nspath_eval('ogc:And', namespaces))
        tmp_list = cql.split(' and ')
    elif ' AND ' in cql:
        logical_op = etree.Element(util.nspath_eval('ogc:And', namespaces))
        tmp_list = cql.split(' AND ')

    if tmp_list:
        LOGGER.debug('Logical operator found (AND/OR)')
    else:
        tmp_list.append(cql)

    for t in tmp_list:
        filters.append(_parse_condition(t))

    root = etree.Element(util.nspath_eval('ogc:Filter', namespaces))

    if logical_op is not None:
        root.append(logical_op)

    for flt in filters:
        condition = etree.Element(util.nspath_eval(flt[0], namespaces))

        etree.SubElement(
            condition,
            util.nspath_eval('ogc:PropertyName', namespaces)).text = flt[1]

        etree.SubElement(
            condition,
            util.nspath_eval('ogc:Literal', namespaces)).text = flt[2]

        if logical_op is not None:
            logical_op.append(condition)
        else:
            root.append(condition)

    LOGGER.debug('Resulting OGC Filter: %s',
                 etree.tostring(root, pretty_print=1))

    return root


def _parse_condition(condition):
    """parses a single condition"""

    LOGGER.debug('condition: %s', condition)

    # split at the most 2 times to take into account literals with
    # spaces in them
    property_name, operator, literal = condition.split(None, 2)

    literal = literal.replace('"', '').replace('\'', '')

    for k, v in fes1_model['ComparisonOperators'].items():
        if v['opvalue'] == operator:
            fes1_predicate = k

    LOGGER.debug('parsed condition: %s %s %s', property_name, fes1_predicate,
                 literal)

    return (fes1_predicate, property_name, literal)
