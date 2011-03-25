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

class Filter(object):
    ''' OGC Filter object support '''
    def __init__(self, flt, cq_mappings):
        ''' Initialize Filter '''

        self.boq = None

        tmp = flt.xpath('ogc:And|ogc:Or|ogc:Not', namespaces=config.NAMESPACES)
        if len(tmp) > 0:  # this is binary logic query
            self.boq = ' %s ' % util.xmltag_split(tmp[0].tag).lower()
            tmp = tmp[0]
        else:
            tmp = flt

        queries = []

        for child in tmp.xpath('child::*'):
            com_op = ''

            if child.tag == util.nspath_eval('ogc:Not'):
                property_name = \
                child.find(util.nspath_eval('ogc:BBOX/ogc:PropertyName'))
                if property_name is None:
                    raise RuntimeError, \
                    ('Missing ogc:PropertyName in spatial filter')
                elif (property_name is not None and property_name.text not in
                ['ows:BoundingBox', '/ows:BoundingBox']):
                    raise RuntimeError, \
                    ('Invalid ogc:PropertyName in spatial filter: %s' %
                    property_name.text)

                queries.append('query_not_bbox(%s,"%s") = "true"' %
                (cq_mappings['ows:BoundingBox']['db_col'],
                gml.get_bbox(child.xpath('child::*')[0])))

            elif child.tag == util.nspath_eval('ogc:BBOX'):
                property_name = child.find(util.nspath_eval('ogc:PropertyName'))
                if property_name is None:
                    raise RuntimeError, \
                    ('Missing PropertyName in spatial filter')
                elif (property_name is not None and
                      property_name.text not in  \
                      ['ows:BoundingBox', '/ows:BoundingBox']):
                    raise RuntimeError, \
                    ('Invalid PropertyName in spatial filter: %s' %
                    property_name.text)

                if self.boq is not None and self.boq == ' not ':
                    queries.append('query_not_bbox(%s,"%s") = "true"' %
                    (cq_mappings['ows:BoundingBox']['db_col'],
                     gml.get_bbox(child)))
                else:
                    queries.append('query_bbox(%s,"%s") = "true"' %
                    (cq_mappings['ows:BoundingBox']['db_col'],
                    gml.get_bbox(child)))

            elif child.tag == util.nspath_eval('ogc:FeatureId'):
                queries.append('%s = \'%s\'' %
                (cq_mappings['dc:identifier']['db_col'],
                child.attrib.get('fid')))

            else:
                matchcase = child.attrib.get('matchCase')
                wildcard = child.attrib.get('wildCard')
                singlechar = child.attrib.get('singleChar')
    
                if wildcard is None:
                    wildcard = '%'
    
                if singlechar is None:
                    singlechar = '_'
    
                try:
                    pname = cq_mappings[child.find(
                    util.nspath_eval('ogc:PropertyName')).text]['db_col']
                except Exception, err:
                    raise RuntimeError, ('Invalid PropertyName: %s.  %s' %
                    (child.find(util.nspath_eval('ogc:PropertyName')).text,
                    str(err)))

                if child.tag != util.nspath_eval('ogc:PropertyIsBetween'):
                    pval = child.find(util.nspath_eval('ogc:Literal')).text
                    pvalue = pval.replace(wildcard,'%').replace(singlechar,'_')

                com_op = _get_operator(child)

                # if this is a case insensitive search
                # then set the LIKE comparison operator
                if matchcase is not None and matchcase == 'false':
                    com_op = 'like'

                if child.tag == util.nspath_eval('ogc:PropertyIsBetween'):
                    com_op = 'between'
                    lower_boundary = child.find(
                    util.nspath_eval('ogc:LowerBoundary/ogc:Literal')).text
                    upper_boundary = child.find(
                    util.nspath_eval('ogc:UpperBoundary/ogc:Literal')).text
                    queries.append('%s %s "%s" and "%s"' %
                    (pname, com_op, lower_boundary, upper_boundary))

                elif (child.find(util.nspath_eval('ogc:PropertyName')).text ==
                'csw:AnyText'):
                    # csw:AnyText is a freetext search.  Strip modifiers
                    pvalue = pvalue.replace('%','')
                    queries.append('query_anytext(%s, "%s") = "true"' %
                    (cq_mappings['csw:AnyText']['db_col'], pvalue))

                else:
                    if self.boq == ' not ':
                        queries.append('%s is null or not %s %s "%s"' %
                        (pname, pname, com_op, pvalue))
                    else:
                        queries.append('%s %s "%s"' % (pname, com_op, pvalue))

        if self.boq is not None and self.boq != ' not ':
            self.where = self.boq.join(queries)
        else:
            self.where = queries[0]

def _get_operator(element):
    ''' return the SQL operator based on Filter query '''
    if element.tag == util.nspath_eval('ogc:PropertyIsEqualTo'):
        com_op = '=='
    elif element.tag == util.nspath_eval('ogc:PropertyIsNotEqualTo'):
        com_op = '!='
    elif element.tag == util.nspath_eval('ogc:PropertyIsLessThan'):
        com_op = '<'
    elif element.tag == util.nspath_eval('ogc:PropertyIsGreaterThan'):
        com_op = '>'
    elif element.tag == util.nspath_eval('ogc:PropertyIsLessThanOrEqualTo'):
        com_op = '<='
    elif element.tag == util.nspath_eval('ogc:PropertyIsGreaterThanOrEqualTo'):
        com_op = '>='
    elif element.tag == util.nspath_eval('ogc:PropertyIsLike'):
        com_op = 'like'
    elif element.tag == util.nspath_eval('ogc:PropertyIsNull'):
        com_op = 'is null'
    return com_op
