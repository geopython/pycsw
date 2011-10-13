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

import config, gml, util

MODEL =  {
    'GeometryOperands': {
        'values': ['gml:Point', 'gml:LineString', 'gml:Polygon', 'gml:Envelope']
    },
    'SpatialOperators': {
        'values': ['BBOX', 'Beyond', 'Contains', 'Crosses', 'Disjoint',
        'DWithin', 'Equals', 'Intersects', 'Overlaps', 'Touches', 'Within']
    },
    'ComparisonOperators': {
        'ogc:PropertyIsBetween': { 'opname': 'Between', 'opvalue': 'and'},
        'ogc:PropertyIsEqualTo': { 'opname': 'EqualTo', 'opvalue': '='},
        'ogc:PropertyIsGreaterThan': { 'opname': 'GreaterThan', 'opvalue': '>'},
        'ogc:PropertyIsGreaterThanOrEqualTo': { 
            'opname': 'GreaterThanEqualTo', 'opvalue': '>='},
        'ogc:PropertyIsLessThan': { 'opname': 'LessThan', 'opvalue': '<'},
        'ogc:PropertyIsLessThanOrEqualTo': {
            'opname': 'LessThanEqualTo', 'opvalue': '<='},
        'ogc:PropertyIsLike': { 'opname': 'Like', 'opvalue': 'like'},
        'ogc:PropertyIsNotEqualTo': { 'opname': 'NotEqualTo', 'opvalue': '!='},
        'ogc:PropertyIsNull': { 'opname': 'NullCheck', 'opvalue': 'is null'},
    },
    'Ids': {
        'values': ['EID', 'FID']
    }
}

def parse(element, queryables, dbtype):
    ''' OGC Filter object support '''

    boq = None

    tmp = element.xpath('ogc:And|ogc:Or|ogc:Not', namespaces=config.NAMESPACES)
    if len(tmp) > 0:  # this is binary logic query
        boq = ' %s ' % util.xmltag_split(tmp[0].tag).lower()
        tmp = tmp[0]
    else:
        tmp = element

    queries = []

    for child in tmp.xpath('child::*'):
        com_op = ''

        if child.tag == util.nspath_eval('ogc:Not'):
            queries.append("%s = 'false'" %
            _get_spatial_operator(child.xpath('child::*')[0]))

        elif child.tag in \
        [util.nspath_eval('ogc:%s' % n) for n in \
        MODEL['SpatialOperators']['values']]:
            if boq is not None and boq == ' not ':
                queries.append("%s = 'false'" %
                _get_spatial_operator(child))
            else:
                queries.append("%s = 'true'" % 
                _get_spatial_operator(child))

        elif child.tag == util.nspath_eval('ogc:FeatureId'):
            queries.append("identifier = '%s'" % child.attrib.get('fid'))

        else:
            matchcase = child.attrib.get('matchCase')
            wildcard = child.attrib.get('wildCard')
            singlechar = child.attrib.get('singleChar')

            if wildcard is None:
                wildcard = '%'

            if singlechar is None:
                singlechar = '_'

            try:
                pname = queryables[child.find(
                util.nspath_eval('ogc:PropertyName')).text]['dbcol']
            except Exception, err:
                raise RuntimeError, ('Invalid PropertyName: %s.  %s' %
                (child.find(util.nspath_eval('ogc:PropertyName')).text,
                str(err)))

            if child.tag != util.nspath_eval('ogc:PropertyIsBetween'):
                pval = child.find(util.nspath_eval('ogc:Literal')).text
                pvalue = pval.replace(wildcard,'%').replace(singlechar,'_')

            com_op = _get_comparison_operator(child)

            # if this is a case insensitive search
            # then set the DB-specific LIKE comparison operator
            if ((matchcase is not None and matchcase == 'false') or
            pname == 'anytext'):
                com_op = 'ilike' if dbtype == 'postgresql' else 'like'

            if child.tag == util.nspath_eval('ogc:PropertyIsBetween'):
                com_op = 'between'
                lower_boundary = child.find(
                util.nspath_eval('ogc:LowerBoundary/ogc:Literal')).text
                upper_boundary = child.find(
                util.nspath_eval('ogc:UpperBoundary/ogc:Literal')).text
                queries.append("%s %s '%s' and '%s'" %
                (pname, com_op, lower_boundary, upper_boundary))
            else:
                if boq == ' not ':
                    queries.append("%s is null or not %s %s '%s'" %
                    (pname, pname, com_op, pvalue))
                else:
                    queries.append("%s %s '%s'" % (pname, com_op, pvalue))

    where = boq.join(queries) if (boq is not None and boq != ' not ') \
    else queries[0]

    return where

def _get_spatial_operator(element):
    ''' return the spatial predicate function '''
    property_name = element.find(util.nspath_eval('ogc:PropertyName'))
    distance = element.find(util.nspath_eval('ogc:Distance'))

    distance = 'false' if distance is None else distance.text

    if property_name is None:
        raise RuntimeError, \
        ('Missing ogc:PropertyName in spatial filter')
    if (property_name.text.find('BoundingBox') == -1 and
        property_name.text.find('Envelope') == -1):
        raise RuntimeError, \
        ('Invalid ogc:PropertyName in spatial filter: %s' %
        property_name.text)

    spatial_query = "query_spatial(wkt_geometry,'%s','%s','%s')" % \
    (gml.get_geometry(element, MODEL['GeometryOperands']['values']),
    util.xmltag_split(element.tag).lower(), distance)

    return spatial_query

def _get_comparison_operator(element):
    ''' return the SQL operator based on Filter query '''

    return MODEL['ComparisonOperators']\
    ['ogc:%s' % util.xmltag_split(element.tag)]['opvalue'] 
