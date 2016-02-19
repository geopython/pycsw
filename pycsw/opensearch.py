# -*- coding: iso-8859-15 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2014 Tom Kralidis, Angelos Tzotsos
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
import logging

LOGGER = logging.getLogger(__name__)

class OpenSearch(object):
    """OpenSearch wrapper class"""

    def __init__(self, context):
        """initialize"""

        self.namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'geo': 'http://a9.com/-/opensearch/extensions/geo/1.0/',
            'os': 'http://a9.com/-/spec/opensearch/1.1/',
            'time': 'http://a9.com/-/opensearch/extensions/time/1.0/'
        }

        self.context = context
        #self.context.namespaces.update(self.namespaces)

    def response_csw2opensearch(self, element, cfg):
        """transform a CSW response into an OpenSearch response"""

        root_tag = util.xmltag_split(element.tag)
        if root_tag == 'ExceptionReport':
            return element

        LOGGER.debug('RESPONSE: %s', root_tag)

        if util.xmltag_split(element.tag) == 'GetRecordsResponse':

            startindex = int(element.xpath('//@nextRecord')[0]) - int(
                        element.xpath('//@numberOfRecordsReturned')[0])
            if startindex < 1:
                startindex = 1

            node = etree.Element(util.nspath_eval('atom:feed',
                       self.context.namespaces), nsmap=self.namespaces)
            etree.SubElement(node, util.nspath_eval('atom:id',
                       self.context.namespaces)).text = cfg.get('server', 'url')
            etree.SubElement(node, util.nspath_eval('atom:title',
                       self.context.namespaces)).text = cfg.get('metadata:main',
                       'identification_title')
            #etree.SubElement(node, util.nspath_eval('atom:updated',
            #  self.context.namespaces)).text = element.xpath('//@timestamp')[0]

            etree.SubElement(node, util.nspath_eval('os:totalResults',
                        self.context.namespaces)).text = element.xpath(
                        '//@numberOfRecordsMatched')[0]
            etree.SubElement(node, util.nspath_eval('os:startIndex',
                        self.context.namespaces)).text = str(startindex)
            etree.SubElement(node, util.nspath_eval('os:itemsPerPage',
                        self.context.namespaces)).text = element.xpath(
                        '//@numberOfRecordsReturned')[0]

            for rec in element.xpath('//atom:entry',
                        namespaces=self.context.namespaces):
                node.append(rec)
        elif util.xmltag_split(element.tag) == 'Capabilities':
            node = etree.Element('OpenSearchDescription', nsmap={None: self.namespaces['os']})
            etree.SubElement(node, 'ShortName').text = element.xpath('//ows:Title', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, 'LongName').text = element.xpath('//ows:Title', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, 'Description').text = element.xpath('//ows:Abstract', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, 'Tags').text = ' '.join(x.text for x in element.xpath('//ows:Keyword', namespaces=self.context.namespaces))

            node1 = etree.SubElement(node, 'Url')
            node1.set('type', 'application/atom+xml')
            node1.set('method', 'get')
            node1.set('template', '%s?mode=opensearch&service=CSW&version=2.0.2&request=GetRecords&elementsetname=full&typenames=csw:Record&resulttype=results&q={searchTerms?}&bbox={geo:box?}&time={time:start?}/{time:end?}&startposition={startIndex?}&maxrecords={count?}' % element.xpath('//ows:Get/@xlink:href', namespaces=self.context.namespaces)[0])

            node1 = etree.SubElement(node, 'Image')
            node1.set('type', 'image/vnd.microsoft.icon')
            node1.set('width', '16')
            node1.set('height', '16')
            node1.text = 'http://pycsw.org/img/favicon.ico'

            etree.SubElement(node, 'Developer').text = element.xpath('//ows:IndividualName', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, 'Contact').text = element.xpath('//ows:ElectronicMailAddress', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, 'Attribution').text = element.xpath('//ows:ProviderName', namespaces=self.context.namespaces)[0].text
        elif util.xmltag_split(element.tag) == 'ExceptionReport':
            node = element
        else:  # return Description document
            node = etree.Element(util.nspath_eval('os:Description', self.context.namespaces))

        return node


def kvp2filterxml(kvp, context):

    filter_xml = ""
    valid_xml = ""

    # Count parameters
    par_count = 0
    for p in ['q','bbox','time']:
        if p in kvp:
            par_count += 1

    # Create root element for FilterXML
    root = etree.Element(util.nspath_eval('ogc:Filter',
                context.namespaces))

    # bbox to FilterXML
    if 'bbox' in kvp:
        bbox_list = [x.strip() for x in kvp['bbox'].split(',')]
        bbox_element = etree.Element(util.nspath_eval('ogc:BBOX',
                    context.namespaces))
        el = etree.Element(util.nspath_eval('ogc:PropertyName',
                    context.namespaces))
        el.text = 'ows:BoundingBox'
        bbox_element.append(el)
        env = etree.Element(util.nspath_eval('gml:Envelope',
                    context.namespaces))
        el = etree.Element(util.nspath_eval('gml:lowerCorner',
                    context.namespaces))
        try:
            el.text = "%s %s" % (bbox_list[0], bbox_list[1])
        except Exception as err:
            errortext = 'Exception: OpenSearch bbox not valid.\nError: %s.' % str(err)
            LOGGER.debug(errortext)
        env.append(el)
        el = etree.Element(util.nspath_eval('gml:upperCorner',
                    context.namespaces))
        try:
            el.text = "%s %s" % (bbox_list[2], bbox_list[3])
        except Exception as err:
            errortext = 'Exception: OpenSearch bbox not valid.\nError: %s.' % str(err)
            LOGGER.debug(errortext)
        env.append(el)
        bbox_element.append(env)

    # q to FilterXML
    if 'q' in kvp:
        anytext_element = etree.Element(util.nspath_eval('ogc:PropertyIsEqualTo',
                    context.namespaces))
        el = etree.Element(util.nspath_eval('ogc:PropertyName',
                    context.namespaces))
        el.text = 'csw:AnyText'
        anytext_element.append(el)
        el = etree.Element(util.nspath_eval('ogc:Literal',
                    context.namespaces))
        el.text = kvp['q']
        anytext_element.append(el)

    # time to FilterXML
    if 'time' in kvp:
        time_list = kvp['time'].split("/")
        time_element = None
        if (len(time_list) == 2):
            # This is a normal request
            if '' not in time_list:
                # Both dates are present
                time_element = etree.Element(util.nspath_eval('ogc:PropertyIsBetween',
                            context.namespaces))
                el = etree.Element(util.nspath_eval('ogc:PropertyName',
                            context.namespaces))
                el.text = 'dc:date'
                time_element.append(el)
                el = etree.Element(util.nspath_eval('ogc:LowerBoundary',
                            context.namespaces))
                el2 = etree.Element(util.nspath_eval('ogc:Literal',
                            context.namespaces))
                el2.text = time_list[0]
                el.append(el2)
                time_element.append(el)
                el = etree.Element(util.nspath_eval('ogc:UpperBoundary',
                            context.namespaces))
                el2 = etree.Element(util.nspath_eval('ogc:Literal',
                            context.namespaces))
                el2.text = time_list[1]
                el.append(el2)
                time_element.append(el)
            else:
                # One of two is empty
                if time_list[1] is '':
                    time_element = etree.Element(util.nspath_eval('ogc:PropertyIsGreaterThanOrEqualTo',
                                context.namespaces))
                    el = etree.Element(util.nspath_eval('ogc:PropertyName',
                                context.namespaces))
                    el.text = 'dc:date'
                    time_element.append(el)
                    el = etree.Element(util.nspath_eval('ogc:Literal',
                                context.namespaces))
                    el.text = time_list[0]
                    time_element.append(el)
                else:
                    time_element = etree.Element(util.nspath_eval('ogc:PropertyIsLessThanOrEqualTo',
                                context.namespaces))
                    el = etree.Element(util.nspath_eval('ogc:PropertyName',
                                context.namespaces))
                    el.text = 'dc:date'
                    time_element.append(el)
                    el = etree.Element(util.nspath_eval('ogc:Literal',
                                context.namespaces))
                    el.text = time_list[1]
                    time_element.append(el)
        elif ((len(time_list) == 1) and ('' not in time_list)):
            # This is an equal request
            time_element = etree.Element(util.nspath_eval('ogc:PropertyIsEqualTo',
                        context.namespaces))
            el = etree.Element(util.nspath_eval('ogc:PropertyName',
                        context.namespaces))
            el.text = 'dc:date'
            time_element.append(el)
            el = etree.Element(util.nspath_eval('ogc:Literal',
                        context.namespaces))
            el.text = time_list[0]
            time_element.append(el)
        else:
            # Error
            errortext = 'Exception: OpenSearch time not valid: %s.' % str(kvp['time'])
            LOGGER.debug(errortext)

    if (par_count == 1):
        # Only one OpenSearch parameter exists
        if 'bbox' in kvp:
            root.append(bbox_element)
        elif 'time' in kvp:
            root.append(time_element)
        elif 'q' in kvp:
            root.append(anytext_element)
    elif (par_count > 1):
        # Since more than 1 parameter, append the AND logical operator
        logical_and = etree.Element(util.nspath_eval('ogc:And',
                context.namespaces))
        if 'bbox' in kvp:
            logical_and.append(bbox_element)
        if 'time' in kvp:
            logical_and.append(time_element)
        if 'q' in kvp:
            logical_and.append(anytext_element)
        root.append(logical_and)

    # Render etree to string XML
    return etree.tostring(root)
