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

from lxml import etree
import config, gml, util

class Filter(object):
    def __init__(self, flt, cq_mappings):

        self.boq = None

        tmp = flt.xpath('ogc:And|ogc:Or|ogc:Not', namespaces=config.namespaces)
        if len(tmp) > 0:  # this is binary logic query
            self.boq = ' %s ' % util.xmltag_split(tmp[0].tag).lower()
            tmp = tmp[0]
        else:
            tmp = flt

        queries = []

        for c in tmp.xpath('child::*'):
            co = ''

            if c.tag == util.nspath_eval('ogc:Not'):
                pn = c.find(util.nspath_eval('ogc:BBOX/ogc:PropertyName'))
                if pn is None:
                    raise RuntimeError, ('Missing ogc:PropertyName in spatial filter')
                elif pn is not None and pn.text not in ['ows:BoundingBox', '/ows:BoundingBox']:
                    raise RuntimeError, ('Invalid ogc:PropertyName in spatial filter: %s' % pn.text)
                bbox = gml.get_bbox(c.xpath('child::*')[0])

                queries.append('query_not_bbox(%s,"%s") = "true"' % (cq_mappings['ows:BoundingBox']['db_col'], bbox))

            elif c.tag == util.nspath_eval('ogc:BBOX'):
                pn = c.find(util.nspath_eval('ogc:PropertyName'))
                if pn is None:
                    raise RuntimeError, ('Missing PropertyName in spatial filter')
                elif pn is not None and pn.text not in ['ows:BoundingBox', '/ows:BoundingBox']:
                    raise RuntimeError, ('Invalid PropertyName in spatial filter: %s' % pn.text)
                bbox = gml.get_bbox(c)

                if self.boq is not None and self.boq == ' not ':
                    queries.append('query_not_bbox(%s,"%s") = "true"' % (cq_mappings['ows:BoundingBox']['db_col'], bbox))
                else:
                    queries.append('query_bbox(%s,"%s") = "true"' % (cq_mappings['ows:BoundingBox']['db_col'], bbox))

            elif c.tag == util.nspath_eval('ogc:FeatureId'):
                id = c.attrib.get('fid')
                queries.append('%s = \'%s\'' % (cq_mappings['dc:identifier']['db_col'], id))

            else:
                matchcase = c.attrib.get('matchCase')
                wildcard = c.attrib.get('wildCard')
                singlechar = c.attrib.get('singleChar')
    
                if wildcard is None:
                    wildcard = '%'
    
                if singlechar is None:
                    singlechar = '_'
    
                try:
                    pname = cq_mappings[c.find(util.nspath_eval('ogc:PropertyName')).text]['db_col']
                except Exception, err:
                    raise RuntimeError, ('Invalid PropertyName: %s' % c.find(util.nspath_eval('ogc:PropertyName')).text)

                if c.tag != util.nspath_eval('ogc:PropertyIsBetween'):
                    pv = c.find(util.nspath_eval('ogc:Literal')).text
                    pvalue = pv.replace(wildcard,'%').replace(singlechar,'_')

                if c.tag == util.nspath_eval('ogc:PropertyIsEqualTo'):
                    co = '=='
                elif c.tag == util.nspath_eval('ogc:PropertyIsNotEqualTo'):
                    co = '!='
                elif c.tag == util.nspath_eval('ogc:PropertyIsLessThan'):
                    co = '<'
                elif c.tag == util.nspath_eval('ogc:PropertyIsGreaterThan'):
                    co = '>'
                elif c.tag == util.nspath_eval('ogc:PropertyIsLessThanOrEqualTo'):
                    co = '<='
                elif c.tag == util.nspath_eval('ogc:PropertyIsGreaterThanOrEqualTo'):
                    co = '>='
                elif c.tag == util.nspath_eval('ogc:PropertyIsLike'):
                    co = 'like'
                elif c.tag == util.nspath_eval('ogc:PropertyIsNull'):
                    co = 'is null'
    
                # if this is a case insensitive search, then set the LIKE comparison operator
                if matchcase is not None and matchcase == 'false':
                    co = 'like'

                if c.tag == util.nspath_eval('ogc:PropertyIsBetween'):
                    co = 'between'
                    lb = c.find(util.nspath_eval('ogc:LowerBoundary/ogc:Literal')).text
                    ub = c.find(util.nspath_eval('ogc:UpperBoundary/ogc:Literal')).text
                    queries.append('%s %s "%s" and "%s"' % (pname, co, lb, ub))

                elif c.find(util.nspath_eval('ogc:PropertyName')).text == 'csw:AnyText':
                    # csw:AnyText is a freetext search.  Strip modifiers
                    pvalue=pvalue.replace('%','')
                    queries.append('query_anytext(%s, "%s") = "true"' % (cq_mappings['csw:AnyText']['db_col'], pvalue))

                else:
                    if self.boq == ' not ':
                        queries.append('not %s %s "%s"' % (pname,co,pvalue))
                    else:
                        queries.append('%s %s "%s"' % (pname,co,pvalue))

        if self.boq is not None and self.boq != ' not ':
            self.where = self.boq.join(queries)
        else:
            self.where = queries[0]
