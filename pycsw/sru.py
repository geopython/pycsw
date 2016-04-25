# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
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

from pycsw.core import util
from pycsw.core.etree import etree
from pycsw.ogc.fes import fes1


class Sru(object):
    """SRU wrapper class"""
    def __init__(self, context):
        self.sru_version = '1.1'

        self.namespaces = {
            'zd': 'http://www.loc.gov/zing/srw/diagnostic/',
            'sru': 'http://www.loc.gov/zing/srw/',
            'zr': 'http://explain.z3950.org/dtd/2.1/',
            'zs': 'http://www.loc.gov/zing/srw/',
            'srw_dc': 'info:srw/schema/1/dc-schema'
        }

        self.mappings = {
            'csw:Record': {
                'schema': {
                    'name': 'dc',
                    'identifier': 'info:srw/cql-context-set/1/dc-v1.1',
                },
                'index': {
                    # map OGC queryables to XPath expressions
                    'title': '4',
                    'creator': '1003',
                    'subject': '29',
                    'abstract': '62',
                    'publisher': '1018',
                    'contributor': 'TBD',
                    'modified': 'TBD',
                    'date': '30',
                    'type': '1031',
                    'format': '1034',
                    'identifier': '12',
                    'source': 'TBD',
                    'language': 'TBD',
                    'relation': 'TBD',
                    'rights': 'TBD',
                    # bbox and full text map to internal fixed columns
                    #'ows:BoundingBox': 'bbox',
                    #'csw:AnyText': 'xml'
                }
            }
        }

        self.context = context
        self.context.namespaces.update(self.namespaces)

    def request_sru2csw(self, kvpin):
        """transform an SRU request into a CSW request"""

        kvpout = {'service': 'CSW', 'version': '2.0.2', 'mode': 'sru'}

        if 'operation' in kvpin:
            if kvpin['operation'] == 'explain':
                kvpout['request'] = 'GetCapabilities'
            elif kvpin['operation'] == 'searchRetrieve':
                kvpout['request'] = 'GetRecords'
                if 'startrecord' in kvpin:
                    kvpout['startposition'] = int(kvpin['startrecord'])
                if 'maximumrecords' in kvpin:
                    kvpout['maxrecords'] = int(kvpin['maximumrecords'])
                else:
                    kvpout['maxrecords'] = 0

                # TODO: make smarter typename fetching
                kvpout['typenames'] = 'csw:Record'
                kvpout['elementsetname'] = 'brief'
                kvpout['constraintlanguage'] = 'CQL_TEXT'
                kvpout['resulttype'] = 'results'

                if 'query' in kvpin:
                    pname_in_query = False
                    for coops in fes1.MODEL['ComparisonOperators'].keys():
                        if kvpin['query'].find(fes1.MODEL['ComparisonOperators'][coops]['opvalue']) != -1:
                            pname_in_query = True
                            break

                    kvpout['constraint'] = {'type': 'cql'}

                    if not pname_in_query:
                        kvpout['constraint'] = 'csw:AnyText like \'%%%s%%\'' % kvpin['query']
                    else:
                        kvpout['constraint'] = kvpin['query']
        else:
            kvpout['request'] = 'GetCapabilities'

        return kvpout

    def response_csw2sru(self, element, environ):
        """transform a CSW response into an SRU response"""

        if util.xmltag_split(element.tag) == 'Capabilities':  # explain
            node = etree.Element(util.nspath_eval('sru:explainResponse', self.namespaces), nsmap=self.namespaces)

            etree.SubElement(node, util.nspath_eval('sru:version', self.namespaces)).text = self.sru_version

            record = etree.SubElement(node, util.nspath_eval('sru:record', self.namespaces))

            etree.SubElement(record, util.nspath_eval('sru:recordPacking', self.namespaces)).text = 'XML'
            etree.SubElement(record, util.nspath_eval('sru:recordSchema', self.namespaces)).text = 'http://explain.z3950.org/dtd/2.1/'

            recorddata = etree.SubElement(record, util.nspath_eval('sru:recordData', self.namespaces))

            explain = etree.SubElement(recorddata, util.nspath_eval('zr:explain', self.namespaces))

            serverinfo = etree.SubElement(explain, util.nspath_eval('zr:serverInfo', self.namespaces), protocol='SRU', version=self.sru_version, transport='http', method='GET POST SOAP')

            etree.SubElement(serverinfo, util.nspath_eval('zr:host', self.namespaces)).text = environ.get('HTTP_HOST', environ["SERVER_NAME"])  # WSGI allows for either of these
            etree.SubElement(serverinfo, util.nspath_eval('zr:port', self.namespaces)).text = environ['SERVER_PORT']
            etree.SubElement(serverinfo, util.nspath_eval('zr:database', self.namespaces)).text = 'pycsw'

            databaseinfo = etree.SubElement(explain, util.nspath_eval('zr:databaseInfo', self.namespaces))

            etree.SubElement(databaseinfo, util.nspath_eval('zr:title', self.namespaces), lang='en', primary='true').text = element.xpath('//ows:Title|//ows20:Title', namespaces=self.context.namespaces)[0].text
            etree.SubElement(databaseinfo, util.nspath_eval('zr:description', self.namespaces), lang='en', primary='true').text = element.xpath('//ows:Abstract|//ows20:Abstract', namespaces=self.context.namespaces)[0].text

            indexinfo = etree.SubElement(explain, util.nspath_eval('zr:indexInfo', self.namespaces))
            etree.SubElement(indexinfo, util.nspath_eval('zr:set', self.namespaces), name='dc', identifier='info:srw/cql-context-set/1/dc-v1.1')

            for key, value in sorted(self.mappings['csw:Record']['index'].items()):
                zrindex = etree.SubElement(indexinfo, util.nspath_eval('zr:index', self.namespaces), id=value)
                etree.SubElement(zrindex, util.nspath_eval('zr:title', self.namespaces)).text = key
                zrmap = etree.SubElement(zrindex, util.nspath_eval('zr:map', self.namespaces))
                etree.SubElement(zrmap, util.nspath_eval('zr:map', self.namespaces), set='dc').text = key

            zrindex = etree.SubElement(indexinfo, util.nspath_eval('zr:index', self.namespaces))
            zrmap = etree.SubElement(zrindex, util.nspath_eval('zr:map', self.namespaces))
            etree.SubElement(zrmap, util.nspath_eval('zr:name', self.namespaces), set='dc').text = 'title222'

            schemainfo = etree.SubElement(explain, util.nspath_eval('zr:schemaInfo', self.namespaces))
            zrschema = etree.SubElement(schemainfo, util.nspath_eval('zr:schema', self.namespaces), name='dc', identifier='info:srw/schema/1/dc-v1.1')
            etree.SubElement(zrschema, util.nspath_eval('zr:title', self.namespaces)).text = 'Simple Dublin Core'

            configinfo = etree.SubElement(explain, util.nspath_eval('zr:configInfo', self.namespaces))
            etree.SubElement(configinfo, util.nspath_eval('zr:default', self.namespaces), type='numberOfRecords').text = '0'

        elif util.xmltag_split(element.tag) == 'GetRecordsResponse':

            recpos = int(element.xpath('//@nextRecord')[0]) - int(element.xpath('//@numberOfRecordsReturned')[0])

            node = etree.Element(util.nspath_eval('zs:searchRetrieveResponse', self.namespaces), nsmap=self.namespaces)
            etree.SubElement(node, util.nspath_eval('zs:version', self.namespaces)).text = self.sru_version
            etree.SubElement(node, util.nspath_eval('zs:numberOfRecords', self.namespaces)).text = element.xpath('//@numberOfRecordsMatched')[0]

            for rec in element.xpath('//csw:BriefRecord', namespaces=self.context.namespaces):
                record = etree.SubElement(node, util.nspath_eval('zs:record', self.namespaces))
                etree.SubElement(node, util.nspath_eval('zs:recordSchema', self.namespaces)).text = 'info:srw/schema/1/dc-v1.1'
                etree.SubElement(node, util.nspath_eval('zs:recordPacking', self.namespaces)).text = 'xml'

                recorddata = etree.SubElement(record, util.nspath_eval('zs:recordData', self.namespaces))
                rec.tag = util.nspath_eval('srw_dc:srw_dc', self.namespaces)
                recorddata.append(rec)

                etree.SubElement(record, util.nspath_eval('zs:recordPosition', self.namespaces)).text = str(recpos)
                recpos += 1

        elif util.xmltag_split(element.tag) == 'ExceptionReport':
            node = self.exceptionreport2diagnostic(element)
        return node

    def exceptionreport2diagnostic(self, element):
        """transform a CSW exception into an SRU diagnostic"""
        node = etree.Element(
            util.nspath_eval('zs:searchRetrieveResponse', self.namespaces), nsmap=self.namespaces)

        etree.SubElement(node, util.nspath_eval('zs:version', self.namespaces)).text = self.sru_version

        diagnostics = etree.SubElement(node, util.nspath_eval('zs:diagnostics', self.namespaces))

        diagnostic = etree.SubElement(
            diagnostics, util.nspath_eval('zs:diagnostic', self.namespaces))

        etree.SubElement(diagnostic, util.nspath_eval('zd:diagnostic', self.namespaces)).text = \
            'info:srw/diagnostic/1/7'

        etree.SubElement(diagnostic, util.nspath_eval('zd:message', self.namespaces)).text = \
            element.xpath('//ows:Exception/ows:ExceptionText|//ows20:Exception/ows20:ExceptionText', namespaces=self.context.namespaces)[0].text

        etree.SubElement(diagnostic, util.nspath_eval('zd:details', self.namespaces)).text = \
            element.xpath('//ows:Exception|//ows20:Exception', namespaces=self.context.namespaces)[0].attrib.get('exceptionCode')

        return node
