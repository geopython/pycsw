# -*- coding: iso-8859-15 -*-
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

import gml, util

MODEL =  {
    'GeometryOperands': {
        'values': gml.TYPES
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
    'Functions': {
        'length': { 'args': '1'},
        'lower': { 'args': '1'},
        'ltrim': { 'args': '1'},
        'rtrim': { 'args': '1'},
        'trim': { 'args': '1'},
        'upper': { 'args': '1'},
    },
    'Ids': {
        'values': ['EID', 'FID']
    }
}

def parse(element, queryables, dbtype, nsmap):
    ''' OGC Filter object support '''

    boq = None

    tmp = element.xpath('ogc:And|ogc:Or|ogc:Not', namespaces=nsmap)
    if len(tmp) > 0:  # this is binary logic query
        boq = ' %s ' % util.xmltag_split(tmp[0].tag).lower()
        tmp = tmp[0]
    else:
        tmp = element

    queries = []

    for child in tmp.xpath('child::*'):
        com_op = ''
        boolean_true = '\'true\''
        boolean_false = '\'false\''

        if dbtype == 'mysql':
            boolean_true = 'true'
            boolean_false = 'false'

        if child.tag == util.nspath_eval('ogc:Not', nsmap):
            queries.append("%s = %s" %
            (_get_spatial_operator(queryables['pycsw:BoundingBox'],
            child.xpath('child::*')[0], dbtype, nsmap), boolean_false))

        elif child.tag in \
        [util.nspath_eval('ogc:%s' % n, nsmap) for n in \
        MODEL['SpatialOperators']['values']]:
            if boq is not None and boq == ' not ':
                # for ogc:Not spatial queries in PostGIS we must explictly
                # test that pycsw:BoundingBox is null as well
                if dbtype == 'postgresql+postgis':
                    queries.append("%s = %s or %s is null" %
                    (_get_spatial_operator(queryables['pycsw:BoundingBox'],
                    child, dbtype, nsmap), boolean_false,
                    queryables['pycsw:BoundingBox']))
                else:
                    queries.append("%s = %s" %
                    (_get_spatial_operator(queryables['pycsw:BoundingBox'],
                    child, dbtype, nsmap), boolean_false))
            else:
                queries.append("%s = %s" % 
                (_get_spatial_operator(queryables['pycsw:BoundingBox'],
                 child, dbtype, nsmap), boolean_true))

        elif child.tag == util.nspath_eval('ogc:FeatureId', nsmap):
            queries.append("%s = '%s'" % (queryables['pycsw:Identifier'],
            child.attrib.get('fid')))

        else:
            fname = None
            matchcase = child.attrib.get('matchCase')
            wildcard = child.attrib.get('wildCard')
            singlechar = child.attrib.get('singleChar')

            if wildcard is None:
                wildcard = '%'

            if singlechar is None:
                singlechar = '_'

            if (child.xpath('child::*')[0].tag ==
                util.nspath_eval('ogc:Function', nsmap)):
                if (child.xpath('child::*')[0].attrib['name'] not in
                MODEL['Functions'].keys()):
                    raise RuntimeError, ('Invalid ogc:Function: %s' %
                    (child.xpath('child::*')[0].attrib['name']))
                fname = child.xpath('child::*')[0].attrib['name']

                try:
                    pname = queryables[child.find(
                    util.nspath_eval('ogc:Function/ogc:PropertyName',
                    nsmap)).text]['dbcol']
                except Exception, err:
                    raise RuntimeError, ('Invalid PropertyName: %s.  %s' %
                    (child.find(util.nspath_eval('ogc:Function/ogc:PropertyName',
                    nsmap)).text,
                    str(err)))

            else:
                try:
                    pname = queryables[child.find(
                    util.nspath_eval('ogc:PropertyName', nsmap)).text]['dbcol']
                except Exception, err:
                    raise RuntimeError, ('Invalid PropertyName: %s.  %s' %
                    (child.find(util.nspath_eval('ogc:PropertyName',
                     nsmap)).text,
                     str(err)))

            if (child.tag != util.nspath_eval('ogc:PropertyIsBetween', nsmap)):
                pval = child.find(util.nspath_eval('ogc:Literal', nsmap)).text
                pvalue = pval.replace(wildcard,'%').replace(singlechar,'_')

            com_op = _get_comparison_operator(child)

            # if this is a case insensitive search
            # then set the DB-specific LIKE comparison operator
            if ((matchcase is not None and matchcase == 'false') or
            pname == 'anytext'):
                com_op = 'ilike' if dbtype in ['postgresql', 'postgresql+postgis'] else 'like'

            if (child.tag == util.nspath_eval('ogc:PropertyIsBetween', nsmap)):
                com_op = 'between'
                lower_boundary = child.find(
                    util.nspath_eval('ogc:LowerBoundary/ogc:Literal',
                    nsmap)).text
                upper_boundary = child.find(
                    util.nspath_eval('ogc:UpperBoundary/ogc:Literal',
                    nsmap)).text
                queries.append("%s %s '%s' and '%s'" %
                (pname, com_op, lower_boundary, upper_boundary))
            else:
                if boq == ' not ':
                    if fname is not None:
                        queries.append("%s is null or not %s(%s) %s '%s'" %
                        (pname, fname, pname, com_op, pvalue))
                    else:
                        queries.append("%s is null or not %s %s '%s'" %
                        (pname, pname, com_op, pvalue))
                else:
                    if fname is not None:
                        queries.append("%s(%s) %s '%s'" % \
                        (fname, pname, com_op, pvalue))
                    else:
                        queries.append("%s %s '%s'" % (pname, com_op, pvalue))

    where = boq.join(queries) if (boq is not None and boq != ' not ') \
    else queries[0]

    return where

def _get_spatial_operator(geomattr, element, dbtype, nsmap):
    ''' return the spatial predicate function '''
    property_name = element.find(util.nspath_eval('ogc:PropertyName', nsmap))
    distance = element.find(util.nspath_eval('ogc:Distance', nsmap))

    distance = 'false' if distance is None else distance.text

    if property_name is None:
        raise RuntimeError, \
        ('Missing ogc:PropertyName in spatial filter')
    if (property_name.text.find('BoundingBox') == -1 and
        property_name.text.find('Envelope') == -1):
        raise RuntimeError, \
        ('Invalid ogc:PropertyName in spatial filter: %s' %
        property_name.text)

    geometry = gml.Geometry(element, nsmap)

    spatial_predicate = util.xmltag_split(element.tag).lower()

    if dbtype == 'mysql':  # adjust spatial query for MySQL
        if spatial_predicate == 'bbox':
            spatial_predicate = 'intersects'

        if spatial_predicate == 'beyond':
            spatial_query = "ifnull(distance(geomfromtext(%s), \
            geomfromtext('%s')) > convert(%s, signed),false)" % \
            (geomattr, geometry.wkt, distance)
        elif spatial_predicate == 'dwithin':
            spatial_query = "ifnull(distance(geomfromtext(%s), \
            geomfromtext('%s')) <= convert(%s, signed),false)" % \
            (geomattr, geometry.wkt, distance)
        else:
            spatial_query = "ifnull(%s(geomfromtext(%s), \
            geomfromtext('%s')),false)" % (spatial_predicate, geomattr, geometry.wkt)

    elif dbtype == 'postgresql+postgis':  # adjust spatial query for PostGIS
        if spatial_predicate == 'bbox':
            spatial_predicate = 'intersects'

        if spatial_predicate == 'beyond':
            spatial_query = "not st_dwithin(st_geomfromtext(%s), \
            st_geomfromtext('%s'), %f)" % (geomattr, geometry.wkt, float(distance))
        elif spatial_predicate == 'dwithin':
            spatial_query = "st_dwithin(st_geomfromtext(%s), \
            st_geomfromtext('%s'), %f)" % (geomattr, geometry.wkt, float(distance))
        else:
            spatial_query = "st_%s(st_geomfromtext(%s), \
            st_geomfromtext('%s'))" % (spatial_predicate, geomattr, geometry.wkt)
    else:
        spatial_query = "query_spatial(%s,'%s','%s','%s')" % \
        (geomattr, geometry.wkt, spatial_predicate, distance)

    return spatial_query

def _get_comparison_operator(element):
    ''' return the SQL operator based on Filter query '''

    return MODEL['ComparisonOperators']\
    ['ogc:%s' % util.xmltag_split(element.tag)]['opvalue'] 
