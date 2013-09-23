# -*- coding: iso-8859-15 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
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

from lxml import etree
from pycsw import util

class OpenSearch(object):
    """OpenSearch wrapper class"""

    def __init__(self, context):
        """initialize"""

        self.namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'
        }

        self.context = context
        self.context.namespaces.update(self.namespaces)

    def response_csw2opensearch(self, element, cfg):
        """transform a CSW response into an OpenSearch response"""

        if util.xmltag_split(element.tag) == 'GetRecordsResponse':

            startindex = int(element.xpath('//@nextRecord')[0]) - int(element.xpath('//@numberOfRecordsReturned')[0])
            if startindex < 1:
                startindex = 1

            node = etree.Element(util.nspath_eval('atom:feed', self.context.namespaces), nsmap=self.namespaces)
            etree.SubElement(node, util.nspath_eval('atom:id', self.context.namespaces)).text = cfg.get('server', 'url')
            etree.SubElement(node, util.nspath_eval('atom:title', self.context.namespaces)).text = cfg.get('metadata:main', 'identification_title')
            #etree.SubElement(node, util.nspath_eval('atom:updated', self.context.namespaces)).text = element.xpath('//@timestamp')[0]

            etree.SubElement(node, util.nspath_eval('opensearch:totalResults', self.context.namespaces)).text = element.xpath('//@numberOfRecordsMatched')[0]
            etree.SubElement(node, util.nspath_eval('opensearch:startIndex', self.context.namespaces)).text = str(startindex)
            etree.SubElement(node, util.nspath_eval('opensearch:itemsPerPage', self.context.namespaces)).text = element.xpath('//@numberOfRecordsReturned')[0]

            for rec in element.xpath('//atom:entry', namespaces=self.context.namespaces):
                node.append(rec)

        return node
