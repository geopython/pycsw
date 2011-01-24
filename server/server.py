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
import time
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

        node = etree.Element(util.nspath('ExceptionReport', config.namespaces['ows']), nsmap=config.namespaces, version='1.0.2', language=self.config['server']['language'])
        node.attrib['{'+config.namespaces['xsi']+'}schemaLocation'] = '%s http://schemas.opengis.net/ows/1.0.0/owsExceptionReport.xsd' % config.namespaces['ows']

        e = etree.SubElement(node, util.nspath('Exception', config.namespaces['ows']), exceptionCode=code, locator=locator)
        etree.SubElement(e, util.nspath('ExceptionText', config.namespaces['ows'])).text=text

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

        node = etree.Element(util.nspath('Capabilities', config.namespaces['csw']), nsmap=config.namespaces, version='2.0.2')
        node.attrib['{'+config.namespaces['xsi']+'}schemaLocation'] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % config.namespaces['csw']

        if si is True:
            si = etree.SubElement(node, util.nspath('ServiceIdentification', config.namespaces['ows']))
            etree.SubElement(si, util.nspath('Title', config.namespaces['ows'])).text=self.config['identification']['title']
            etree.SubElement(si, util.nspath('Abstract', config.namespaces['ows'])).text=self.config['identification']['abstract']
            keywords = etree.SubElement(si, util.nspath('Keywords', config.namespaces['ows']))
            for k in self.config['identification']['keywords'].split(','):
                etree.SubElement(keywords, util.nspath('Keyword', config.namespaces['ows'])).text=k
            etree.SubElement(si, util.nspath('ServiceType', config.namespaces['ows']), codeSpace='OGC').text='CSW'
            etree.SubElement(si, util.nspath('ServiceTypeVersion', config.namespaces['ows'])).text='2.0.2'
            etree.SubElement(si, util.nspath('Fees', config.namespaces['ows'])).text=self.config['identification']['fees']
            etree.SubElement(si, util.nspath('AccessConstraints', config.namespaces['ows'])).text=self.config['identification']['accessconstraints']

        if sp is True:
            sp = etree.SubElement(node, util.nspath('ServiceProvider', config.namespaces['ows']))
            etree.SubElement(sp, util.nspath('ProviderName', config.namespaces['ows'])).text=self.config['provider']['name']
            ps = etree.SubElement(sp, util.nspath('ProviderSite', config.namespaces['ows']))
            ps.attrib['{'+config.namespaces['xlink']+'}type'] = 'simple'
            ps.attrib['{'+config.namespaces['xlink']+'}href'] = self.config['provider']['url']
            sc = etree.SubElement(sp, util.nspath('ServiceContact', config.namespaces['ows']))
            etree.SubElement(sc, util.nspath('IndividualName', config.namespaces['ows'])).text=self.config['contact']['name']
            etree.SubElement(sc, util.nspath('PositionName', config.namespaces['ows'])).text=self.config['contact']['position']
            ci = etree.SubElement(sc, util.nspath('ContactInfo', config.namespaces['ows']))
            ph = etree.SubElement(ci, util.nspath('Phone', config.namespaces['ows']))
            etree.SubElement(ph, util.nspath('Voice', config.namespaces['ows'])).text=self.config['contact']['phone']
            etree.SubElement(ph, util.nspath('Facsimile', config.namespaces['ows'])).text=self.config['contact']['fax']
            address = etree.SubElement(ci, util.nspath('Address', config.namespaces['ows']))
            etree.SubElement(address, util.nspath('DeliveryPoint', config.namespaces['ows'])).text=self.config['contact']['address']
            etree.SubElement(address, util.nspath('City', config.namespaces['ows'])).text=self.config['contact']['city']
            etree.SubElement(address, util.nspath('AdministrativeArea', config.namespaces['ows'])).text=self.config['contact']['stateorprovince']
            etree.SubElement(address, util.nspath('PostalCode', config.namespaces['ows'])).text=self.config['contact']['postalcode']
            etree.SubElement(address, util.nspath('Country', config.namespaces['ows'])).text=self.config['contact']['country']
            etree.SubElement(address, util.nspath('ElectronicMailAddress', config.namespaces['ows'])).text=self.config['contact']['email']

            ps = etree.SubElement(ci, util.nspath('OnlineResource', config.namespaces['ows']))
            ps.attrib['{'+config.namespaces['xlink']+'}type'] = 'simple'
            ps.attrib['{'+config.namespaces['xlink']+'}href'] = self.config['contact']['url']
            etree.SubElement(ci, util.nspath('HoursOfService', config.namespaces['ows'])).text=self.config['contact']['hours']
            etree.SubElement(ci, util.nspath('ContactInstructions', config.namespaces['ows'])).text=self.config['contact']['contactinstructions']
            etree.SubElement(sc, util.nspath('Role', config.namespaces['ows'])).text=self.config['contact']['role']

        if om is True:
            om = etree.SubElement(node, util.nspath('OperationsMetadata', config.namespaces['ows']))
            for o in config.model['operations'].keys():
                op = etree.SubElement(om, util.nspath('Operation', config.namespaces['ows']), name=o)
                dcp = etree.SubElement(op, util.nspath('DCP', config.namespaces['ows']))
                http = etree.SubElement(dcp, util.nspath('HTTP', config.namespaces['ows']))

                get = etree.SubElement(http, util.nspath('Get', config.namespaces['ows']))
                get.attrib['{'+config.namespaces['xlink']+'}type'] = 'simple'
                get.attrib['{'+config.namespaces['xlink']+'}href'] = self.config['server']['baseurl']
                post = etree.SubElement(http, util.nspath('Post', config.namespaces['ows']))
                post.attrib['{'+config.namespaces['xlink']+'}type'] = 'simple'
                post.attrib['{'+config.namespaces['xlink']+'}href'] = self.config['server']['baseurl']

                for p in config.model['operations'][o]['parameters']:
                    param = etree.SubElement(op, util.nspath('Parameter', config.namespaces['ows']), name=p)
                    for v in config.model['operations'][o]['parameters'][p]['values']:
                        etree.SubElement(param, util.nspath('Value', config.namespaces['ows'])).text = v

            for p in config.model['parameters'].keys():
                param = etree.SubElement(om, util.nspath('Parameter', config.namespaces['ows']), name=p)
                for v in config.model['parameters'][p]['values']:
                    etree.SubElement(param, util.nspath('Value', config.namespaces['ows'])).text = v

            for p in config.model['constraints'].keys():
                param = etree.SubElement(om, util.nspath('Constraint', config.namespaces['ows']), name=p)
                for v in config.model['constraints'][p]['values']:
                    etree.SubElement(param, util.nspath('Value', config.namespaces['ows'])).text = v

        fi = etree.SubElement(node, util.nspath('Filter_Capabilities', config.namespaces['ogc']))
        sc = etree.SubElement(fi, util.nspath('Spatial_Capabilities', config.namespaces['ogc']))
        go = etree.SubElement(sc, util.nspath('GeometryOperands', config.namespaces['ogc']))
        etree.SubElement(go, util.nspath('GeometryOperand', config.namespaces['ogc'])).text = 'gml:Envelope'

        so = etree.SubElement(sc, util.nspath('SpatialOperators', config.namespaces['ogc']))
        etree.SubElement(so, util.nspath('SpatialOperator', config.namespaces['ogc']), name='BBOX')

        sc = etree.SubElement(fi, util.nspath('Scalar_Capabilities', config.namespaces['ogc']))
        etree.SubElement(sc, util.nspath('LogicalOperators', config.namespaces['ogc']))
    
        co = etree.SubElement(sc, util.nspath('ComparisonOperators', config.namespaces['ogc']))

        for c in ['LessThan','GreaterThan','LessThanEqualTo','GreaterThanEqualTo','EqualTo','NotEqualTo','Like','Between','NullCheck']:
            etree.SubElement(co, util.nspath('ComparisonOperator', config.namespaces['ogc'])).text = c

        ic = etree.SubElement(fi, util.nspath('Id_Capabilities', config.namespaces['ogc']))
        etree.SubElement(ic, util.nspath('EID', config.namespaces['ogc']))
        etree.SubElement(ic, util.nspath('FID', config.namespaces['ogc']))

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
    
        if self.kvp.has_key('outputformat') and self.kvp['outputformat'] not in config.model['constraints']['outputFormat']['values']:
            return self.exceptionreport('InvalidParameterValue','outputformat', 'Invalid value for outputformat: %s' % self.kvp['outputformat'])
    
        if self.kvp.has_key('schemalanguage') and self.kvp['schemalanguage'] not in config.model['operations']['DescribeRecord']['parameters']['schemaLanguage']['values']:
            return self.exceptionreport('InvalidParameterValue','schemalanguage', 'Invalid value for schemalanguage: %s' % self.kvp['schemalanguage'])

        node = etree.Element(util.nspath('DescribeRecordResponse', config.namespaces['csw']), nsmap=config.namespaces)
        node.attrib['{'+config.namespaces['xsi']+'}schemaLocation'] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % config.namespaces['csw']

        if csw is True:
            sc = etree.SubElement(node, util.nspath('SchemaComponent', config.namespaces['csw']), schemaLanguage='XMLSCHEMA', targetNamespace=config.namespaces['csw'])
            dc = etree.parse(os.path.join(self.config['server']['home'],'etc','schemas','record.xsd')).getroot()
            sc.append(dc)

        if gmd is True:
            sc = etree.SubElement(node, util.nspath('SchemaComponent', config.namespaces['csw']), schemaLanguage='XMLSCHEMA', targetNamespace=config.namespaces['gmd'])
            xs = etree.SubElement(sc, util.nspath('schema', config.namespaces['xs']), elementFormDefault='qualified',targetNamespace=config.namespaces['gmd'])
            etree.SubElement(xs, util.nspath('include', config.namespaces['xs']), schemaLocation='http://www.isotc211.org/2005/gmd/gmd.xsd')

        return etree.tostring(node, pretty_print=True)
    
    def getrecords(self):

        timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())

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
            node = etree.Element(util.nspath('Acknowledgement', config.namespaces['csw']), nsmap=config.namespaces, timeStamp=timestamp)
            node.attrib['{'+config.namespaces['xsi']+'}schemaLocation'] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % config.namespaces['csw']

            node1 = etree.SubElement(node, util.nspath('EchoedRequest', config.namespaces['csw']))
            node1.append(etree.fromstring(self.request))

            return etree.tostring(node,pretty_print=True)
        
        esn = self.kvp['elementsetname']

        if self.kvp.has_key('maxrecords') is False:
            self.kvp['maxrecords'] = self.config['server']['maxrecords']

        q = query.Query(self.config['server']['data'])
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

        node = etree.Element(util.nspath('GetRecordsResponse', config.namespaces['csw']), nsmap=config.namespaces, version='2.0.2')
        node.attrib['{'+config.namespaces['xsi']+'}schemaLocation'] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % config.namespaces['csw']

        etree.SubElement(node, util.nspath('SearchStatus', config.namespaces['csw']), timestamp=timestamp)

        sr = etree.SubElement(node, util.nspath('SearchResults', config.namespaces['csw']), numberOfRecordsMatched=matched, numberOfRecordsReturned=returned, nextRecord=next)

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
    
                record = etree.SubElement(sr, util.nspath(el, config.namespaces['csw']))
    
                if self.kvp.has_key('elementname') is True and len(self.kvp['elementname']) > 0:
                    for e in self.kvp['elementname']:
                        ns,el, = e.split(':')
                        if el == 'BoundingBox':
                            bbox = r.bbox.split(',')
                            b = etree.SubElement(record, util.nspath('BoundingBox', config.namespaces['ows']), crs='urn:x-ogc:def:crs:EPSG:6.11:4326')
                            etree.SubElement(b, util.nspath('LowerCorner', config.namespaces['ows'])).text = '%s %s' % (bbox[0],bbox[1])
                            etree.SubElement(b, util.nspath('UpperCorner', config.namespaces['ows'])).text = '%s %s' % (bbox[2],bbox[3])
 
                        else:
                            if eval('r.%s'%el) != 'None':
                                etree.SubElement(record, util.nspath(el, config.namespaces[ns])).text=eval('r.%s'%el)
                elif self.kvp.has_key('elementsetname') is True:
                    etree.SubElement(record, util.nspath('identifier', config.namespaces['dc'])).text=r.identifier
                    etree.SubElement(record, util.nspath('title', config.namespaces['dc'])).text=r.title
                    etree.SubElement(record, util.nspath('type', config.namespaces['dc'])).text=r.type
                    if self.kvp['elementsetname'] == 'full':
                        etree.SubElement(record, util.nspath('date', config.namespaces['dc'])).text=r.date
                    if self.kvp['elementsetname'] == 'summary':
                        etree.SubElement(record, util.nspath('format', config.namespaces['dc'])).text=r.format

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

        timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())

        # init the query
        q = query.Query(self.config['server']['data'])

        results = q.get(ids=ids)

        node = etree.Element(util.nspath('GetRecordByIdResponse', config.namespaces['csw']), nsmap=config.namespaces)
        node.attrib['{'+config.namespaces['xsi']+'}schemaLocation'] = '%s http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd' % config.namespaces['csw']

        node.append(etree.Comment('hi'))

        for r in results:
            if esn == 'brief':
                el = 'BriefRecord'
            elif esn == 'summary':
                el = 'SummaryRecord'
            else:
                el = 'Record'
            record = etree.SubElement(node, util.nspath(el, config.namespaces['csw']))

            etree.SubElement(record, util.nspath('identifier', config.namespaces['dc'])).text=r.identifier
            if r.title != 'None':
                etree.SubElement(record, util.nspath('title', config.namespaces['dc'])).text=r.title
            etree.SubElement(record, util.nspath('type', config.namespaces['dc'])).text=r.type

            if self.kvp.has_key('elementsetname') is False:
                for k in r.subject_list.split(','):
                    etree.SubElement(record, util.nspath('subject', config.namespaces['dc'])).text=k

                etree.SubElement(record, util.nspath('format', config.namespaces['dc'])).text=r.format
                etree.SubElement(record, util.nspath('modified', config.namespaces['dct'])).text=r.modified
                etree.SubElement(record, util.nspath('abstract', config.namespaces['dct'])).text=r.abstract

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
            for d in doc.findall(util.nspath('TypeName', config.namespaces['csw'])):
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

            if doc.find(util.nspath('Query/Constraint', config.namespaces['csw'])):
                tmp = doc.find(util.nspath('Query/Constraint', config.namespaces['csw'])+'/'+ util.nspath('Filter', config.namespaces['ogc']))
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

            tmp = doc.find('{http://www.opengis.net/cat/csw/2.0.2}Query/{http://www.opengis.net/ogc}SortBy')
            if tmp is not None:
                request['sortby'] = {}
                request['sortby']['propertyname'] = tmp.find(util.nspath('SortProperty/PropertyName', config.namespaces['ogc'])).text

                tmp2 =  tmp.find(util.nspath('SortProperty/SortOrder', config.namespaces['ogc']))
                if tmp2 is not None:                   
                    request['sortby']['order'] = tmp2.text
                else:
                    request['sortby']['order'] = 'asc'
            else:
                request['sortby'] = None

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
