# -*- coding: iso-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2011 Tom Kralidis
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
import config, fes, util

class SruStaticContext(object):
    def __init__(self, staticcontext):
        self.SRU_VERSION = '1.1'

        self.NAMESPACES = {
            'zd': 'http://www.loc.gov/zing/srw/diagnostic/',
            'sru': 'http://www.loc.gov/zing/srw/',
            'zr': 'http://explain.z3950.org/dtd/2.1/',
            'zs': 'http://www.loc.gov/zing/srw/',
            'srw_dc': 'info:srw/schema/1/dc-schema'
            }

        self.MAPPINGS = {
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


class Sru(object):
    def __init__(self, staticcontext):
        self.globalstaticcontext = staticcontext
        self.staticcontext = SruStaticContext(self.globalstaticcontext)

        staticcontext.NAMESPACES.update(self.staticcontext.NAMESPACES)

    def nspath_eval(self, astr):
        return util.nspath_eval(astr, self.globalstaticcontext)

    def request_sru2csw(self, kvpin, typenames):
        ''' transform an SRU request into a CSW request '''

        kvpout = {'service': 'CSW', 'version': '2.0.2', 'mode': 'sru'}

        if kvpin.has_key('operation'):
            if kvpin['operation'] == 'explain':
                kvpout['request'] = 'GetCapabilities'
            elif kvpin['operation'] == 'searchRetrieve':
                kvpout['request'] = 'GetRecords'
                if kvpin.has_key('startrecord'):
                    kvpout['startposition'] = int(kvpin['startrecord'])
                if kvpin.has_key('maximumrecords'):
                    kvpout['maxrecords'] = int(kvpin['maximumrecords'])
                else:
                    kvpout['maxrecords'] = 0

                # TODO: make smarter typename fetching
                kvpout['typenames'] = ','.join(typenames)
                kvpout['elementsetname'] = 'brief'
                kvpout['constraintlanguage'] = 'CQL_TEXT'
                kvpout['resulttype'] = 'results'

                if kvpin.has_key('query'):
                    pname_in_query = False
                    for coops in fes.MODEL['ComparisonOperators'].keys():
                        if kvpin['query'].find(fes.MODEL['ComparisonOperators'][coops]['opvalue']) != -1:
                            pname_in_query = True
                            break

                    kvpout['constraint'] = {'type': 'cql'}

                    if pname_in_query is False:
                        kvpout['constraint'] = 'csw:AnyText like \'%%%s%%\'' % kvpin['query']
                    else:
                        kvpout['constraint'] = kvpin['query']
        else:
            kvpout['request'] = 'GetCapabilities'

        return kvpout

    def response_csw2sru(self, element, environ):
        ''' transform a CSW response into an SRU response '''

        if util.xmltag_split(element.tag) == 'Capabilities':  # explain
            node = etree.Element(self.nspath_eval('sru:explainResponse'),
            nsmap=self.staticcontext.NAMESPACES)

            etree.SubElement(node, self.nspath_eval('sru:version')).text = self.staticcontext.SRU_VERSION

            record = etree.SubElement(node, self.nspath_eval('sru:record'))

            etree.SubElement(record, self.nspath_eval('sru:recordPacking')).text = 'XML'
            etree.SubElement(record, self.nspath_eval('sru:recordSchema')).text = 'http://explain.z3950.org/dtd/2.1/'

            recorddata = etree.SubElement(record, self.nspath_eval('sru:recordData'))

            explain = etree.SubElement(recorddata, self.nspath_eval('zr:explain'))

            serverinfo = etree.SubElement(explain, self.nspath_eval('zr:serverInfo'),
            protocol='SRU', version=self.staticcontext.SRU_VERSION, transport='http', method='GET POST SOAP')

            etree.SubElement(serverinfo, self.nspath_eval('zr:host')).text = environ.get('HTTP_HOST', environ["SERVER_NAME"]) # WSGI allows for either of these
            etree.SubElement(serverinfo, self.nspath_eval('zr:port')).text = environ['SERVER_PORT']
            etree.SubElement(serverinfo, self.nspath_eval('zr:database')).text = 'pycsw'

            databaseinfo = etree.SubElement(explain, self.nspath_eval('zr:databaseInfo'))

            etree.SubElement(databaseinfo, self.nspath_eval('zr:title'), lang='en', primary='true').text = element.xpath('//ows:Title', namespaces=self.globalstaticcontext.NAMESPACES)[0].text
            etree.SubElement(databaseinfo, self.nspath_eval('zr:description'), lang='en', primary='true').text = element.xpath('//ows:Abstract', namespaces=self.globalstaticcontext.NAMESPACES)[0].text

            indexinfo = etree.SubElement(explain, self.nspath_eval('zr:indexInfo'))
            etree.SubElement(indexinfo, self.nspath_eval('zr:set'), name='dc', identifier='info:srw/cql-context-set/1/dc-v1.1')

            for key, value in self.staticcontext.MAPPINGS['csw:Record']['index'].iteritems():
                zrindex = etree.SubElement(indexinfo, self.nspath_eval('zr:index'), id=value)
                etree.SubElement(zrindex, self.nspath_eval('zr:title')).text = key
                zrmap = etree.SubElement(zrindex, self.nspath_eval('zr:map'))
                etree.SubElement(zrmap, self.nspath_eval('zr:map'), set='dc').text = key

            zrindex = etree.SubElement(indexinfo, self.nspath_eval('zr:index'))
            zrmap = etree.SubElement(zrindex, self.nspath_eval('zr:map'))
            etree.SubElement(zrmap, self.nspath_eval('zr:name'), set='dc').text = 'title222'

            schemainfo = etree.SubElement(explain, self.nspath_eval('zr:schemaInfo'))
            zrschema = etree.SubElement(schemainfo, self.nspath_eval('zr:schema'), name='dc', identifier='info:srw/schema/1/dc-v1.1')
            etree.SubElement(zrschema, self.nspath_eval('zr:title')).text = 'Simple Dublin Core'

            configinfo = etree.SubElement(explain, self.nspath_eval('zr:configInfo'))
            etree.SubElement(configinfo, self.nspath_eval('zr:default'), type='numberOfRecords').text = '0'

        elif util.xmltag_split(element.tag) == 'GetRecordsResponse':

            recpos = int(element.xpath('//@nextRecord')[0]) - int(element.xpath('//@numberOfRecordsReturned')[0])

            node = etree.Element(self.nspath_eval('zs:searchRetrieveResponse'), nsmap=self.staticcontext.NAMESPACES)
            etree.SubElement(node, self.nspath_eval('zs:version')).text = self.staticcontext.SRU_VERSION
            etree.SubElement(node, self.nspath_eval('zs:numberOfRecords')).text = element.xpath('//@numberOfRecordsMatched')[0]

            for rec in element.xpath('//csw:BriefRecord', namespaces=self.globalstaticcontext.NAMESPACES):
                record = etree.SubElement(node, self.nspath_eval('zs:record'))
                etree.SubElement(node, self.nspath_eval('zs:recordSchema')).text = 'info:srw/schema/1/dc-v1.1'
                etree.SubElement(node, self.nspath_eval('zs:recordPacking')).text = 'xml'

                recorddata = etree.SubElement(record, self.nspath_eval('zs:recordData'))
                rec.tag = self.nspath_eval('srw_dc:srw_dc')
                recorddata.append(rec)

                etree.SubElement(record, self.nspath_eval('zs:recordPosition')).text = str(recpos)
                recpos += 1

        elif util.xmltag_split(element.tag) == 'ExceptionReport':
            node = self.exceptionreport2diagnostic(element)
        return node

    def exceptionreport2diagnostic(self, element):
        ''' transform a CSW exception into an SRU diagnostic '''
        node = etree.Element(
        self.nspath_eval('zs:searchRetrieveResponse'), nsmap=self.staticcontext.NAMESPACES)

        etree.SubElement(node, self.nspath_eval('zs:version')).text = self.staticcontext.SRU_VERSION

        diagnostics = etree.SubElement(node, self.nspath_eval('zs:diagnostics'))

        diagnostic = etree.SubElement(
        diagnostics, self.nspath_eval('zs:diagnostic'))

        etree.SubElement(diagnostic, self.nspath_eval('zd:diagnostic')).text = \
        'info:srw/diagnostic/1/7'

        etree.SubElement(diagnostic, self.nspath_eval('zd:message')).text = \
        element.find(self.nspath_eval('ows:Exception/ows:ExceptionText')).text

        etree.SubElement(diagnostic, self.nspath_eval('zd:details')).text = \
        element.find(self.nspath_eval('ows:Exception')).attrib.get('exceptionCode')

        return node
