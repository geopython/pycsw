# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id: server.py 56 2011-03-07 16:45:35Z tomkralidis $
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
import cgi
import sqlite3
import urllib2
from lxml import etree
import config, core_queryables, filter, log, repository, util

class Csw(object):
    def __init__(self,configfile=None):
        # load user configuration
        self.config = config.get_config(configfile)

        # configure transaction support, if specified in config
        self._gen_transactions()

        # configure logging
        try:
            self.log = log.initlog(self.config)
        except Exception, err:
            self.response = self.exceptionreport('NoApplicableCode', 'service', str(err))

        # generate domain model
        config.model['operations']['GetDomain'] = config.gen_domains()

        # set OGC schemas location
        if self.config['server'].has_key('ogc_schemas_base') is False:  # use default value
            self.config['server']['ogc_schemas_base'] = config.ogc_schemas_base

        # configure core queryables
        self.cq = core_queryables.CoreQueryables(self.config)

        # initialize connection to repository
        self.db = repository.Repository(self.config['repository']['db'], self.config['repository']['records_table'])

        # generate distributed search model, if specified in config
        if self.config['server'].has_key('federatedcatalogues') is True:
            self.log.debug('Configuring distributed search.')
            config.model['constraints']['FederatedCatalogues'] = {}
            config.model['constraints']['FederatedCatalogues']['values'] = []
            for fc in self.config['server']['federatedcatalogues'].split(','):
                config.model['constraints']['FederatedCatalogues']['values'].append(fc)

        self.log.debug('Configuration: %s.' % self.config)
        self.log.debug('Model: %s.' % config.model)
        self.log.debug('Core Queryable mappings: %s.' % self.cq.mappings)

    def dispatch(self):
        error = 0

        if hasattr(self,'response') is True:
            self._set_response()
            return

        cgifs = cgi.FieldStorage(keep_blank_values=1)
    
        if cgifs.file:  # it's a POST request
            postdata = cgifs.file.read()
            self.request = postdata
            self.log.debug('Request type: POST.  Request:\n%s\n', self.request)
            self.kvp = self.parse_postdata(postdata)
            if isinstance(self.kvp, str) is True:  # it's an exception
                error = 1
                locator = 'service'
                code = 'InvalidRequest'
                text = self.kvp
    
        else:  # it's a GET request
            self.kvp = {}
            self.request = 'http://%s%s' % (os.environ['HTTP_HOST'], os.environ['REQUEST_URI'])
            self.log.debug('Request type: GET.  Request:\n%s\n', self.request)
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
                    if self.kvp['request'] in ['Transaction','Harvest']:
                        code = 'OperationNotSupported'
                        text = '%s operations are not supported' % self.kvp['request']
                    else:
                        code = 'InvalidParameterValue'
                        text = 'Invalid value for request: %s' % self.kvp['request']

        if error == 1:  # return an ExceptionReport
            self.response = self.exceptionreport(code, locator, text)
    
        else:  # process per the request value
            if self.kvp['request'] == 'GetCapabilities':
                self.response = self.getcapabilities()
            elif self.kvp['request'] == 'DescribeRecord':
                self.response = self.describerecord()
            elif self.kvp['request'] == 'GetDomain':
                self.response = self.getdomain()
            elif self.kvp['request'] == 'GetRecords':
                self.response = self.getrecords()
            elif self.kvp['request'] == 'GetRecordById':
                self.response = self.getrecordbyid()
            elif self.kvp['request'] == 'Transaction':
                self.response = self.transaction()
            elif self.kvp['request'] == 'Harvest':
                self.response = self.harvest()
            else:
                self.response = self.exceptionreport('InvalidParameterValue', 'request', 'Invalid request parameter: %s' % self.kvp['request'])

        self._set_response()
        self.log.debug('Response:\n%s\n' % self.response)

    def exceptionreport(self,code,locator,text):
        self.exception = True

        node = etree.Element(util.nspath_eval('ows:ExceptionReport'), nsmap=config.namespaces, version='1.0.2', language=self.config['server']['language'])
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s %s/ows/1.0.0/owsExceptionReport.xsd' % (config.namespaces['ows'], self.config['server']['ogc_schemas_base'])

        e = etree.SubElement(node, util.nspath_eval('ows:Exception'), exceptionCode=code, locator=locator)
        etree.SubElement(e, util.nspath_eval('ows:ExceptionText')).text=text

        return node
    
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
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s %s/csw/2.0.2/CSW-discovery.xsd' % (config.namespaces['csw'], self.config['server']['ogc_schemas_base'])

        if si is True:
            self.log.debug('Writing section ServiceIdentification.')
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
            self.log.debug('Writing section ServiceProvider.')
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
            self.log.debug('Writing section OperationsMetadata.')
            om = etree.SubElement(node, util.nspath_eval('ows:OperationsMetadata'))
            for o in config.model['operations'].keys():
                op = etree.SubElement(om, util.nspath_eval('ows:Operation'), name=o)
                dcp = etree.SubElement(op, util.nspath_eval('ows:DCP'))
                http = etree.SubElement(dcp, util.nspath_eval('ows:HTTP'))

                if config.model['operations'][o]['methods']['get'] is True:
                    get = etree.SubElement(http, util.nspath_eval('ows:Get'))
                    get.attrib[util.nspath_eval('xlink:type')] = 'simple'
                    get.attrib[util.nspath_eval('xlink:href')] = self.config['server']['url']

                if config.model['operations'][o]['methods']['post'] is True:
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
            
            etree.SubElement(om, util.nspath_eval('ows:ExtendedCapabilities'))

        # always write out Filter_Capabilities
        self.log.debug('Writing section Filter_Capabilities.')
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

        return node
    
    def describerecord(self):
        csw = False
    
        if self.kvp.has_key('typename') and len(self.kvp['typename']) > 0:
            for t in self.kvp['typename']:
                if t == 'csw:Record':  # return only csw
                    csw = True
        else:
            csw = True
    
        if self.kvp.has_key('outputformat') and self.kvp['outputformat'] not in config.model['operations']['DescribeRecord']['parameters']['outputFormat']['values']:
            return self.exceptionreport('InvalidParameterValue','outputformat', 'Invalid value for outputformat: %s' % self.kvp['outputformat'])
    
        if self.kvp.has_key('schemalanguage') and self.kvp['schemalanguage'] not in config.model['operations']['DescribeRecord']['parameters']['schemaLanguage']['values']:
            return self.exceptionreport('InvalidParameterValue','schemalanguage', 'Invalid value for schemalanguage: %s' % self.kvp['schemalanguage'])

        node = etree.Element(util.nspath_eval('csw:DescribeRecordResponse'), nsmap=config.namespaces)
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s %s/csw/2.0.2/CSW-discovery.xsd' % (config.namespaces['csw'], self.config['server']['ogc_schemas_base'])

        if csw is True:
            self.log.debug('Writing csw:Record schema.')
            sc = etree.SubElement(node, util.nspath_eval('csw:SchemaComponent'), schemaLanguage='XMLSCHEMA', targetNamespace=config.namespaces['csw'])
            dc = etree.parse(os.path.join(self.config['server']['home'],'etc','schemas','ogc','csw','2.0.2','record.xsd')).getroot()
            sc.append(dc)

        return node
    
    def getdomain(self):
        if self.kvp.has_key('parametername') is False and self.kvp.has_key('propertyname') is False:
            return self.exceptionreport('MissingParameterValue','parametername', 'Missing value.  One of propertyname or parametername must be specified')

        node = etree.Element(util.nspath_eval('csw:GetDomainResponse'), nsmap=config.namespaces)
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s %s/csw/2.0.2/CSW-discovery.xsd' % (config.namespaces['csw'], self.config['server']['ogc_schemas_base'])

        if self.kvp.has_key('parametername'):
            for pn in self.kvp['parametername'].split(','):
                self.log.debug('Parsing parametername %s.' % pn)
                dv = etree.SubElement(node, util.nspath_eval('csw:DomainValues'), type='csw:Record')
                etree.SubElement(dv, util.nspath_eval('csw:ParameterName')).text = pn
                o,p = pn.split('.')
                if o in config.model['operations'].keys() and p in config.model['operations'][o]['parameters'].keys():
                    lv = etree.SubElement(dv, util.nspath_eval('csw:ListOfValues'))
                    for v in config.model['operations'][o]['parameters'][p]['values']:
                        etree.SubElement(lv, util.nspath_eval('csw:Value')).text = v

        if self.kvp.has_key('propertyname'):
            for pn in self.kvp['propertyname'].split(','):
                self.log.debug('Parsing propertyname %s.' % pn)
                dv = etree.SubElement(node, util.nspath_eval('csw:DomainValues'), type='csw:Record')
                etree.SubElement(dv, util.nspath_eval('csw:PropertyName')).text = pn

                try:
                    tmp = self.cq.mappings[pn]['obj_attr']
                    self.log.debug('Querying database on property %s (%s).' % (pn, tmp))
                    results = self.db.query(propertyname=tmp)
                    self.log.debug('Results: %s' %str(len(results)))
                    lv = etree.SubElement(dv, util.nspath_eval('csw:ListOfValues'))
                    for r in results:
                        etree.SubElement(lv, util.nspath_eval('csw:Value')).text = r[0]
                except:
                    self.log.debug('No results for propertyname %s.' % pn)
                    pass

        return node

    def getrecords(self):

        timestamp = util.get_today_and_now()

        if self.kvp.has_key('elementsetname') is False and self.kvp.has_key('elementname') is False:  # mutually exclusive required
            return self.exceptionreport('MissingParameterValue', 'elementsetname', 'Missing one of ElementSetName or ElementName parameter(s)')

        if self.kvp.has_key('outputschema') is False:
            self.kvp['outputschema'] = config.namespaces['csw']

        if self.kvp['outputschema'] not in config.model['operations']['GetRecords']['parameters']['outputSchema']['values']:
            return self.exceptionreport('InvalidParameterValue', 'outputschema', 'Invalid outputSchema parameter value: %s' % self.kvp['outputschema'])

        if self.kvp.has_key('outputformat') is False:
            self.kvp['outputformat'] = 'application/xml'
     
        if self.kvp['outputformat'] not in config.model['operations']['GetRecords']['parameters']['outputFormat']['values']:
            return self.exceptionreport('InvalidParameterValue', 'outputformat', 'Invalid outputFormat parameter value: %s' % self.kvp['outputformat'])

        if self.kvp.has_key('resulttype') is False:
            self.kvp['resulttype'] = 'hits'

        if self.kvp['resulttype'] is not None:
            if self.kvp['resulttype'] not in config.model['operations']['GetRecords']['parameters']['resultType']['values']:
                return self.exceptionreport('InvalidParameterValue', 'resulttype', 'Invalid resultType parameter value: %s' % self.kvp['resulttype'])

        if (self.kvp.has_key('elementname') is False or len(self.kvp['elementname']) == 0) and self.kvp['elementsetname'] not in config.model['operations']['GetRecords']['parameters']['ElementSetName']['values']:
            return self.exceptionreport('InvalidParameterValue', 'elementsetname', 'Invalid ElementSetName parameter value: %s' % self.kvp['elementsetname'])

        if self.kvp['resulttype'] == 'validate':
            node = etree.Element(util.nspath_eval('csw:Acknowledgement'), nsmap=config.namespaces, timeStamp=timestamp)
            node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s %s/csw/2.0.2/CSW-discovery.xsd' % (config.namespaces['csw'], self.config['server']['ogc_schemas_base'])

            node1 = etree.SubElement(node, util.nspath_eval('csw:EchoedRequest'))
            node1.append(etree.fromstring(self.request))

            return node

        if self.kvp.has_key('maxrecords') is False:
            self.kvp['maxrecords'] = self.config['server']['maxrecords']

        if self.kvp.has_key('constraint') is True and (self.kvp.has_key('filter') is False and self.kvp.has_key('cql') is False):  # GET request
            self.log.debug('csw:Constraint passed over HTTP GET.')
            if self.kvp.has_key('constraintlanguage') is False:
                return self.exceptionreport('MissingParameterValue', 'constraintlanguage', 'constraintlanguage required when constraint specified')
            if self.kvp['constraintlanguage'] not in config.model['operations']['GetRecords']['parameters']['CONSTRAINTLANGUAGE']['values']:
                return self.exceptionreport('InvalidParameterValue', 'constraintlanguage', 'Invalid constraintlanguage: %s' % self.kvp['constraintlanguage'])
            if self.kvp['constraintlanguage'] == 'CQL_TEXT':
                self.kvp['cql'] = self.kvp['constraint']
                self.kvp['cql'] = self._cql_update_cq_mappings(self.kvp['constraint'])
                self.kvp['filter'] = None
            elif self.kvp['constraintlanguage'] == 'FILTER':

                # validate filter XML
                try:
                    schema = os.path.join(self.config['server']['home'],'etc','schemas','ogc','filter','1.1.0','filter.xsd')
                    self.log.debug('Validating Filter %s.' % self.kvp['constraint'])
                    schema = etree.XMLSchema(etree.parse(schema))
                    parser = etree.XMLParser(schema=schema)
                    doc = etree.fromstring(self.kvp['constraint'], parser)
                    self.log.debug('Filter is valid XML.')
                    self.kvp['filter'] = filter.Filter(doc, self.cq.mappings)
                except Exception, err:
                    et = 'Exception: the document is not valid.\nError: %s.' % str(err)
                    self.log.debug(et)
                    return self.exceptionreport('InvalidParameterValue', 'constraint', 'Invalid Filter query: %s' % et)

                self.kvp['cql'] = None

        if self.kvp.has_key('filter') is False:
            self.kvp['filter'] = None
        if self.kvp.has_key('cql') is False:
            self.kvp['cql'] = None

        if self.kvp.has_key('sortby') is False:
            self.kvp['sortby'] = None

        if self.kvp.has_key('startposition') is False:
            self.kvp['startposition'] = 1

        self.log.debug('Querying database with filter: %s, cql: %s, sortby: %s.' % (self.kvp['filter'], self.kvp['cql'], self.kvp['sortby']))

        try:
            results = self.db.query(filter=self.kvp['filter'], cql=self.kvp['cql'], sortby=self.kvp['sortby'])
        except Exception, err:
            return self.exceptionreport('InvalidParameterValue', 'constraint', 'Invalid query: %s' % err)

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

        dsresults = []

        if self.config['server'].has_key('federatedcatalogues') and self.kvp['distributedsearch'] == 'TRUE' and self.kvp['hopcount'] > 0:

            self.log.debug('DistributedSearch specified (hopCount=%s.' % self.kvp['hopcount'])

            from owslib.csw import CatalogueServiceWeb
            for fc in self.config['server']['federatedcatalogues'].split(','):
                self.log.debug('Performing distributed search on federated catalogue: %s.' % fc)
                c = CatalogueServiceWeb(fc)
                c.getrecords(xml=self.request)
                self.log.debug('Distirubuted search results from catalogue %s: %s.' % (fc, c.results))
                matched = str(int(matched) + int(c.results['matches']))
                dsresults.append(c.records)

        self.log.debug('Search results: matched: %s, returned: %s, next: %s.' % (matched, returned, next))
        node = etree.Element(util.nspath_eval('csw:GetRecordsResponse'), nsmap=config.namespaces, version='2.0.2')
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s %s/csw/2.0.2/CSW-discovery.xsd' % (config.namespaces['csw'], self.config['server']['ogc_schemas_base'])

        etree.SubElement(node, util.nspath_eval('csw:SearchStatus'), timestamp=timestamp)

        if self.kvp['filter'] is None and self.kvp['resulttype'] is None:
            returned='0'

        sr = etree.SubElement(node, util.nspath_eval('csw:SearchResults'), numberOfRecordsMatched=matched, numberOfRecordsReturned=returned, nextRecord=next,recordSchema=self.kvp['outputschema'])

        if self.kvp['filter'] is None and self.kvp['resulttype'] is None:
            self.log.debug('Empty result set returned.')
            return node

        max = int(self.kvp['startposition']) + int(self.kvp['maxrecords'])
 
        if results is not None:
            self.log.debug('Presenting records %s - %s.' % (self.kvp['startposition'], max))
            for r in results[int(self.kvp['startposition'])-1:int(max)-1]:
                sr.append(self._write_record(r))

        if self.kvp.has_key('distributedsearch') and self.kvp['distributedsearch'] == 'TRUE' and self.kvp['hopcount'] > 0:
            for rs in dsresults:
                for rec in rs:
                    sr.append(etree.fromstring(rs[rec].xml))

        return node

    def getrecordbyid(self):

        if self.kvp.has_key('id') is False:
            return self.exceptionreport('MissingParameterValue', 'id', 'Missing id parameter')
        if len(self.kvp['id']) < 1:
            return self.exceptionreport('InvalidParameterValue', 'id', 'Invalid id parameter')

        ids = self.kvp['id'].split(',')

        if self.kvp.has_key('outputformat') and self.kvp['outputformat'] not in config.model['operations']['GetRecordById']['parameters']['outputFormat']['values']:
            return self.exceptionreport('InvalidParameterValue', 'outputformat', 'Invalid outputformat parameter %s' % self.kvp['outputformat'])

        if self.kvp.has_key('outputschema') and self.kvp['outputschema'] not in config.model['operations']['GetRecordById']['parameters']['outputSchema']['values']:
            return self.exceptionreport('InvalidParameterValue', 'outputschema', 'Invalid outputschema parameter %s' % self.kvp['outputschema'])

        if self.kvp.has_key('elementsetname') is False:
            self.kvp['elementsetname'] = 'summary'
        else:
            if self.kvp['elementsetname'] not in config.model['operations']['GetRecordById']['parameters']['ElementSetName']['values']:
                return self.exceptionreport('InvalidParameterValue', 'elementsetname', 'Invalid elementsetname parameter %s' % self.kvp['elementsetname'])
            if self.kvp['elementsetname'] == 'full':
                self.kvp['elementsetname'] = ''
            else:
                self.kvp['elementsetname'] = self.kvp['elementsetname']

        timestamp = util.get_today_and_now()

        self.log.debug('Querying database with ids: %s.' % ids)
        results = self.db.query(ids=ids)

        node = etree.Element(util.nspath_eval('csw:GetRecordByIdResponse'), nsmap=config.namespaces)
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s %s/csw/2.0.2/CSW-discovery.xsd' % (config.namespaces['csw'], self.config['server']['ogc_schemas_base'])

        self.log.debug('Presenting %s records.' % str(len(results)))
        for r in results:
             node.append(self._write_record(r))

        return node

    def transaction(self):
        if self.config['transactions']['enabled'] != 'true':
            return self.exceptionreport('OperationNotSupported', 'transaction', 'Transaction operations are not supported')
        ip = os.environ['REMOTE_ADDR']
        if ip not in self.config['transactions']['ips'].split(','):
            return self.exceptionreport('NoApplicableCode', 'transaction', 'Transaction operations are not enabled from this IP address: %s' % ip)

        node = etree.Element(util.nspath_eval('csw:TransactionResponse'), nsmap=config.namespaces, version='2.0.2')
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s %s/csw/2.0.2/CSW-publication.xsd' % (config.namespaces['csw'], self.config['server']['ogc_schemas_base'])

        return node

    def harvest(self):
        if self.config['transactions']['enabled'] != 'true':
            return self.exceptionreport('OperationNotSupported', 'harvest', 'Harvest operations are not supported')
        ip = os.environ['REMOTE_ADDR']
        if ip not in self.config['transactions']['ips'].split(','):
            return self.exceptionreport('NoApplicableCode', 'harvest', 'Harvest operations are not enabled from this IP address: %s' % ip)

        # validate resourcetype
        if self.kvp['resourcetype'] not in config.model['operations']['Harvest']['parameters']['ResourceType']['values']:
            return self.exceptionreport('InvalidParameterValue', 'resourcetype', 'Invalid resource type parameter: %s.  Allowable resourcetype values: %s' % (self.kvp['resourcetype'], ','.join(config.model['operations']['Harvest']['parameters']['ResourceType']['values'])))

        # fetch resource
        try:
            req = urllib2.Request(self.kvp['source'])
            req.add_header('User-Agent', 'pycsw (http://pycsw.org/)')
            r = urllib2.urlopen(req).read() 
        except Exception, err:
            et = 'Error fetching document %s.\nError: %s.' % (self.kvp['source'], str(err))
            self.log.debug(et)
            return self.exceptionreport('InvalidParameterValue', 'source', et)

        node = etree.Element(util.nspath_eval('csw:HarvestResponse'), nsmap=config.namespaces)
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s %s/csw/2.0.2/CSW-publication.xsd' % (config.namespaces['csw'], self.config['server']['ogc_schemas_base'])
        etree.SubElement(node,'hi').text = r

        return node

    def parse_postdata(self,postdata):
        request = {}
        try:
            self.log.debug('Parsing %s.' % postdata)
            doc = etree.fromstring(postdata)
        except Exception, err:
            et = 'Exception: the document is not well-formed.\nError: %s.' % str(err)
            self.log.debug(et)
            return et

        # if this is a SOAP request, get to SOAP-ENV:Body/csw:*
        if doc.tag == util.nspath_eval('soapenv:Envelope'):
            self.log.debug('SOAP request specified.')
            self.soap = True
            doc = doc.find(util.nspath_eval('soapenv:Body')).xpath('child::*')[0]

        if doc.tag in [util.nspath_eval('csw:Transaction'), util.nspath_eval('csw:Harvest')]:
            schema = os.path.join(self.config['server']['home'],'etc','schemas','ogc','csw','2.0.2','CSW-publication.xsd')
        else:
            schema = os.path.join(self.config['server']['home'],'etc','schemas','ogc','csw','2.0.2','CSW-discovery.xsd')

        try:
            self.log.debug('Validating %s.' % postdata)
            schema = etree.XMLSchema(etree.parse(schema))
            parser = etree.XMLParser(schema=schema)
            if hasattr(self, 'soap') is True and self.soap is True:  # validate the body of the SOAP request
                doc = etree.fromstring(etree.tostring(doc), parser)
            else:  # validate the request normally
                doc = etree.fromstring(postdata, parser)
            self.log.debug('Request is valid XML.')
        except Exception, err:
            et = 'Exception: the document is not valid.\nError: %s.' % str(err)
            self.log.debug(et)
            return et

        request['request'] = util.xmltag_split(doc.tag)
        self.log.debug('Request operation %s specified.' % request['request'])
        tmp = doc.find('./').attrib.get('service')
        if tmp is not None:
            request['service'] = tmp

        tmp = doc.find('./').attrib.get('version')
        if tmp is not None:
            request['version'] = tmp

        tmp = doc.find('.//%s' % util.nspath_eval('ows:Version'))
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

        # GetDomain
        if request['request'] == 'GetDomain':
            tmp = doc.find(util.nspath_eval('csw:ParameterName'))
            if tmp is not None:
                request['parametername'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw:PropertyName'))
            if tmp is not None:
                request['propertyname'] = tmp.text

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
                request['resulttype'] = None

            tmp = doc.find('./').attrib.get('outputFormat')
            if tmp is not None:
                request['outputformat'] = tmp
            else:
                request['outputformat'] = 'application/xml'

            tmp = doc.find('./').attrib.get('startPosition')
            if tmp is not None:
                request['startposition'] = tmp
            else:
                request['startposition'] = 1

            tmp = doc.find('./').attrib.get('maxRecords')
            if tmp is not None:
                request['maxrecords'] = tmp
            else:
                request['maxrecords'] = self.config['server']['maxrecords']

            client_mr = int(request['maxrecords'])
            server_mr = int(self.config['server']['maxrecords'])

            if client_mr < server_mr:
                request['maxrecords'] = client_mr

 
            tmp = doc.find(util.nspath_eval('csw:DistributedSearch'))
            if tmp is not None:
                request['distributedsearch'] = 'TRUE'
                hc = tmp.attrib.get('hopCount')
                if hc is not None:
                    request['hopcount'] = int(hc)-1
                else:
                    request['hopcount'] = 1
            else:
                request['distributedsearch'] = 'FALSE'

            tmp = doc.find(util.nspath_eval('csw:Query/csw:ElementSetName'))
            if tmp is not None:
                request['elementsetname'] = tmp.text
            else:
                request['elementsetname'] = None

            request['elementname'] = []
            for e in doc.findall(util.nspath_eval('csw:Query/csw:ElementName')):
                request['elementname'].append(e.text)

            request['filter'] = None
            request['cql'] = None

            tmp = doc.find(util.nspath_eval('csw:Query/csw:Constraint'))
            if tmp is not None:
                ctype = tmp.xpath('child::*')

                try: 
                    if ctype[0].tag == util.nspath_eval('ogc:Filter'):
                        self.log.debug('Filter constraint specified.')
                        try:
                            request['filter'] = filter.Filter(ctype[0], self.cq.mappings)
                        except Exception, err:
                            return 'Invalid Filter request: %s' % err
                    elif ctype[0].tag == util.nspath_eval('csw:CqlText'):
                        self.log.debug('CQL constraint specified: %s.' % ctype[0].text)
                        request['cql'] = self._cql_update_cq_mappings(ctype[0].text)
                    else:
                        return '2Invalid csw:Constraint request declaration (ogc:Filter or csw:CqlText is required)'
                except Exception, err:
                    return 'Invalid csw:Constraint request declaration (ogc:Filter or csw:CqlText is required)'
            else: 
                self.log.debug('No csw:Constraint (ogc:Filter or csw:CqlText) specified.')

            tmp = doc.find(util.nspath_eval('csw:Query/ogc:SortBy'))
            if tmp is not None:
                self.log.debug('Sorted query specified.')
                request['sortby'] = {}
                request['sortby']['propertyname'] = tmp.find(util.nspath_eval('ogc:SortProperty/ogc:PropertyName')).text
                request['sortby']['cq_mapping'] = self.cq.mappings[tmp.find(util.nspath_eval('ogc:SortProperty/ogc:PropertyName')).text.lower()]['db_col']

                tmp2 =  tmp.find(util.nspath_eval('ogc:SortProperty/ogc:SortOrder'))
                if tmp2 is not None:                   
                    request['sortby']['order'] = tmp2.text
                else:
                    request['sortby']['order'] = 'asc'
            else:
                request['sortby'] = None

        # GetRecordById
        if request['request'] == 'GetRecordById':
            ids = []
            for id in doc.findall(util.nspath_eval('csw:Id')):
                ids.append(id.text)

            request['id'] = ','.join(ids)

            tmp = doc.find(util.nspath_eval('csw:ElementSetName'))
            if tmp is not None:
                request['elementsetname'] = tmp.text
            else:
                request['elementsetname'] = 'summary'

        # Transaction
        if request['request'] == 'Transaction':
            tmp = doc.find(util.nspath_eval('csw:Insert'))
            if tmp is not None:
                request['ttype'] = 'insert'
            tmp = doc.find(util.nspath_eval('csw:Update'))
            if tmp is not None:
                request['ttype'] = 'update'
            tmp = doc.find(util.nspath_eval('csw:Delete'))
            if tmp is not None:
                request['ttype'] = 'delete'
 
        # Harvest
        if request['request'] == 'Harvest':
            request['source'] = doc.find(util.nspath_eval('csw:Source')).text
            request['resourcetype'] = doc.find(util.nspath_eval('csw:ResourceType')).text

            tmp = doc.find(util.nspath_eval('csw:ResourceFormat'))
            if tmp is not None:
                request['resourceformat'] = tmp
            else:
                request['resourceformat'] = 'application/xml'

            tmp = doc.find(util.nspath_eval('csw:HarvestInterval'))
            if tmp is not None:
                request['harvestinterval'] = tmp

            tmp = doc.find(util.nspath_eval('csw:ResponseHandler'))
            if tmp is not None:
                request['responsehandler'] = tmp

        return request

    def _write_record(self, r):
        if self.kvp['elementsetname'] == 'brief':
            el = 'BriefRecord'
        elif self.kvp['elementsetname'] == 'summary':
            el = 'SummaryRecord'
        else:
            el = 'Record'

        record = etree.Element(util.nspath_eval('csw:%s' % el))

        bbox = getattr(r, self.cq.mappings['ows:BoundingBox']['obj_attr'])

        if self.kvp.has_key('elementname') is True and len(self.kvp['elementname']) > 0:
            for e in self.kvp['elementname']:
                ns,el, = e.split(':')
                if el == 'BoundingBox':
                    self._write_bbox(record, bbox)
                else:
                    if hasattr(r, self.cq.mappings[e]['obj_attr']) is True:
                        etree.SubElement(record, util.nspath_eval('%s:%s' % (ns, el))).text=getattr(r, self.cq.mappings[e]['obj_attr'])
        elif self.kvp.has_key('elementsetname') is True:
            if self.kvp['elementsetname'] == 'full':  # dump the full record
                record = etree.fromstring(getattr(r,self.cq.mappings['csw:AnyText']['obj_attr']))
            else:  # dump brief record first (always required elements) then summary if requests
                for i in ['dc:identifier','dc:title','dc:type']:
                    etree.SubElement(record, util.nspath_eval(i)).text=getattr(r, self.cq.mappings[i]['obj_attr'])
                if self.kvp['elementsetname'] == 'summary':
                    subjects = getattr(r, self.cq.mappings['dc:subject']['obj_attr'])
                    if subjects is not None:
                        for s in subjects.split(','):
                            etree.SubElement(record, util.nspath_eval('dc:subject')).text=s
                    for i in ['dc:format','dc:relation','dct:modified','dct:abstract']:
                        val = getattr(r, self.cq.mappings[i]['obj_attr'])
                        if val is not None:
                            etree.SubElement(record, util.nspath_eval(i)).text=val
                self._write_bbox(record, bbox)

        return record

    def _write_bbox(self, record, bbox):
        if bbox is not None:
            bbox2 = bbox.split(',')
            if len(bbox2) == 4:
                b = etree.SubElement(record, util.nspath_eval('ows:BoundingBox'), crs='urn:x-ogc:def:crs:EPSG:6.11:4326')
                etree.SubElement(b, util.nspath_eval('ows:LowerCorner')).text = '%s %s' % (bbox2[1],bbox2[0])
                etree.SubElement(b, util.nspath_eval('ows:UpperCorner')).text = '%s %s' % (bbox2[3],bbox2[2])

    def _set_response(self):
        # set HTTP response headers and XML declaration
        self.log.debug('Writing response.')
        hh = 'Content-type:%s\n\n' % self.config['server']['mimetype']
        xmldecl = '<?xml version="1.0" encoding="%s" standalone="no"?>\n' % self.config['server']['encoding']
        appinfo = '<!-- pycsw %s r$Rev: 62 $ -->\n' % config.version

        if hasattr(self, 'soap') and self.soap is True:
            self._gen_soap_wrapper() 

        self.response = '%s%s%s%s' % (hh, xmldecl, appinfo, etree.tostring(self.response, pretty_print=1))

    def _gen_soap_wrapper(self):
        self.log.debug('Writing SOAP wrapper.')
        node = etree.Element(util.nspath_eval('soapenv:Envelope'), nsmap=config.namespaces)
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s %s' % (config.namespaces['soapenv'], config.namespaces['soapenv']) 

	node2 = etree.SubElement(node, util.nspath_eval('soapenv:Body'))

        if hasattr(self, 'exception') and self.exception is True:
            node3 = etree.SubElement(node2, util.nspath_eval('soapenv:Fault'))
            node4 = etree.SubElement(node3, util.nspath_eval('soapenv:Code'))
            etree.SubElement(node4, util.nspath_eval('soapenv:Value')).text = 'soap:Server'
            node4 = etree.SubElement(node3, util.nspath_eval('soapenv:Reason'))
            etree.SubElement(node4, util.nspath_eval('soapenv:Text')).text = 'A server exception was encountered.'
            node4 = etree.SubElement(node3, util.nspath_eval('soapenv:Detail'))
            node4.append(self.response)
        else:
            node2.append(self.response)

        self.response = node

    def _gen_transactions(self):
        if self.config.has_key('transactions') is True and self.config['transactions'].has_key('enabled') is True and self.config['transactions']['enabled'] == 'true':
            config.model['operations']['Transaction'] = {}
            config.model['operations']['Transaction']['methods'] = {}
            config.model['operations']['Transaction']['methods']['get'] = False
            config.model['operations']['Transaction']['methods']['post'] = True
            config.model['operations']['Transaction']['parameters'] = {}

            config.model['operations']['Harvest'] = {}
            config.model['operations']['Harvest']['methods'] = {}
            config.model['operations']['Harvest']['methods']['get'] = False
            config.model['operations']['Harvest']['methods']['post'] = True
            config.model['operations']['Harvest']['parameters'] = {}
            config.model['operations']['Harvest']['parameters']['ResourceType'] = {}
            config.model['operations']['Harvest']['parameters']['ResourceType']['values'] = config.model['operations']['GetRecords']['parameters']['outputSchema']['values']

    def _cql_update_cq_mappings(self,cql):
        self.log.debug('Raw CQL text = %s.' % cql)
        if cql is not None:
            for k,v in self.cq.mappings.iteritems():
                cql = cql.replace(k, self.cq.mappings[k]['db_col'])
            self.log.debug('Interpolated CQL text = %s.' % cql)
            return cql
