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

import os
import sys
import time
import ConfigParser
import sqlite3
from lxml import etree
import query, util

namespaces = {
    None : 'http://www.opengis.net/cat/csw/2.0.2',
    'csw': 'http://www.opengis.net/cat/csw/2.0.2',
    'dc' : 'http://purl.org/dc/elements/1.1/',
    'dct': 'http://purl.org/dc/terms/',
    'gml': 'http://www.opengis.net/gml',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'ogc': 'http://www.opengis.net/ogc',
    'ows': 'http://www.opengis.net/ows',
    'xlink': 'http://www.w3.org/1999/xlink',
    'xs': 'http://www.w3.org/2001/XMLSchema',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

class Csw(object):
    def __init__(self,config=None):
        if file is not None:
            cp = ConfigParser.SafeConfigParser()
            cp.readfp(open(config))

        self.config = {}
        for i in cp.sections():
            s = i.lower()
            self.config[s] = {}
            for j in cp.options(i):
                k = j.lower()
                self.config[s][k] = unicode(cp.get(i,j).decode('latin-1')).strip()

        self.model =  {
            'operations': {
                'GetCapabilities': {
                    'parameters': {
                        'sections': {
                            'values': ['ServiceIdentification', 'ServiceProvider', 'OperationsMetadata', 'FilterCapabilities']
                        }
                    }
                },
                'DescribeRecord': {
                    'parameters': {
                        'schemaLanguage': {
                            #'values': ['XMLSCHEMA']
                            'values': ['http://www.w3.org/XML/Schema']
                        }
                    }
                },
                'GetRecords': {
                    'parameters': {
                        'resultType': {
                            'values': ['hits', 'results', 'validate']
                        }
                    }
                },
                'GetRecordById': {
                    'parameters': {
                    }
                }
            },
            'parameters': {
                'version': { 
                    'values': ['2.0.2']
                },
                'service': {
                    'values': ['CSW']
                }
            },
            'constraints': {
                'PostEncoding': {
                    'values': ['XML']
                },
                'outputFormat': {
                    'values': ['application/xml']
                },
                'outputSchema': {
                    'values': ['http://www.opengis.net/cat/csw/2.0.2', 'http://www.isotc211.org/2005/gmd']
                },
                'TypeNames': {
                    'values': ['csw:Record','gmd:MD_Metadata']
                },
                'ElementSetName': {
                    'values': ['brief', 'summary', 'full']
                }
            }
        }

    def dispatch(self):
        import sys
        import re
        import cgi
        import util
    
        error = 0

        cgifs = cgi.FieldStorage(keep_blank_values=1)
    
        if cgifs.file:  # it's a POST request
            postdata = cgifs.file.read()
            self.kvp = self.parse_postdata(postdata)
    
        else:  # it's a GET request
            self.kvp = {}
            for key in cgifs.keys():
                self.kvp[key.lower()] = cgifs[key].value
    
        # test for the basic keyword values (service, version, request)
        for k in ['service', 'version', 'request']:
            if self.kvp.has_key(k) == False:
                if k == 'version' and self.kvp.has_key('request') and self.kvp['request'] == 'GetCapabilities':
                    pass
                else:
                    error   = 1
                    locator = k
                    code = 'MissingParameterValue'
                    text = 'Missing keyword: %s' % k
                    break
    
        # test each of the basic keyword values
        if error == 0:
            # test service
            if self.kvp['service'] != 'CSW':
                error = 1
                locator = 'service'
                code = 'InvalidParameterValue'
                text = 'Invalid value for service: %s.  Value MUST be CSW' % self.kvp['service']
    
            # test version
            if self.kvp.has_key('version') and util.get_version_integer(self.kvp['version']) != \
                util.get_version_integer('2.0.2') and self.kvp['request'] != 'GetCapabilities':
                error = 1
                locator = 'version'
                code = 'InvalidParameterValue'
                text = 'Invalid value for version: %s.  Value MUST be 2.0.2' % self.kvp['version']
    
            # check for GetCapabilities acceptversions
            if self.kvp.has_key('acceptversions'):
                for v in self.kvp['acceptversions'].split(','):
                    if util.get_version_integer(v) == util.get_version_integer('2.0.2'):
                        break
                    else:
                        error = 1
                        locator = 'acceptversions'
                        code = 'VersionNegotiationFailed'
                        text = 'Invalid parameter value in acceptversions: %s.  Value MUST be 2.0.2' % self.kvp['acceptversions']
    
            # test request
            if self.kvp['request'] not in self.model['operations'].keys():
                error = 1
                locator = 'request'
                code = 'InvalidParameterValue'
                text = 'Invalid value for request: %s' % self.kvp['request']
    
    
        if error == 1:  # return an ExceptionReport
            self.response = self.exceptionreport(code, locator, text)
    
        else:  # process per the request value
            if self.kvp['request'] == 'GetCapabilities':
                self.response = self.getcapabilities()
            elif self.kvp['request'] == 'DescribeRecord':
                self.response = self.describerecord()
            elif self.kvp['request'] == 'GetRecords':
                self.response = self.getrecords()
            elif self.kvp['request'] == 'GetRecordById':
                self.response = self.getrecordbyid()
            else:
                self.response = self.exceptionreport('InvalidParameterValue', 'request', 'Invalid request parameter: %s' % self.kvp['request'])

        # set HTTP response headers and XML declaration
        hh = 'Content-type:%s\n\n' % self.config['server']['mimetype']
        xmldecl = '<?xml version="1.0" encoding="%s" standalone="no"?>\n' % self.config['server']['encoding']
        self.response = '%s%s%s' % (hh, xmldecl, self.response)

    def exceptionreport(self,code,locator,text):

        node = etree.Element(util.nspath('ExceptionReport', namespaces['ows']), nsmap=namespaces, version='1.0.2', language=self.config['server']['language'])
        node.attrib['{'+namespaces['xsi']+'}schemaLocation'] = '%s http://schemas.opengis.net/ows/1.0.0/owsExceptionReport.xsd' % namespaces['ows']

        e = etree.SubElement(node, util.nspath('Exception', namespaces['ows']), exceptionCode=code, locator=locator)
        etree.SubElement(e, util.nspath('ExceptionText', namespaces['ows'])).text=text

        return etree.tostring(node, pretty_print=True)
    
    def getcapabilities(self):
        si = True
        sp = True
        om = True
        if self.kvp.has_key('sections'):
            si = False
            sp = False
            om = False
            for s in self.kvp['sections'].split(','):
                if s == 'ServiceIdentification':
                    si = True
                if s == 'ServiceProvider':
                    sp = True
                if s == 'OperationsMetadata':
                    om = True

        node = etree.Element(util.nspath('Capabilities', namespaces['csw']), nsmap=namespaces, version='2.0.2')
        node.attrib['{'+namespaces['xsi']+'}schemaLocation'] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % namespaces['csw']

        if si is True:
            si = etree.SubElement(node, util.nspath('ServiceIdentification', namespaces['ows']))
            etree.SubElement(si, util.nspath('Title', namespaces['ows'])).text=self.config['identification']['title']
            etree.SubElement(si, util.nspath('Abstract', namespaces['ows'])).text=self.config['identification']['abstract']
            keywords = etree.SubElement(si, util.nspath('Keywords', namespaces['ows']))
            for k in self.config['identification']['keywords'].split(','):
                etree.SubElement(keywords, util.nspath('Keyword', namespaces['ows'])).text=k
            etree.SubElement(si, util.nspath('ServiceType', namespaces['ows']), codeSpace='OGC').text='CSW'
            etree.SubElement(si, util.nspath('ServiceTypeVersion', namespaces['ows'])).text='2.0.2'
            etree.SubElement(si, util.nspath('Fees', namespaces['ows'])).text=self.config['identification']['fees']
            etree.SubElement(si, util.nspath('AccessConstraints', namespaces['ows'])).text=self.config['identification']['accessconstraints']

        if sp is True:
            sp = etree.SubElement(node, util.nspath('ServiceProvider', namespaces['ows']))
            etree.SubElement(sp, util.nspath('ProviderName', namespaces['ows'])).text=self.config['provider']['name']
            ps = etree.SubElement(sp, util.nspath('ProviderSite', namespaces['ows']))
            ps.attrib['{'+namespaces['xlink']+'}type'] = 'simple'
            ps.attrib['{'+namespaces['xlink']+'}href'] = self.config['provider']['url']
            sc = etree.SubElement(sp, util.nspath('ServiceContact', namespaces['ows']))
            etree.SubElement(sc, util.nspath('IndividualName', namespaces['ows'])).text=self.config['contact']['name']
            etree.SubElement(sc, util.nspath('PositionName', namespaces['ows'])).text=self.config['contact']['position']
            ci = etree.SubElement(sc, util.nspath('ContactInfo', namespaces['ows']))
            ph = etree.SubElement(ci, util.nspath('Phone', namespaces['ows']))
            etree.SubElement(ph, util.nspath('Voice', namespaces['ows'])).text=self.config['contact']['phone']
            etree.SubElement(ph, util.nspath('Facsimile', namespaces['ows'])).text=self.config['contact']['fax']
            address = etree.SubElement(ci, util.nspath('Address', namespaces['ows']))
            etree.SubElement(address, util.nspath('DeliveryPoint', namespaces['ows'])).text=self.config['contact']['address']
            etree.SubElement(address, util.nspath('City', namespaces['ows'])).text=self.config['contact']['city']
            etree.SubElement(address, util.nspath('AdministrativeArea', namespaces['ows'])).text=self.config['contact']['stateorprovince']
            etree.SubElement(address, util.nspath('PostalCode', namespaces['ows'])).text=self.config['contact']['postalcode']
            etree.SubElement(address, util.nspath('Country', namespaces['ows'])).text=self.config['contact']['country']
            etree.SubElement(address, util.nspath('ElectronicMailAddress', namespaces['ows'])).text=self.config['contact']['email']

            ps = etree.SubElement(ci, util.nspath('OnlineResource', namespaces['ows']))
            ps.attrib['{'+namespaces['xlink']+'}type'] = 'simple'
            ps.attrib['{'+namespaces['xlink']+'}href'] = self.config['contact']['url']
            etree.SubElement(ci, util.nspath('HoursOfService', namespaces['ows'])).text=self.config['contact']['hours']
            etree.SubElement(ci, util.nspath('ContactInstructions', namespaces['ows'])).text=self.config['contact']['contactinstructions']
            etree.SubElement(sc, util.nspath('Role', namespaces['ows'])).text=self.config['contact']['role']

        if om is True:
            om = etree.SubElement(node, util.nspath('OperationsMetadata', namespaces['ows']))
            for o in self.model['operations'].keys():
                op = etree.SubElement(om, util.nspath('Operation', namespaces['ows']), name=o)
                dcp = etree.SubElement(op, util.nspath('DCP', namespaces['ows']))
                http = etree.SubElement(dcp, util.nspath('HTTP', namespaces['ows']))

                get = etree.SubElement(http, util.nspath('Get', namespaces['ows']))
                get.attrib['{'+namespaces['xlink']+'}type'] = 'simple'
                get.attrib['{'+namespaces['xlink']+'}href'] = self.config['server']['baseurl']
                post = etree.SubElement(http, util.nspath('Post', namespaces['ows']))
                post.attrib['{'+namespaces['xlink']+'}type'] = 'simple'
                post.attrib['{'+namespaces['xlink']+'}href'] = self.config['server']['baseurl']

                for p in self.model['operations'][o]['parameters']:
                    param = etree.SubElement(op, util.nspath('Parameter', namespaces['ows']), name=p)
                    for v in self.model['operations'][o]['parameters'][p]['values']:
                        etree.SubElement(param, util.nspath('Value', namespaces['ows'])).text = v

            for p in self.model['parameters'].keys():
                param = etree.SubElement(om, util.nspath('Parameter', namespaces['ows']), name=p)
                for v in self.model['parameters'][p]['values']:
                    etree.SubElement(param, util.nspath('Value', namespaces['ows'])).text = v

            for p in self.model['constraints'].keys():
                param = etree.SubElement(om, util.nspath('Constraint', namespaces['ows']), name=p)
                for v in self.model['constraints'][p]['values']:
                    etree.SubElement(param, util.nspath('Value', namespaces['ows'])).text = v

        fi = etree.SubElement(node, util.nspath('Filter_Capabilities', namespaces['ogc']))
        sc = etree.SubElement(fi, util.nspath('Spatial_Capabilities', namespaces['ogc']))
        go = etree.SubElement(sc, util.nspath('GeometryOperands', namespaces['ogc']))
        etree.SubElement(go, util.nspath('GeometryOperand', namespaces['ogc'])).text = 'gml:Envelope'

        so = etree.SubElement(sc, util.nspath('SpatialOperators', namespaces['ogc']))
        etree.SubElement(so, util.nspath('SpatialOperator', namespaces['ogc']), name='BBOX')

        sc = etree.SubElement(fi, util.nspath('Scalar_Capabilities', namespaces['ogc']))
        etree.SubElement(sc, util.nspath('LogicalOperators', namespaces['ogc']))
    
        co = etree.SubElement(sc, util.nspath('ComparisonOperators', namespaces['ogc']))

        for c in ['LessThan','GreaterThan','LessThanEqualTo','GreaterThanEqualTo','EqualTo','NotEqualTo','Like','Between','NullCheck']:
            etree.SubElement(co, util.nspath('ComparisonOperator', namespaces['ogc'])).text = c

        ic = etree.SubElement(fi, util.nspath('Id_Capabilities', namespaces['ogc']))
        etree.SubElement(ic, util.nspath('EID', namespaces['ogc']))
        etree.SubElement(ic, util.nspath('FID', namespaces['ogc']))

        return etree.tostring(node, pretty_print=True)
    
    def describerecord(self):
        csw = False
        gmd = False
    
        if self.kvp.has_key('typename') and len(self.kvp['typename']) > 0:
            for t in self.kvp['typename']:
                #if t not in ['csw:Record', 'gmd:MD_Metadata']:
                #    return exceptionreport('InvalidParameterValue', 'typename', \
                #    'Invalid value for typename: %s' % t)
                #else:
                if t == 'csw:Record':  # return only csw
                    csw = True
                if t == 'gmd:MD_Metadata':  # return only iso
                    gmd = True
        else:
            csw = True
            gmd = True
    
        if self.kvp.has_key('outputformat') and self.kvp['outputformat'] not in self.model['constraints']['outputFormat']['values']:
            return self.exceptionreport('InvalidParameterValue','outputformat', 'Invalid value for outputformat: %s' % self.kvp['outputformat'])
    
        if self.kvp.has_key('schemalanguage') and self.kvp['schemalanguage'] not in self.model['operations']['DescribeRecord']['parameters']['schemaLanguage']['values']:
            return self.exceptionreport('InvalidParameterValue','schemalanguage', 'Invalid value for schemalanguage: %s' % self.kvp['schemalanguage'])

        node = etree.Element(util.nspath('DescribeRecordResponse', namespaces['csw']), nsmap=namespaces)
        node.attrib['{'+namespaces['xsi']+'}schemaLocation'] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % namespaces['csw']

        if csw is True:
            sc = etree.SubElement(node, util.nspath('SchemaComponent', namespaces['csw']), schemaLanguage='XMLSCHEMA', targetNamespace=namespaces['csw'])
            dc = etree.parse('/usr/local/wwwsites/apache/devgeo.cciw.ca/htdocs/pycsw/trunk/server/record.xsd').getroot()
            sc.append(dc)
            #xs = etree.SubElement(sc, util.nspath('schema', namespaces['xs']), elementFormDefault='qualified',targetNamespace=namespaces['csw'])
            #etree.SubElement(xs, util.nspath('include', namespaces['xs']), schemaLocation='http://schemas.opengis.net/csw/2.0.2/record.xsd')

        if gmd is True:
            sc = etree.SubElement(node, util.nspath('SchemaComponent', namespaces['csw']), schemaLanguage='XMLSCHEMA', targetNamespace=namespaces['gmd'])
            xs = etree.SubElement(sc, util.nspath('schema', namespaces['xs']), elementFormDefault='qualified',targetNamespace=namespaces['gmd'])
            etree.SubElement(xs, util.nspath('include', namespaces['xs']), schemaLocation='http://www.isotc211.org/2005/gmd/gmd.xsd')

        return etree.tostring(node, pretty_print=True)
    
    def getrecords(self):

        timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())

        if self.kvp.has_key('elementsetname') is False:
            return self.exceptionreport('MissingParameterValue', 'elementsetname', 'Missing ElementSetName parameter')

        esn = self.kvp['elementsetname']

        if self.kvp.has_key('maxrecords') is False:
            self.kvp['maxrecords'] = self.config['server']['maxrecords']

        q = query.Query(self.config['server']['data'])
        results = q.get()

        node = etree.Element(util.nspath('GetRecordsResponse', namespaces['csw']), nsmap=namespaces, version='2.0.2')
        node.attrib['{'+namespaces['xsi']+'}schemaLocation'] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % namespaces['csw']

        etree.SubElement(node, util.nspath('SearchStatus', namespaces['csw']), timestamp=timestamp)

        sr = etree.SubElement(node, util.nspath('SearchResults', namespaces['csw']), numberOfRecordsMatched=str(len(results)), numberOfRecordsReturned=str(self.kvp['maxrecords']), nextRecord=str(int(self.kvp['maxrecords'])+1))

        for r in results[0:int(self.kvp['maxrecords'])]:
            if esn == 'brief':
                el = 'BriefRecord'
            elif esn == 'summary':
                el = 'SummaryRecord'
            else:
                el = 'Record'

            record = etree.SubElement(sr, util.nspath(el, namespaces['csw']))

            if self.kvp.has_key('elementname') is True and len(self.kvp['elementname']) > 0:
                for e in self.kvp['elementname']:
                    ns,el, = e.split(':')
                    etree.SubElement(record, util.nspath(el, namespaces[ns])).text=eval('r.%s'%el)
            elif self.kvp.has_key('elementsetname') is True:
                etree.SubElement(record, util.nspath('identifier', namespaces['dc'])).text=r.identifier
                etree.SubElement(record, util.nspath('title', namespaces['dc'])).text=r.title
                etree.SubElement(record, util.nspath('type', namespaces['dc'])).text=r.type

        return etree.tostring(node, pretty_print=True)

    def getrecordbyid(self):

        if self.kvp.has_key('id') is False:
            return self.exceptionreport('MissingParameterValue', 'id', 'Missing id parameter')
        if len(self.kvp['id']) < 1:
            return self.exceptionreport('InvalidParameterValue', 'id', 'Invalid id parameter')

        ids = self.kvp['id'].split(',')

        if self.kvp.has_key('outputformat') and self.kvp['outputformat'] not in self.model['constraints']['outputFormat']['values']:
            return self.exceptionreport('InvalidParameterValue', 'outputformat', 'Invalid outputformat parameter %s' % self.kvp['outputformat'])

        if self.kvp.has_key('outputschema') and self.kvp['outputschema'] not in self.model['constraints']['outputSchema']['values']:
            return self.exceptionreport('InvalidParameterValue', 'outputschema', 'Invalid outputschema parameter %s' % self.kvp['outputschema'])


        if self.kvp.has_key('elementsetname') is False:
            esn = 'summary'
        else:
            if self.kvp['elementsetname'] not in self.model['constraints']['ElementSetName']['values']:
                return self.exceptionreport('InvalidParameterValue', 'elementsetname', 'Invalid elementsetname parameter %s' % self.kvp['elementsetname'])
            if self.kvp['elementsetname'] == 'full':
                esn = ''
            else:
                esn = self.kvp['elementsetname']

        timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())

        # init the query
        q = query.Query(self.config['server']['data'])

        results = q.get(ids=ids)

        node = etree.Element(util.nspath('GetRecordByIdResponse', namespaces['csw']), nsmap=namespaces)
        node.attrib['{'+namespaces['xsi']+'}schemaLocation'] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % namespaces['csw']

        node.append(etree.Comment('hi'))

        for r in results:
            if esn == 'brief':
                el = 'BriefRecord'
            elif esn == 'summary':
                el = 'SummaryRecord'
            else:
                el = 'Record'
            record = etree.SubElement(node, util.nspath(el, namespaces['csw']))

            etree.SubElement(record, util.nspath('identifier', namespaces['dc'])).text=r.identifier
            if r.title != 'None':
                etree.SubElement(record, util.nspath('title', namespaces['dc'])).text=r.title
            etree.SubElement(record, util.nspath('type', namespaces['dc'])).text=r.type

            if self.kvp.has_key('elementsetname') is False:
                for k in r.subject_list.split(','):
                    etree.SubElement(record, util.nspath('subject', namespaces['dc'])).text=k

                etree.SubElement(record, util.nspath('format', namespaces['dc'])).text=r.format
                etree.SubElement(record, util.nspath('modified', namespaces['dct'])).text=r.modified
                etree.SubElement(record, util.nspath('abstract', namespaces['dct'])).text=r.abstract

        return etree.tostring(node, pretty_print=True)

    def parse_postdata(self,postdata):
        request = {}
        doc = etree.fromstring(postdata)
        request['request'] = doc.tag.split('}')[1]
        tmp = doc.find('./').attrib.get('service')
        if tmp is not None:
            request['service'] = tmp
        else:
            request['service'] = None
        tmp = doc.find('./').attrib.get('version')
        if tmp is not None:
            request['version'] = tmp
        else:
            request['version'] = None
        tmp = doc.find('.//{http://www.opengis.net/ows}Version')
        if tmp is not None:
            request['version'] = tmp.text
    
        # DescribeRecord
        if request['request'] == 'DescribeRecord':
            request['typename'] = []
            for d in doc.findall('{http://www.opengis.net/cat/csw/2.0.2}TypeName'):
                request['typename'].append(d.text)
    
            tmp = doc.find('./').attrib.get('schemaLanguage')
            if tmp is not None:
                request['schemalanguage'] = tmp
    
            tmp = doc.find('./').attrib.get('outputFormat')
            if tmp is not None:
                request['outputformat'] = tmp
   
        # GetRecords
        if request['request'] == 'GetRecords':
            tmp = doc.find('./').attrib.get('outputSchema')
            if tmp is not None:
                request['outputschema'] = tmp
            else:
                request['outputschema'] = 'http://www.opengis.net/cat/csw/2.0.2'
            tmp = doc.find('./').attrib.get('outputFormat')

            if tmp is not None:
                request['outputformat'] = tmp
            else:
                request['outputformat'] = 'application/xml'

            tmp = doc.find('./').attrib.get('startposition')
            if tmp is not None:
                request['startposition'] = tmp
            else:
                request['startposition'] = 0

            tmp = doc.find('./').attrib.get('maxRecords')
            if tmp is not None:
                request['maxrecords'] = tmp
            else:
                request['maxrecords'] = self.config['server']['maxrecords']

            client_mr = request['maxrecords']
            server_mr = self.config['server']['maxrecords']

            if client_mr < server_mr:
                request['maxrecords'] = client_mr
            else:
                request['maxrecords'] = server_mr

            tmp = doc.find('{http://www.opengis.net/cat/csw/2.0.2}Query/{http://www.opengis.net/cat/csw/2.0.2}ElementSetName')
            if tmp is not None:
                request['elementsetname'] = tmp.text
            else:
                request['elementsetname'] = None

            request['elementname'] = []
            for e in doc.findall('{http://www.opengis.net/cat/csw/2.0.2}Query/{http://www.opengis.net/cat/csw/2.0.2}ElementName'):
                request['elementname'].append(e.text)

        if request['request'] == 'GetRecordById':
            tmp = doc.find('{http://www.opengis.net/cat/csw/2.0.2}Id')
            if tmp is not None:
                request['id'] = tmp.text
            else:
                request['id'] = None

            tmp = doc.find('{http://www.opengis.net/cat/csw/2.0.2}ElementSetName')
            if tmp is not None:
                request['elementsetname'] = tmp.text
            else:
                request['elementsetname'] = None

 
        return request
