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

import six
import logging
from pycsw.core import util
from pycsw.core.etree import etree

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
        self.context.namespaces.update(self.namespaces)

    def response_csw2opensearch(self, element, cfg):
        """transform a CSW response into an OpenSearch response"""

        root_tag = etree.QName(element).localname
        if root_tag == 'ExceptionReport':
            return element

        LOGGER.debug('RESPONSE: %s', root_tag)
        try:
            version = element.xpath('//@version')[0]
        except Exception as err:
            version = '3.0.0'

        self.exml = element
        self.cfg = cfg
        self.bind_url = util.bind_url(self.cfg.get('server', 'url'))

        if version == '2.0.2':
            return self._csw2_2_os()
        elif version == '3.0.0':
            return self._csw3_2_os()

    def _csw2_2_os(self):
        """CSW 2.0.2 Capabilities to OpenSearch Description"""

        operation_name = etree.QName(self.exml).localname
        if operation_name == 'GetRecordsResponse':

            startindex = int(self.exml.xpath('//@nextRecord')[0]) - int(
                        self.exml.xpath('//@numberOfRecordsReturned')[0])
            if startindex < 1:
                startindex = 1

            node = etree.Element(util.nspath_eval('atom:feed',
                       self.context.namespaces), nsmap=self.namespaces)
            etree.SubElement(node, util.nspath_eval('atom:id',
                       self.context.namespaces)).text = self.cfg.get('server', 'url')
            etree.SubElement(node, util.nspath_eval('atom:title',
                       self.context.namespaces)).text = self.cfg.get('metadata:main',
                       'identification_title')
            #etree.SubElement(node, util.nspath_eval('atom:updated',
            #  self.context.namespaces)).text = self.exml.xpath('//@timestamp')[0]

            etree.SubElement(node, util.nspath_eval('os:totalResults',
                        self.context.namespaces)).text = self.exml.xpath(
                        '//@numberOfRecordsMatched')[0]
            etree.SubElement(node, util.nspath_eval('os:startIndex',
                        self.context.namespaces)).text = str(startindex)
            etree.SubElement(node, util.nspath_eval('os:itemsPerPage',
                        self.context.namespaces)).text = self.exml.xpath(
                        '//@numberOfRecordsReturned')[0]

            for rec in self.exml.xpath('//atom:entry',
                        namespaces=self.context.namespaces):
                node.append(rec)
        elif operation_name == 'Capabilities':
            node = etree.Element(util.nspath_eval('os:OpenSearchDescription', self.namespaces), nsmap=self.namespaces)
            etree.SubElement(node, util.nspath_eval('os:ShortName', self.namespaces)).text = self.exml.xpath('//ows:Title', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, util.nspath_eval('os:LongName', self.namespaces)).text = self.exml.xpath('//ows:Title', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, util.nspath_eval('os:Description', self.namespaces)).text = self.exml.xpath('//ows:Abstract', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, util.nspath_eval('os:Tags', self.namespaces)).text = ' '.join(x.text for x in self.exml.xpath('//ows:Keyword', namespaces=self.context.namespaces))

            node1 = etree.SubElement(node, util.nspath_eval('os:Url', self.namespaces))
            node1.set('type', 'application/atom+xml')
            node1.set('method', 'get')
            node1.set('template', '%smode=opensearch&service=CSW&version=2.0.2&request=GetRecords&elementsetname=full&typenames=csw:Record&resulttype=results&q={searchTerms?}&bbox={geo:box?}&time={time:start?}/{time:end?}&startposition={startIndex?}&maxrecords={count?}' % self.bind_url)

            node1 = etree.SubElement(node, util.nspath_eval('os:Image', self.namespaces))
            node1.set('type', 'image/vnd.microsoft.icon')
            node1.set('width', '16')
            node1.set('height', '16')
            node1.text = 'http://pycsw.org/img/favicon.ico'

            etree.SubElement(node, util.nspath_eval('os:Developer', self.namespaces)).text = self.exml.xpath('//ows:IndividualName', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, util.nspath_eval('os:Context', self.namespaces)).text = self.exml.xpath('//ows:ElectronicMailAddress', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, util.nspath_eval('os:Attribution', self.namespaces)).text = self.exml.xpath('//ows:ProviderName', namespaces=self.context.namespaces)[0].text
        elif operation_name == 'ExceptionReport':
            node = self.exml
        else:  # return Description document
            node = etree.Element(util.nspath_eval('os:Description', self.context.namespaces))

        return node

    def _csw3_2_os(self):
        """CSW 3.0.0 Capabilities to OpenSearch Description"""

        response_name = etree.QName(self.exml).localname
        if response_name == 'GetRecordsResponse':

            startindex = int(self.exml.xpath('//@nextRecord')[0]) - int(
                        self.exml.xpath('//@numberOfRecordsReturned')[0])
            if startindex < 1:
                startindex = 1

            node = etree.Element(util.nspath_eval('atom:feed',
                       self.context.namespaces), nsmap=self.namespaces)
            etree.SubElement(node, util.nspath_eval('atom:id',
                       self.context.namespaces)).text = self.cfg.get('server', 'url')
            etree.SubElement(node, util.nspath_eval('atom:title',
                       self.context.namespaces)).text = self.cfg.get('metadata:main',
                       'identification_title')
            author = etree.SubElement(node, util.nspath_eval('atom:author', self.context.namespaces))
            etree.SubElement(author, util.nspath_eval('atom:name', self.context.namespaces)).text = self.cfg.get('metadata:main',
                       'provider_name')
            etree.SubElement(node, util.nspath_eval('atom:link',
                       self.context.namespaces), rel='search',
                           type='application/opensearchdescription+xml',
                           href='%smode=opensearch&service=CSW&version=3.0.0&request=GetCapabilities' % self.bind_url)

            etree.SubElement(node, util.nspath_eval('atom:updated',
                self.context.namespaces)).text = self.exml.xpath('//@timestamp')[0]

            etree.SubElement(node, util.nspath_eval('os:Query', self.context.namespaces), role='request')

            etree.SubElement(node, util.nspath_eval('os:totalResults',
                        self.context.namespaces)).text = self.exml.xpath(
                        '//@numberOfRecordsMatched')[0]
            etree.SubElement(node, util.nspath_eval('os:startIndex',
                        self.context.namespaces)).text = str(startindex)
            etree.SubElement(node, util.nspath_eval('os:itemsPerPage',
                        self.context.namespaces)).text = self.exml.xpath(
                        '//@numberOfRecordsReturned')[0]

            for rec in self.exml.xpath('//atom:entry',
                        namespaces=self.context.namespaces):
                node.append(rec)
        elif response_name == 'Capabilities':
            node = etree.Element(util.nspath_eval('os:OpenSearchDescription', self.namespaces), nsmap=self.namespaces)
            etree.SubElement(node, util.nspath_eval('os:ShortName', self.namespaces)).text = self.exml.xpath('//ows20:Title', namespaces=self.context.namespaces)[0].text[:16]
            etree.SubElement(node, util.nspath_eval('os:LongName', self.namespaces)).text = self.exml.xpath('//ows20:Title', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, util.nspath_eval('os:Description', self.namespaces)).text = self.exml.xpath('//ows20:Abstract', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, util.nspath_eval('os:Tags', self.namespaces)).text = ' '.join(x.text for x in self.exml.xpath('//ows20:Keyword', namespaces=self.context.namespaces))

            # Requirement-022
            node1 = etree.SubElement(node, util.nspath_eval('os:Url', self.namespaces))
            node1.set('type', 'application/xml')
            node1.set('template', '%sservice=CSW&version=3.0.0&request=GetRecords&elementsetname=full&typenames=csw:Record&resulttype=results&q={searchTerms?}&bbox={geo:box?}&time={time:start?}/{time:end?}&outputformat=application/xml&outputschema=http://www.opengis.net/cat/csw/3.0&startposition={startIndex?}&maxrecords={count?}&recordids={geo:uid}' % self.bind_url)

            # Requirement-023
            node1 = etree.SubElement(node, util.nspath_eval('os:Url', self.namespaces))
            node1.set('type', 'application/atom+xml')
            node1.set('template', '%smode=opensearch&service=CSW&version=3.0.0&request=GetRecords&elementsetname=full&typenames=csw:Record&resulttype=results&q={searchTerms?}&bbox={geo:box?}&time={time:start?}/{time:end?}&outputformat=application/atom%%2Bxml&startposition={startIndex?}&maxrecords={count?}&recordids={geo:uid}' % self.bind_url)

            node1 = etree.SubElement(node, util.nspath_eval('os:Image', self.namespaces))
            node1.set('type', 'image/vnd.microsoft.icon')
            node1.set('width', '16')
            node1.set('height', '16')
            node1.text = 'http://pycsw.org/img/favicon.ico'

            os_query = etree.SubElement(node, util.nspath_eval('os:Query', self.namespaces), role='example')
            os_query.attrib[util.nspath_eval('geo:box', self.namespaces)] = '-180,-90,180,90'

            etree.SubElement(node, util.nspath_eval('os:Developer', self.namespaces)).text = self.exml.xpath('//ows20:IndividualName', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, util.nspath_eval('os:Contact', self.namespaces)).text = self.exml.xpath('//ows20:ElectronicMailAddress', namespaces=self.context.namespaces)[0].text
            etree.SubElement(node, util.nspath_eval('os:Attribution', self.namespaces)).text = self.exml.xpath('//ows20:ProviderName', namespaces=self.context.namespaces)[0].text
        elif response_name == 'ExceptionReport':
            node = self.exml
        else:  # GetRecordById output
            node = etree.Element(util.nspath_eval('atom:feed',
                       self.context.namespaces), nsmap=self.namespaces)
            etree.SubElement(node, util.nspath_eval('atom:id',
                       self.context.namespaces)).text = self.cfg.get('server', 'url')
            etree.SubElement(node, util.nspath_eval('atom:title',
                       self.context.namespaces)).text = self.cfg.get('metadata:main',
                       'identification_title')
            #etree.SubElement(node, util.nspath_eval('atom:updated',
            #  self.context.namespaces)).text = self.exml.xpath('//@timestamp')[0]

            etree.SubElement(node, util.nspath_eval('os:totalResults',
                        self.context.namespaces)).text = '1'
            etree.SubElement(node, util.nspath_eval('os:startIndex',
                        self.context.namespaces)).text = '1'
            etree.SubElement(node, util.nspath_eval('os:itemsPerPage',
                        self.context.namespaces)).text = '1'

            for rec in self.exml.xpath('//atom:entry', namespaces=self.context.namespaces):
                #node.append(rec)
                node = rec
        return node


def kvp2filterxml(kvp, context):
    ''' transform kvp to filter XML string '''

    bbox_element = None
    time_element = None
    anytext_elements = []

    # Count parameters
    par_count = 0
    for p in ['q','bbox','time']:
        if p in kvp and kvp[p] != '':
            par_count += 1

    # Create root element for FilterXML
    root = etree.Element(util.nspath_eval('ogc:Filter', context.namespaces))

    # bbox to FilterXML
    if 'bbox' in kvp and kvp['bbox'] != '':
        LOGGER.debug('Detected bbox parameter')
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

        if len(bbox_list) == 5:  # add srsName
            LOGGER.debug('Found CRS')
            env.attrib['srsName'] = bbox_list[4]
        else:
            LOGGER.debug('Assuming 4326')
            env.attrib['srsName'] = 'urn:ogc:def:crs:OGC:1.3:CRS84'
            if not validate_4326(bbox_list):
                msg = '4326 coordinates out of range: %s' % bbox_list
                LOGGER.error(msg)
                raise RuntimeError(msg)

        try:
            el.text = "%s %s" % (bbox_list[0], bbox_list[1])
        except Exception as err:
            errortext = 'Exception: OpenSearch bbox not valid.\nError: %s.' % str(err)
            LOGGER.exception(errortext)
        env.append(el)
        el = etree.Element(util.nspath_eval('gml:upperCorner',
                    context.namespaces))
        try:
            el.text = "%s %s" % (bbox_list[2], bbox_list[3])
        except Exception as err:
            errortext = 'Exception: OpenSearch bbox not valid.\nError: %s.' % str(err)
            LOGGER.exception(errortext)
        env.append(el)
        bbox_element.append(env)

    # q to FilterXML
    if 'q' in kvp and kvp['q'] != '':
        LOGGER.debug('Detected q parameter')
        qvals = kvp['q'].split()
        LOGGER.debug(qvals)
        if len(qvals) > 1:
            par_count += 1
        for qval in qvals:
            LOGGER.debug('processing q token')
            anytext_element = etree.Element(util.nspath_eval('ogc:PropertyIsEqualTo',
                        context.namespaces))
            el = etree.Element(util.nspath_eval('ogc:PropertyName',
                        context.namespaces))
            el.text = 'csw:AnyText'
            anytext_element.append(el)
            el = etree.Element(util.nspath_eval('ogc:Literal',
                        context.namespaces))
            if six.PY2:
                el.text = qval.decode('utf8')
            else:
                el.text = qval
            anytext_element.append(el)
            anytext_elements.append(anytext_element)

    # time to FilterXML
    if 'time' in kvp and kvp['time'] != '':
        LOGGER.debug('Detected time parameter %s', kvp['time'])
        time_list = kvp['time'].split("/")
        if (len(time_list) == 2):
            LOGGER.debug('TIMELIST: %s', time_list)
            # This is a normal request
            if '' not in time_list:
                LOGGER.debug('Both dates present')
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
                if time_list == ['', '']:
                    par_count -= 1
                # One of two is empty
                elif time_list[1] is '':
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
            LOGGER.error(errortext)

    if par_count == 0:
        return ''
    elif par_count == 1:
        LOGGER.debug('Single predicate filter')
        # Only one OpenSearch parameter exists
        if 'bbox' in kvp and kvp['bbox'] != '':
            LOGGER.debug('Adding bbox')
            root.append(bbox_element)
        elif time_element is not None:
            LOGGER.debug('Adding time')
            root.append(time_element)
        elif anytext_elements:
            LOGGER.debug('Adding anytext')
            root.extend(anytext_elements)
    elif (par_count > 1):
        LOGGER.debug('ogc:And query (%d predicates)', par_count)
        # Since more than 1 parameter, append the AND logical operator
        logical_and = etree.Element(util.nspath_eval('ogc:And',
                context.namespaces))
        if bbox_element is not None:
            logical_and.append(bbox_element)
        if time_element is not None:
            logical_and.append(time_element)
        if anytext_elements is not None:
            logical_and.extend(anytext_elements)
        root.append(logical_and)

    # Render etree to string XML
    LOGGER.debug(etree.tostring(root, encoding='unicode'))
    return etree.tostring(root, encoding='unicode')


def validate_4326(bbox_list):
    """Helper function to validate 4326."""
    is_valid = False
    if ((-180.0 <= float(bbox_list[0]) <= 180.0) and
            (-90.0 <= float(bbox_list[1]) <= 90.0) and
            (-180.0 <= float(bbox_list[2]) <= 180.0) and
            (-90.0 <= float(bbox_list[3]) <= 90.0)):
        is_valid = True
    return is_valid
