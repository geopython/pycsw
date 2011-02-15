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
import re
import sys
import cgi
import sqlite3
from lxml import etree
import config, filter, query, util

class Csw(object):
    def __init__(self,configfile=None):
        self.config = config.get_config(configfile)

    def dispatch(self):
        error = 0

        cgifs = cgi.FieldStorage(keep_blank_values=1)
    
        if cgifs.file:  # it's a POST request
            postdata = cgifs.file.read()
            self.request = postdata
            self.kvp = self.parse_postdata(postdata)
            if isinstance(self.kvp, str) is True:  # it's an exception
                error = 1
                locator = 'service'
                code = 'InvalidRequest'
                text = self.kvp
    
        else:  # it's a GET request
            self.kvp = {}
            self.request = os.environ['HTTP_HOST'] + '?' + os.environ['REQUEST_URI']
            for key in cgifs.keys():
                self.kvp[key.lower()] = cgifs[key].value

        if error == 0:
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
                if self.kvp['request'] not in config.model['operations'].keys():
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
        appinfo = '<!-- pycsw %s -->\n' % config.version
        self.response = '%s%s%s%s' % (hh, xmldecl, appinfo, self.response)

    def exceptionreport(self,code,locator,text):

        node = etree.Element(util.nspath_eval('ows:ExceptionReport'), nsmap=config.namespaces, version='1.0.2', language=self.config['server']['language'])
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s http://schemas.opengis.net/ows/1.0.0/owsExceptionReport.xsd' % config.namespaces['ows']

        e = etree.SubElement(node, util.nspath_eval('ows:Exception'), exceptionCode=code, locator=locator)
        etree.SubElement(e, util.nspath_eval('ows:ExceptionText')).text=text

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

        node = etree.Element(util.nspath_eval('csw:Capabilities'), nsmap=config.namespaces, version='2.0.2')
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % config.namespaces['csw']

        if si is True:
            si = etree.SubElement(node, util.nspath_eval('ows:ServiceIdentification'))
            etree.SubElement(si, util.nspath_eval('ows:Title')).text=self.config['identification']['title']
            etree.SubElement(si, util.nspath_eval('ows:Abstract')).text=self.config['identification']['abstract']
            keywords = etree.SubElement(si, util.nspath_eval('ows:Keywords'))
            for k in self.config['identification']['keywords'].split(','):
                etree.SubElement(keywords, util.nspath_eval('ows:Keyword')).text=k
            etree.SubElement(si, util.nspath_eval('ows:ServiceType'), codeSpace='OGC').text='CSW'
            etree.SubElement(si, util.nspath_eval('ows:ServiceTypeVersion')).text='2.0.2'
            etree.SubElement(si, util.nspath_eval('ows:Fees')).text=self.config['identification']['fees']
            etree.SubElement(si, util.nspath_eval('ows:AccessConstraints')).text=self.config['identification']['accessconstraints']

        if sp is True:
            sp = etree.SubElement(node, util.nspath_eval('ows:ServiceProvider'))
            etree.SubElement(sp, util.nspath_eval('ows:ProviderName')).text=self.config['provider']['name']
            ps = etree.SubElement(sp, util.nspath_eval('ows:ProviderSite'))
            ps.attrib[util.nspath_eval('xlink:type')] = 'simple'
            ps.attrib[util.nspath_eval('xlink:href')] = self.config['provider']['url']
            sc = etree.SubElement(sp, util.nspath_eval('ows:ServiceContact'))
            etree.SubElement(sc, util.nspath_eval('ows:IndividualName')).text=self.config['contact']['name']
            etree.SubElement(sc, util.nspath_eval('ows:PositionName')).text=self.config['contact']['position']
            ci = etree.SubElement(sc, util.nspath_eval('ows:ContactInfo'))
            ph = etree.SubElement(ci, util.nspath_eval('ows:Phone'))
            etree.SubElement(ph, util.nspath_eval('ows:Voice')).text=self.config['contact']['phone']
            etree.SubElement(ph, util.nspath_eval('ows:Facsimile')).text=self.config['contact']['fax']
            address = etree.SubElement(ci, util.nspath_eval('ows:Address'))
            etree.SubElement(address, util.nspath_eval('ows:DeliveryPoint')).text=self.config['contact']['address']
            etree.SubElement(address, util.nspath_eval('ows:City')).text=self.config['contact']['city']
            etree.SubElement(address, util.nspath_eval('ows:AdministrativeArea')).text=self.config['contact']['stateorprovince']
            etree.SubElement(address, util.nspath_eval('ows:PostalCode')).text=self.config['contact']['postalcode']
            etree.SubElement(address, util.nspath_eval('ows:Country')).text=self.config['contact']['country']
            etree.SubElement(address, util.nspath_eval('ows:ElectronicMailAddress')).text=self.config['contact']['email']

            ps = etree.SubElement(ci, util.nspath_eval('ows:OnlineResource'))
            ps.attrib[util.nspath_eval('xlink:type')] = 'simple'
            ps.attrib[util.nspath_eval('xlink:href')] = self.config['contact']['url']
            etree.SubElement(ci, util.nspath_eval('ows:HoursOfService')).text=self.config['contact']['hours']
            etree.SubElement(ci, util.nspath_eval('ows:ContactInstructions')).text=self.config['contact']['contactinstructions']
            etree.SubElement(sc, util.nspath_eval('ows:Role')).text=self.config['contact']['role']

        if om is True:
            om = etree.SubElement(node, util.nspath_eval('ows:OperationsMetadata'))
            for o in config.model['operations'].keys():
                op = etree.SubElement(om, util.nspath_eval('ows:Operation'), name=o)
                dcp = etree.SubElement(op, util.nspath_eval('ows:DCP'))
                http = etree.SubElement(dcp, util.nspath_eval('ows:HTTP'))

                get = etree.SubElement(http, util.nspath_eval('ows:Get'))
                get.attrib[util.nspath_eval('xlink:type')] = 'simple'
                get.attrib[util.nspath_eval('xlink:href')] = self.config['server']['url']

                post = etree.SubElement(http, util.nspath_eval('ows:Post'))
                post.attrib[util.nspath_eval('xlink:type')] = 'simple'
                post.attrib[util.nspath_eval('xlink:href')] = self.config['server']['url']

                for p in config.model['operations'][o]['parameters']:
                    param = etree.SubElement(op, util.nspath_eval('ows:Parameter'), name=p)
                    for v in config.model['operations'][o]['parameters'][p]['values']:
                        etree.SubElement(param, util.nspath_eval('ows:Value')).text = v

            for p in config.model['parameters'].keys():
                param = etree.SubElement(om, util.nspath_eval('ows:Parameter'), name=p)
                for v in config.model['parameters'][p]['values']:
                    etree.SubElement(param, util.nspath_eval('ows:Value')).text = v

            for p in config.model['constraints'].keys():
                param = etree.SubElement(om, util.nspath_eval('ows:Constraint'), name=p)
                for v in config.model['constraints'][p]['values']:
                    etree.SubElement(param, util.nspath_eval('ows:Value')).text = v

        fi = etree.SubElement(node, util.nspath_eval('ogc:Filter_Capabilities'))
        sc = etree.SubElement(fi, util.nspath_eval('ogc:Spatial_Capabilities'))
        go = etree.SubElement(sc, util.nspath_eval('ogc:GeometryOperands'))
        etree.SubElement(go, util.nspath_eval('ogc:GeometryOperand')).text = 'gml:Envelope'

        so = etree.SubElement(sc, util.nspath_eval('ogc:SpatialOperators'))
        etree.SubElement(so, util.nspath_eval('ogc:SpatialOperator'), name='BBOX')

        sc = etree.SubElement(fi, util.nspath_eval('ogc:Scalar_Capabilities'))
        etree.SubElement(sc, util.nspath_eval('ogc:LogicalOperators'))
    
        co = etree.SubElement(sc, util.nspath_eval('ogc:ComparisonOperators'))

        for c in ['LessThan','GreaterThan','LessThanEqualTo','GreaterThanEqualTo','EqualTo','NotEqualTo','Like','Between','NullCheck']:
            etree.SubElement(co, util.nspath_eval('ogc:ComparisonOperator')).text = c

        ic = etree.SubElement(fi, util.nspath_eval('ogc:Id_Capabilities'))
        etree.SubElement(ic, util.nspath_eval('ogc:EID'))
        etree.SubElement(ic, util.nspath_eval('ogc:FID'))

        return etree.tostring(node, pretty_print=True)
    
    def describerecord(self):
        csw = False
        #gmd = False
    
        if self.kvp.has_key('typename') and len(self.kvp['typename']) > 0:
            for t in self.kvp['typename']:
                #if t not in ['csw:Record', 'gmd:MD_Metadata']:
                #    return exceptionreport('InvalidParameterValue', 'typename', \
                #    'Invalid value for typename: %s' % t)
                #else:
                if t == 'csw:Record':  # return only csw
                    csw = True
        #        if t == 'gmd:MD_Metadata':  # return only iso
        #            gmd = True
        else:
            csw = True
        #    gmd = True
    
        if self.kvp.has_key('outputformat') and self.kvp['outputformat'] not in config.model['constraints']['outputFormat']['values']:
            return self.exceptionreport('InvalidParameterValue','outputformat', 'Invalid value for outputformat: %s' % self.kvp['outputformat'])
    
        if self.kvp.has_key('schemalanguage') and self.kvp['schemalanguage'] not in config.model['operations']['DescribeRecord']['parameters']['schemaLanguage']['values']:
            return self.exceptionreport('InvalidParameterValue','schemalanguage', 'Invalid value for schemalanguage: %s' % self.kvp['schemalanguage'])

        node = etree.Element(util.nspath_eval('csw:DescribeRecordResponse'), nsmap=config.namespaces)
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % config.namespaces['csw']

        if csw is True:
            sc = etree.SubElement(node, util.nspath_eval('csw:SchemaComponent'), schemaLanguage='XMLSCHEMA', targetNamespace=config.namespaces['csw'])
            dc = etree.parse(os.path.join(self.config['server']['home'],'etc','schemas','record.xsd')).getroot()
            sc.append(dc)

        #if gmd is True:
        #    sc = etree.SubElement(node, util.nspath_eval('csw:SchemaComponent'), schemaLanguage='XMLSCHEMA', targetNamespace=config.namespaces['gmd'])
        #    xs = etree.SubElement(sc, util.nspath_eval('xs:schema'), elementFormDefault='qualified',targetNamespace=config.namespaces['gmd'])
        #    etree.SubElement(xs, util.nspath_eval('xs:include'), schemaLocation='http://www.isotc211.org/2005/gmd/gmd.xsd')

        return etree.tostring(node, pretty_print=True)
    
    def getrecords(self):

        timestamp = util.get_today_and_now()

        if self.kvp['outputschema'] not in config.model['constraints']['outputSchema']['values']:
            return self.exceptionreport('InvalidParameterValue', 'outputschema', 'Invalid outputSchema parameter value: %s' % self.kvp['outputschema'])

        if self.kvp['outputformat'] not in config.model['constraints']['outputFormat']['values']:
            return self.exceptionreport('InvalidParameterValue', 'outputformat', 'Invalid outputFormat parameter value: %s' % self.kvp['outputformat'])

        if self.kvp['resulttype'] not in config.model['operations']['GetRecords']['parameters']['resultType']['values']:
            return self.exceptionreport('InvalidParameterValue', 'resulttype', 'Invalid resultType parameter value: %s' % self.kvp['resulttype'])

        if self.kvp.has_key('elementsetname') is False:
            return self.exceptionreport('MissingParameterValue', 'elementsetname', 'Missing ElementSetName parameter')

        #if self.kvp['filter'] is None:
        #    return self.exceptionreport('InvalidParameterValue', 'filter', 'Invalid Filter request: %s' % self.request)

        #if self.kvp['elementsetname'] in ['brief','summary']:
        #    return self.exceptionreport('InvalidParameterValue', 'elementsetname', 'Invalid ElementSetName parameter: %s' % self.kvp['elementsetname'])

        if self.kvp['resulttype'] == 'validate':
            node = etree.Element(util.nspath_eval('csw:Acknowledgement'), nsmap=config.namespaces, timeStamp=timestamp)
            node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % config.namespaces['csw']

            node1 = etree.SubElement(node, util.nspath_eval('csw:EchoedRequest'))
            node1.append(etree.fromstring(self.request))

            return etree.tostring(node,pretty_print=True)
        
        esn = self.kvp['elementsetname']

        if self.kvp.has_key('maxrecords') is False:
            self.kvp['maxrecords'] = self.config['server']['maxrecords']

        q = query.Query(self.config['server']['metadata_db'])
        results = q.get(self.kvp['filter'], sortby=self.kvp['sortby'])

        if results is None:
            matched = '0'
            returned = '0'
            next = '0'

        else:
            matched = str(len(results))
            if int(matched) < int(self.kvp['maxrecords']):
                returned = str(int(matched))
                next = '0'
            else:
                returned = str(self.kvp['maxrecords'])
                next = str(int(self.kvp['startposition'])+int(self.kvp['maxrecords']))
            if int(self.kvp['maxrecords']) == 0:
                next = '1'

        node = etree.Element(util.nspath_eval('csw:GetRecordsResponse'), nsmap=config.namespaces, version='2.0.2')
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % config.namespaces['csw']

        etree.SubElement(node, util.nspath_eval('csw:SearchStatus'), timestamp=timestamp)

        sr = etree.SubElement(node, util.nspath_eval('csw:SearchResults'), numberOfRecordsMatched=matched, numberOfRecordsReturned=returned, nextRecord=next)

        max = int(self.kvp['startposition']) + int(self.kvp['maxrecords'])

        if results is not None:
            for r in results[int(self.kvp['startposition']):max]:
            #for r in results:
                if esn == 'brief':
                    el = 'BriefRecord'
                elif esn == 'summary':
                    el = 'SummaryRecord'
                else:
                    el = 'Record'
    
                record = etree.SubElement(sr, util.nspath_eval('csw:%s' % el))
    
                if self.kvp.has_key('elementname') is True and len(self.kvp['elementname']) > 0:
                    for e in self.kvp['elementname']:
                        ns,el, = e.split(':')
                        if el == 'BoundingBox':
                            bbox = r.bbox.split(',')
                            if len(bbox) == 4:
                                b = etree.SubElement(record, util.nspath_eval('ows:BoundingBox'), crs='urn:x-ogc:def:crs:EPSG:6.11:4326')
                                etree.SubElement(b, util.nspath_eval('ows:LowerCorner')).text = '%s %s' % (bbox[0],bbox[1])
                                etree.SubElement(b, util.nspath_eval('ows:UpperCorner')).text = '%s %s' % (bbox[2],bbox[3])
 
                        else:
                            if eval('r.%s'%el) != 'None':
                                etree.SubElement(record, util.nspath_eval('%s:%s' % (ns, el))).text=eval('r.%s'%el)
                elif self.kvp.has_key('elementsetname') is True:
                    etree.SubElement(record, util.nspath_eval('dc:identifier')).text=r.identifier
                    etree.SubElement(record, util.nspath_eval('dc:title')).text=r.title
                    etree.SubElement(record, util.nspath_eval('dc:type')).text=r.type
                    if self.kvp['elementsetname'] == 'full':
                        etree.SubElement(record, util.nspath_eval('dc:date')).text=r.date
                    if self.kvp['elementsetname'] == 'summary':
                        etree.SubElement(record, util.nspath_eval('dc:format')).text=r.format

        return etree.tostring(node, pretty_print=True)

    def getrecordbyid(self):

        if self.kvp.has_key('id') is False:
            return self.exceptionreport('MissingParameterValue', 'id', 'Missing id parameter')
        if len(self.kvp['id']) < 1:
            return self.exceptionreport('InvalidParameterValue', 'id', 'Invalid id parameter')

        ids = self.kvp['id'].split(',')

        if self.kvp.has_key('outputformat') and self.kvp['outputformat'] not in config.model['constraints']['outputFormat']['values']:
            return self.exceptionreport('InvalidParameterValue', 'outputformat', 'Invalid outputformat parameter %s' % self.kvp['outputformat'])

        if self.kvp.has_key('outputschema') and self.kvp['outputschema'] not in config.model['constraints']['outputSchema']['values']:
            return self.exceptionreport('InvalidParameterValue', 'outputschema', 'Invalid outputschema parameter %s' % self.kvp['outputschema'])

        if self.kvp.has_key('elementsetname') is False:
            esn = 'summary'
        else:
            if self.kvp['elementsetname'] not in config.model['constraints']['ElementSetName']['values']:
                return self.exceptionreport('InvalidParameterValue', 'elementsetname', 'Invalid elementsetname parameter %s' % self.kvp['elementsetname'])
            if self.kvp['elementsetname'] == 'full':
                esn = ''
            else:
                esn = self.kvp['elementsetname']

        timestamp = util.get_today_and_now()

        # init the query
        q = query.Query(self.config['server']['metadata_db'])

        results = q.get(ids=ids)

        node = etree.Element(util.nspath_eval('csw:GetRecordByIdResponse'), nsmap=config.namespaces)
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % config.namespaces['csw']

        for r in results:
            if esn == 'brief':
                el = 'BriefRecord'
            elif esn == 'summary':
                el = 'SummaryRecord'
            else:
                el = 'Record'
            record = etree.SubElement(node, util.nspath_eval('csw:%s' % el))

            etree.SubElement(record, util.nspath_eval('dc:identifier')).text=r.identifier
            if r.title != 'None':
                etree.SubElement(record, util.nspath_eval('dc:title')).text=r.title
            etree.SubElement(record, util.nspath_eval('dc:type')).text=r.type

            if self.kvp.has_key('elementsetname') is False:
                for k in r.subject_list.split(','):
                    etree.SubElement(record, util.nspath_eval('dc:subject')).text=k

                etree.SubElement(record, util.nspath_eval('dc:format')).text=r.format
                etree.SubElement(record, util.nspath_eval('dct:modified')).text=r.modified
                etree.SubElement(record, util.nspath_eval('dct:abstract')).text=r.abstract

        return etree.tostring(node, pretty_print=True)

    def parse_postdata(self,postdata):
        request = {}
        try:
            doc = etree.fromstring(postdata)
        except Exception, err:
            return str(err)

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
            for d in doc.findall(util.nspath_eval('csw:TypeName')):
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
                request['outputschema'] = config.namespaces['csw']

            tmp = doc.find('./').attrib.get('resultType')
            if tmp is not None:
                request['resulttype'] = tmp
            else:
                request['resulttype'] = 'results'

            tmp = doc.find('./').attrib.get('outputFormat')
            if tmp is not None:
                request['outputformat'] = tmp
            else:
                request['outputformat'] = 'application/xml'

            tmp = doc.find('./').attrib.get('startPosition')
            if tmp is not None:
                request['startposition'] = tmp
            else:
                request['startposition'] = 0

            tmp = doc.find('./').attrib.get('maxRecords')
            if tmp is not None:
                request['maxrecords'] = tmp
            else:
                request['maxrecords'] = self.config['server']['maxrecords']

            client_mr = int(request['maxrecords'])
            server_mr = int(self.config['server']['maxrecords'])

            if client_mr < server_mr:
                request['maxrecords'] = client_mr
#            else:
#                request['maxrecords'] = server_mr

            tmp = doc.find(util.nspath_eval('csw:Query/csw:ElementSetName'))
            if tmp is not None:
                request['elementsetname'] = tmp.text
            else:
                request['elementsetname'] = None

            request['elementname'] = []
            for e in doc.findall(util.nspath_eval('csw:Query/csw:ElementName')):
                request['elementname'].append(e.text)

            if doc.find(util.nspath_eval('csw:Query/csw:Constraint')):
                tmp = doc.find(util.nspath_eval('csw:Query/csw:Constraint/ogc:Filter'))
                if tmp is not None:
                    try:
                        request['filter'] = filter.Filter(tmp)
                    except Exception, err:
                        return 'Invalid Filter request2: %s' % err
                else:
                    try:
                        t=tmp.tag
                    except Exception, err:
                        return 'Invalid Filter request declaration'
            else:
                request['filter'] = None  

            tmp = doc.find(util.nspath_eval('csw:Query/ogc:SortBy'))
            if tmp is not None:
                request['sortby'] = {}
                request['sortby']['propertyname'] = tmp.find(util.nspath_eval('ogc:SortProperty/ogc:PropertyName')).text

                tmp2 =  tmp.find(util.nspath_eval('ogc:SortProperty/ogc:SortOrder'))
                if tmp2 is not None:                   
                    request['sortby']['order'] = tmp2.text
                else:
                    request['sortby']['order'] = 'asc'
            else:
                request['sortby'] = None

        if request['request'] == 'GetRecordById':
            tmp = doc.find(util.nspath_eval('csw:Id'))
            if tmp is not None:
                request['id'] = tmp.text
            else:
                request['id'] = None

            tmp = doc.find(util.nspath_eval('csw:ElementSetName'))
            if tmp is not None:
                request['elementsetname'] = tmp.text
            else:
                request['elementsetname'] = None

        return request
