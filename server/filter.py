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
import config, gml

class Filter(object):
    def __init__(self, flt):

        self.boq = None

        tmp = flt.xpath('ogc:And|ogc:Or|ogc:Not', namespaces={'ogc':'http://www.opengis.net/ogc'})
        if len(tmp) > 0:  # this is binary logic query
            self.boq = ' %s ' % tmp[0].tag.split('}')[1].lower()
            tmp = tmp[0]
        else:
            tmp = flt

        queries = []

        for c in tmp.xpath('child::*'):
            co = ''
            bquery = 'true'

            if c.tag == '{http://www.opengis.net/ogc}BBOX':
                pn = c.find('{http://www.opengis.net/ogc}PropertyName')
                if pn is None:
                    raise RuntimeError, ('Missing PropertyName in spatial filter')
                elif pn is not None and pn.text not in ['ows:BoundingBox', '/ows:BoundingBox']:
                    raise RuntimeError, ('Invalid PropertyName in spatial filter: %s' % pn.text)
                bbox = gml.get_bbox(c)

                if self.boq is not None and self.boq == ' not ':
                    queries.append('bbox_query(bbox,"%s") = "false"' % bbox)
                else:
                #self.where = 'bbox_query(bbox,"%s") = "true"' % bbox
                    queries.append('bbox_query(bbox,"%s") = "true"' % bbox)

            else:
                matchcase = c.attrib.get('matchCase')
                wildcard = c.attrib.get('wildCard')
                singlechar = c.attrib.get('singleChar')
    
                if wildcard is None:
                    wildcard = '%'
    
                if singlechar is None:
                    singlechar = '_'
    
                try:
                    pname = config.mappings[c.find('{http://www.opengis.net/ogc}PropertyName').text]
                except Exception, err:
                    raise RuntimeError, ('Invalid PropertyName: %s' % c.find('{http://www.opengis.net/ogc}PropertyName').text)
    
                pv = c.find('{http://www.opengis.net/ogc}Literal').text
    
                pvalue = pv.replace(wildcard,'%').replace(singlechar,'_')

                if c.tag == '{http://www.opengis.net/ogc}PropertyIsEqualTo':
                    co = '=='
                elif c.tag == '{http://www.opengis.net/ogc}PropertyIsNotEqualTo':
                    co = '!='
                elif c.tag == '{http://www.opengis.net/ogc}PropertyIsLessThan':
                    co = '<'
                elif c.tag == '{http://www.opengis.net/ogc}PropertyIsGreaterThan':
                    co = '>'
                elif c.tag == '{http://www.opengis.net/ogc}PropertyIsLessThanOrEqualTo':
                    co = '<='
                elif c.tag == '{http://www.opengis.net/ogc}PropertyIsGreaterThanOrEqualTo':
                    co = '>='
                elif c.tag == '{http://www.opengis.net/ogc}PropertyIsLike':
                    co = 'like'
                elif c.tag == '{http://www.opengis.net/ogc}PropertyIsNull':
                    co = 'is null'
    
                # if this is a case insensitive search, then set the LIKE comparison operator
                if matchcase is not None and matchcase == 'false':
                    co = 'like'
    
                #self.where = '%s %s "%s"' % (pname,co,pvalue)
                if self.boq == ' not ':
                    queries.append('not %s %s "%s"' % (pname,co,pvalue))
                else:
                    queries.append('%s %s "%s"' % (pname,co,pvalue))

            if c.tag == '{http://www.opengis.net/ogc}PropertyIsBetween':
                co = 'between'
                lb = c.find('{http://www.opengis.net/ogc}LowerBoundary/{http://www.opengis.net/ogc}Literal').text
                ub = c.find('{http://www.opengis.net/ogc}UpperBoundary/{http://www.opengis.net/ogc}Literal').text
                #self.where = '%s and "%s"' % (lb, ub)
                queries.append('%s and "%s"' % (lb, ub))

        if self.boq is not None and self.boq != ' not ':
            self.where = self.boq.join(queries)
        else:
            self.where = queries[0]



















