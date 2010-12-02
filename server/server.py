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
from lxml import etree
from genshi.template import TemplateLoader
import ConfigParser

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
                    text = 'Missing keyword: ', k
                    break
    
        # test each of the basic keyword values
        if error == 0:
            # test service
            if self.kvp['service'] != 'CSW':
                error = 1
                locator = 'service'
                code = 'InvalidParameterValue'
                text = 'Invalid value for service: ', \
                    self.kvp['service'], '.  Value MUST be CSW'
    
            # test version
            if self.kvp.has_key('version') and util.get_version_integer(self.kvp['version']) != \
                util.get_version_integer('2.0.2') and self.kvp['request'] != 'GetCapabilities':
                error = 1
                locator = 'version'
                code = 'InvalidParameterValue'
                text = 'Invalid value for version: ', self.kvp['version'], \
                    '.  Value MUST be ', '2.0.2'
    
            # check for GetCapabilities acceptversions
            if self.kvp.has_key('acceptversions'):
                for v in self.kvp['acceptversions'].split(','):
                    if util.get_version_integer(v) == util.get_version_integer('2.0.2'):
                        break
                    else:
                        error = 1
                        locator = 'acceptversions'
                        code = 'VersionNegotiationFailed'
                        text = 'Invalid parameter value in acceptversions: ', self.kvp['acceptversions'], \
                            '.  Value MUST be ', '2.0.2'
    
            # test request
            if self.kvp['request'] not in self.model['operations'].keys():
                error = 1
                locator = 'request'
                code = 'InvalidParameterValue'
                text = 'Invalid value for request: ', self.kvp['request']
    
    
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

    def exceptionreport(self,code,locator,text):
        loader = TemplateLoader(os.path.join(os.path.dirname(__file__), '..', 'templates', 'ogc', 'ows', '1.0.0'))
        tmpl = loader.load('ExceptionReport.xml')
        stream = tmpl.generate(version='2.0.2',language= \
            self.config['server']['language'],code=code,locator=locator,text=text)
        return stream.render()
    
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
        loader = TemplateLoader(os.path.join(os.path.dirname(__file__), '..', 'templates', 'ogc', 'csw', '2.0.2'))
        tmpl = loader.load('GetCapabilities.xml')
        stream = tmpl.generate(model=self.model,config=self.config, si=si, sp=sp, om=om)
        return stream.render()
    
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
    
        if self.kvp.has_key('outputformat') and self.kvp['outputformat'] != 'application/xml':
            return self.exceptionreport('InvalidParameterValue','outputformat', 'Invalid value for outputformat: %s' % self.kvp['outputformat'])
    
        if self.kvp.has_key('schemalanguage') and self.kvp['schemalanguage'] != 'http://www.w3.org/XML/Schema':
            return self.exceptionreport('InvalidParameterValue','schemalanguage', 'Invalid value for schemalanguage: %s' % self.kvp['schemalanguage'])
    
        loader = TemplateLoader(os.path.join(os.path.dirname(__file__), '..', 'templates', 'ogc', 'csw', '2.0.2'))
        tmpl = loader.load('DescribeRecord.xml')
        stream = tmpl.generate(csw=csw, gmd=gmd)
        return stream.render()

    def getrecords(self):
        import time
        import sqlite3

        timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())

        esn = self.kvp['elementsetname']

        if self.kvp.has_key('maxrecords') is False:
            self.kvp['maxrecords'] = self.config['server']['maxrecords']

        self.results = {}

        conn = sqlite3.connect(self.config['server']['data'])
        cur = conn.cursor()

        # the query
        cur.execute('select metadata from pycsw limit %s' % self.kvp['maxrecords'])

        results = cur.fetchall()

        self.results = {}
        self.results['matches'] = len(results)
        self.results['returned'] = self.kvp['maxrecords']
        self.results['next'] = len(results)+1
        self.results['records'] = []

        for row in results:
            self.results['records'].append(row[0])

        loader = TemplateLoader(os.path.join(os.path.dirname(__file__), '..', 'templates', 'ogc', 'csw', '2.0.2'))
        tmpl = loader.load('GetRecords.xml')
        stream = tmpl.generate(timestamp=timestamp, results=self.results)
        return stream.render()

    def getrecordbyid(self):
        import time
        import sqlite3

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
            esn = self.kvp['elementsetname']

        timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())

        self.results = {}
        conn = sqlite3.connect(self.config['server']['data'])
        cur = conn.cursor()

        if len(ids) > 1:
            sql = 'select metadata from pycsw where uuid in %s' % str(tuple([x for x in ids]))
        else:
            sql = 'select metadata from pycsw where uuid = \'%s\'' % ids[0]

        cur.execute(sql)

        results = cur.fetchall()

        self.results['matches'] = len(results)
        self.results['returned'] = len(results)
        self.results['next'] = len(results)+1
        self.results['records'] = []

        for row in results:
            self.results['records'].append(row[0].replace('csw:Record','csw:%sRecord' % esn.capitalize()))

        loader = TemplateLoader(os.path.join(os.path.dirname(__file__), '..', 'templates', 'ogc', 'csw', '2.0.2'))
        tmpl = loader.load('GetRecordById.xml')
        stream = tmpl.generate(timestamp=timestamp, results=self.results)
        return stream.render()

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

            tmp = doc.find('{http://www.opengis.net/cat/csw/2.0.2}ElementSetName')
            if tmp is not None:
                request['elementsetname'] = tmp.text
            else:
                request['elementsetname'] = None

        if request['request'] == 'GetRecordById':
            tmp = doc.find('{http://www.opengis.net/cat/csw/2.0.2}Id')
            if tmp is not None:
                request['id'] = tmp.text
            else:
                request['id'] = None

            pass
 
        return request
