# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2012 Tom Kralidis
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

import os
import uuid
from lxml import etree
import config, fes, util

OPENSEARCH_VERSION = '1.1'

NAMESPACES = {
    'atom': 'http://www.w3.org/2005/Atom',
    'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'
}

config.NAMESPACES.update(NAMESPACES)

def response_csw2opensearch(element, cfg):
    ''' transform a CSW response into an OpenSearch response '''

    if util.xmltag_split(element.tag) == 'GetRecordsResponse':

        startindex = int(element.xpath('//@nextRecord')[0]) - int(element.xpath('//@numberOfRecordsReturned')[0])
        if startindex < 1:
            startindex = 1

        node = etree.Element(util.nspath_eval('atom:feed'), nsmap=NAMESPACES)
        etree.SubElement(node, util.nspath_eval('atom:id')).text = cfg.get('server', 'url')
        etree.SubElement(node, util.nspath_eval('atom:title')).text = cfg.get('metadata:main', 'identification_title')
        #etree.SubElement(node, util.nspath_eval('atom:updated')).text = element.xpath('//@timestamp')[0]
        
        etree.SubElement(node, util.nspath_eval('opensearch:totalResults')).text = element.xpath('//@numberOfRecordsMatched')[0]
        etree.SubElement(node, util.nspath_eval('opensearch:startIndex')).text = str(startindex)
        etree.SubElement(node, util.nspath_eval('opensearch:itemsPerPage')).text = element.xpath('//@numberOfRecordsReturned')[0]

        for rec in element.xpath('//atom:entry', namespaces=config.NAMESPACES):
            node.append(rec)

    return node
