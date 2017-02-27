# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
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
from pycsw.ogc.gml import gml3

LOGGER = logging.getLogger(__name__)

MODEL = {
    'GeometryOperands': {
        'values': gml3.TYPES
    },
    'SpatialOperators': {
        'values': ['BBOX', 'Beyond', 'Contains', 'Crosses', 'Disjoint',
        'DWithin', 'Equals', 'Intersects', 'Overlaps', 'Touches', 'Within']
    },
    'ComparisonOperators': {
        'ogc:PropertyIsBetween': {'opname': 'Between', 'opvalue': 'and'},
        'ogc:PropertyIsEqualTo': {'opname': 'EqualTo', 'opvalue': '='},
        'ogc:PropertyIsGreaterThan': {'opname': 'GreaterThan', 'opvalue': '>'},
        'ogc:PropertyIsGreaterThanOrEqualTo': {
            'opname': 'GreaterThanEqualTo', 'opvalue': '>='},
        'ogc:PropertyIsLessThan': {'opname': 'LessThan', 'opvalue': '<'},
        'ogc:PropertyIsLessThanOrEqualTo': {
            'opname': 'LessThanEqualTo', 'opvalue': '<='},
        'ogc:PropertyIsLike': {'opname': 'Like', 'opvalue': 'like'},
        'ogc:PropertyIsNotEqualTo': {'opname': 'NotEqualTo', 'opvalue': '!='},
        'ogc:PropertyIsNull': {'opname': 'NullCheck', 'opvalue': 'is null'},
    },
    'Functions': {
        'length': {'args': '1'},
        'lower': {'args': '1'},
        'ltrim': {'args': '1'},
        'rtrim': {'args': '1'},
        'trim': {'args': '1'},
        'upper': {'args': '1'},
    },
    'Ids': {
        'values': ['EID', 'FID']
    }
}


def parse(element, queryables, dbtype, nsmap, orm='sqlalchemy', language='english', fts=False):
    """OGC Filter object support"""

    boq = None
    is_pg = dbtype.startswith('postgresql')

    tmp = element.xpath('ogc:And|ogc:Or|ogc:Not', namespaces=nsmap)
    if len(tmp) > 0:  # this is binary logic query
        element_name = etree.QName(tmp[0]).localname
        boq = ' %s ' % element_name.lower()
        LOGGER.debug('Binary logic detected; operator=%s', boq)
        tmp = tmp[0]
    else:
        tmp = element

    pvalue_serial = [0]  # in list as python 2 has no nonlocal variable
    def assign_param():
        if orm == 'django':
            return '%s'
        param = ':pvalue%d' % pvalue_serial[0]
        pvalue_serial[0] += 1
        return param

    def _get_comparison_expression(elem):
        """return the SQL expression based on Filter query"""
        fname = None
        matchcase = elem.attrib.get('matchCase')
        wildcard = elem.attrib.get('wildCard')
        singlechar = elem.attrib.get('singleChar')
        expression = None

        if wildcard is None:
            wildcard = '%'

        if singlechar is None:
            singlechar = '_'

        if (elem.xpath('child::*')[0].tag ==
                util.nspath_eval('ogc:Function', nsmap)):
            LOGGER.debug('ogc:Function detected')
            if (elem.xpath('child::*')[0].attrib['name'] not in
                    MODEL['Functions']):
                raise RuntimeError('Invalid ogc:Function: %s' %
                                   (elem.xpath('child::*')[0].attrib['name']))
            fname = elem.xpath('child::*')[0].attrib['name']

            try:
                LOGGER.debug('Testing existence of ogc:PropertyName')
                pname = queryables[elem.find(util.nspath_eval('ogc:Function/ogc:PropertyName', nsmap)).text]['dbcol']
            except Exception as err:
                raise RuntimeError('Invalid PropertyName: %s.  %s' % (elem.find(util.nspath_eval('ogc:Function/ogc:PropertyName', nsmap)).text, str(err)))

        else:
            try:
                LOGGER.debug('Testing existence of ogc:PropertyName')
                pname = queryables[elem.find(
                    util.nspath_eval('ogc:PropertyName', nsmap)).text]['dbcol']
            except Exception as err:
                raise RuntimeError('Invalid PropertyName: %s.  %s' %
                                   (elem.find(util.nspath_eval('ogc:PropertyName',
                                   nsmap)).text, str(err)))

        if (elem.tag != util.nspath_eval('ogc:PropertyIsBetween', nsmap)):
            if elem.tag in [util.nspath_eval('ogc:%s' % n, nsmap) for n in
                MODEL['SpatialOperators']['values']]:
                boolean_true = '\'true\''
                boolean_false = '\'false\''
                if dbtype == 'mysql':
                    boolean_true = 'true'
                    boolean_false = 'false'

                return "%s = %s" % (_get_spatial_operator(queryables['pycsw:BoundingBox'], elem, dbtype, nsmap), boolean_true)
            else:
                pval = elem.find(util.nspath_eval('ogc:Literal', nsmap)).text

        com_op = _get_comparison_operator(elem)
        LOGGER.debug('Comparison operator: %s', com_op)

        # if this is a case insensitive search
        # then set the DB-specific LIKE comparison operator

        LOGGER.debug('Setting csw:AnyText property')

        anytext = queryables['csw:AnyText']['dbcol']
        if ((matchcase is not None and matchcase == 'false') or
                pname == anytext):
            com_op = 'ilike' if is_pg else 'like'

        if (elem.tag == util.nspath_eval('ogc:PropertyIsBetween', nsmap)):
            com_op = 'between'
            lower_boundary = elem.find(
                util.nspath_eval('ogc:LowerBoundary/ogc:Literal',
                                 nsmap)).text
            upper_boundary = elem.find(
                util.nspath_eval('ogc:UpperBoundary/ogc:Literal',
                                 nsmap)).text
            expression = "%s %s %s and %s" % \
                           (pname, com_op, assign_param(), assign_param())
            values.append(lower_boundary)
            values.append(upper_boundary)
        else:
            if pname == anytext and is_pg and fts:
                LOGGER.debug('PostgreSQL FTS specific search')
                # do nothing, let FTS do conversion (#212)
                pvalue = pval
            else:
                LOGGER.debug('PostgreSQL non-FTS specific search')
                pvalue = pval.replace(wildcard, '%').replace(singlechar, '_')

                if pname == anytext:  # pad anytext with wildcards
                    LOGGER.debug('PostgreSQL non-FTS specific anytext search')
                    LOGGER.debug('old value: %s', pval)

                    pvalue = '%%%s%%' % pvalue.rstrip('%').lstrip('%')

                    LOGGER.debug('new value: %s', pvalue)

            values.append(pvalue)

            if boq == ' not ':
                if fname is not None:
                    expression = "%s is null or not %s(%s) %s %s" % \
                                   (pname, fname, pname, com_op, assign_param())
                elif pname == anytext and is_pg and fts:
                    LOGGER.debug('PostgreSQL FTS specific search')
                    expression = ("%s is null or not plainto_tsquery('%s', %s) @@ anytext_tsvector" %
                                  (anytext, language, assign_param()))
                else:
                    LOGGER.debug('PostgreSQL non-FTS specific search')
                    expression = "%s is null or not %s %s %s" % \
                                   (pname, pname, com_op, assign_param())
            else:
                if fname is not None:
                    expression = "%s(%s) %s %s" % \
                                   (fname, pname, com_op, assign_param())
                elif pname == anytext and is_pg and fts:
                    LOGGER.debug('PostgreSQL FTS specific search')
                    expression = ("plainto_tsquery('%s', %s) @@ anytext_tsvector" %
                                  (language, assign_param()))
                else:
                    LOGGER.debug('PostgreSQL non-FTS specific search')
                    expression = "%s %s %s" % (pname, com_op, assign_param())

        return expression

    queries = []
    queries_nested = []
    values = []

    LOGGER.debug('Scanning children elements')
    for child in tmp.xpath('child::*'):
        com_op = ''
        boolean_true = '\'true\''
        boolean_false = '\'false\''

        if dbtype == 'mysql':
            boolean_true = 'true'
            boolean_false = 'false'

        if child.tag == util.nspath_eval('ogc:Not', nsmap):
            LOGGER.debug('ogc:Not query detected')
            child_not = child.xpath('child::*')[0]
            if child_not.tag in \
                [util.nspath_eval('ogc:%s' % n, nsmap) for n in
                    MODEL['SpatialOperators']['values']]:
                LOGGER.debug('ogc:Not / spatial operator detected: %s', child.tag)
                queries.append("%s = %s" %
                               (_get_spatial_operator(
                                   queryables['pycsw:BoundingBox'],
                                   child.xpath('child::*')[0], dbtype, nsmap),
                                   boolean_false))
            else:
                LOGGER.debug('ogc:Not / comparison operator detected: %s', child.tag)
                queries.append('not %s' % _get_comparison_expression(child_not))

        elif child.tag in \
            [util.nspath_eval('ogc:%s' % n, nsmap) for n in
                MODEL['SpatialOperators']['values']]:
            LOGGER.debug('spatial operator detected: %s', child.tag)
            if boq is not None and boq == ' not ':
                # for ogc:Not spatial queries in PostGIS we must explictly
                # test that pycsw:BoundingBox is null as well
                # TODO: Do we need the same for 'postgresql+postgis+native'???
                if dbtype == 'postgresql+postgis+wkt':
                    LOGGER.debug('Setting bbox is null test in PostgreSQL')
                    queries.append("%s = %s or %s is null" %
                                   (_get_spatial_operator(
                                       queryables['pycsw:BoundingBox'],
                                       child, dbtype, nsmap), boolean_false,
                                       queryables['pycsw:BoundingBox']))
                else:
                    queries.append("%s = %s" %
                                   (_get_spatial_operator(
                                       queryables['pycsw:BoundingBox'],
                                       child, dbtype, nsmap), boolean_false))
            else:
                queries.append("%s = %s" %
                               (_get_spatial_operator(
                                   queryables['pycsw:BoundingBox'],
                                   child, dbtype, nsmap), boolean_true))

        elif child.tag == util.nspath_eval('ogc:FeatureId', nsmap):
            LOGGER.debug('ogc:FeatureId filter detected')
            queries.append("%s = %s" % (queryables['pycsw:Identifier'], assign_param()))
            values.append(child.attrib.get('fid'))
        else:  # comparison operator
            LOGGER.debug('Comparison operator processing')
            child_tag_name = etree.QName(child).localname
            tagname = ' %s ' % child_tag_name.lower()
            if tagname in [' or ', ' and ']:  # this is a nested binary logic query
                LOGGER.debug('Nested binary logic detected; operator=%s', tagname)
                for child2 in child.xpath('child::*'):
                    queries_nested.append(_get_comparison_expression(child2))
                queries.append('(%s)' % tagname.join(queries_nested))
            else:
                queries.append(_get_comparison_expression(child))

    where = boq.join(queries) if (boq is not None and boq != ' not ') \
        else queries[0]

    return where, values


def _get_spatial_operator(geomattr, element, dbtype, nsmap, postgis_geometry_column='wkb_geometry'):
    """return the spatial predicate function"""
    property_name = element.find(util.nspath_eval('ogc:PropertyName', nsmap))
    distance = element.find(util.nspath_eval('ogc:Distance', nsmap))

    distance = 'false' if distance is None else distance.text

    LOGGER.debug('Scanning for spatial property name')

    if property_name is None:
        raise RuntimeError('Missing ogc:PropertyName in spatial filter')
    if (property_name.text.find('BoundingBox') == -1 and
            property_name.text.find('Envelope') == -1):
        raise RuntimeError('Invalid ogc:PropertyName in spatial filter: %s' %
                           property_name.text)

    geometry = gml3.Geometry(element, nsmap)

    #make decision to apply spatial ranking to results
    set_spatial_ranking(geometry)

    spatial_predicate = etree.QName(element).localname.lower()

    LOGGER.debug('Spatial predicate: %s', spatial_predicate)

    if dbtype == 'mysql':  # adjust spatial query for MySQL
        LOGGER.debug('Adjusting spatial query for MySQL')
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
            geomfromtext('%s')),false)" % \
                (spatial_predicate, geomattr, geometry.wkt)

    elif dbtype == 'postgresql+postgis+wkt':  # adjust spatial query for PostGIS with WKT geometry column
        LOGGER.debug('Adjusting spatial query for PostgreSQL+PostGIS+WKT')
        if spatial_predicate == 'bbox':
            spatial_predicate = 'intersects'

        if spatial_predicate == 'beyond':
            spatial_query = "not st_dwithin(st_geomfromtext(%s), \
            st_geomfromtext('%s'), %f)" % \
                (geomattr, geometry.wkt, float(distance))
        elif spatial_predicate == 'dwithin':
            spatial_query = "st_dwithin(st_geomfromtext(%s), \
            st_geomfromtext('%s'), %f)" % \
                (geomattr, geometry.wkt, float(distance))
        else:
            spatial_query = "st_%s(st_geomfromtext(%s), \
            st_geomfromtext('%s'))" % \
                (spatial_predicate, geomattr, geometry.wkt)

    elif dbtype == 'postgresql+postgis+native':  # adjust spatial query for PostGIS with native geometry
        LOGGER.debug('Adjusting spatial query for PostgreSQL+PostGIS+native')
        if spatial_predicate == 'bbox':
            spatial_predicate = 'intersects'

        if spatial_predicate == 'beyond':
            spatial_query = "not st_dwithin(%s, \
            st_geomfromtext('%s',4326), %f)" % \
                (postgis_geometry_column, geometry.wkt, float(distance))
        elif spatial_predicate == 'dwithin':
            spatial_query = "st_dwithin(%s, \
            st_geomfromtext('%s',4326), %f)" % \
                (postgis_geometry_column, geometry.wkt, float(distance))
        else:
            spatial_query = "st_%s(%s, \
            st_geomfromtext('%s',4326))" % \
                (spatial_predicate, postgis_geometry_column, geometry.wkt)

    else:
        LOGGER.debug('Adjusting spatial query')
        spatial_query = "query_spatial(%s,'%s','%s','%s')" % \
                        (geomattr, geometry.wkt, spatial_predicate, distance)

    return spatial_query


def _get_comparison_operator(element):
    """return the SQL operator based on Filter query"""

    element_name = etree.QName(element).localname
    return MODEL['ComparisonOperators']['ogc:%s' % element_name]['opvalue']

def set_spatial_ranking(geometry):
    """Given that we have a spatial query in ogc:Filter we check the type of geometry
    and set the ranking variables"""

    if util.ranking_enabled:
        if geometry.type in ['Polygon', 'Envelope']:
            util.ranking_pass = True
            util.ranking_query_geometry = geometry.wkt
        elif geometry.type in ['LineString', 'Point']:
            from shapely.geometry.base import BaseGeometry
            from shapely.geometry import box
            from shapely.wkt import loads,dumps
            ls = loads(geometry.wkt)
            b = ls.bounds
            if geometry.type == 'LineString':
                tmp_box = box(b[0],b[1],b[2],b[3])
                tmp_wkt = dumps(tmp_box)
                if tmp_box.area > 0:
                    util.ranking_pass = True
                    util.ranking_query_geometry = tmp_wkt
            elif geometry.type == 'Point':
                tmp_box = box((float(b[0])-1.0),(float(b[1])-1.0),(float(b[2])+1.0),(float(b[3])+1.0))
                tmp_wkt = dumps(tmp_box)
                util.ranking_pass = True
                util.ranking_query_geometry = tmp_wkt
