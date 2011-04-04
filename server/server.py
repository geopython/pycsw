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
import cgi
import urllib2
from lxml import etree
import config, core_queryables, filterencoding, log, profile, repository, util

class Csw(object):
    ''' Base CSW server '''
    def __init__(self, configfile=None):
        ''' Initialize CSW '''
        # load user configuration
        self.config = config.get_config(configfile)

        # configure transaction support, if specified in config
        self._gen_transactions()

        # init kvp
        self.kvp = {}

        self.gzip = False
        self.soap = False
        self.request = None
        self.exception = False

        # configure logging
        try:
            self.log = log.initlog(self.config)
        except Exception, err:
            self.response = self.exceptionreport(
            'NoApplicableCode', 'service', str(err))

        # generate domain model
        config.MODEL['operations']['GetDomain'] = config.gen_domains()

        # set OGC schemas location
        if self.config['server'].has_key('ogc_schemas_base') is False:
            self.config['server']['ogc_schemas_base'] = config.OGC_SCHEMAS_BASE

        # configure core queryables
        self.corequeryables = core_queryables.CoreQueryables(self.config)

        # set XML pretty print
        if (self.config['server'].has_key('xml_pretty_print') and
        self.config['server']['xml_pretty_print'] == 'true'):
            self.xml_pretty_print = 1
        else:
            self.xml_pretty_print = 0

        # set compression level
        if self.config['server'].has_key('gzip_compresslevel'):
            self.gzip_compresslevel = \
            int(self.config['server']['gzip_compresslevel'])
        else:
            self.gzip_compresslevel = 9

        # initialize connection to repository
        self.database = repository.Repository(self.config['repository']['db'],
        self.config['repository']['records_table'])

        # generate distributed search model, if specified in config
        if self.config['server'].has_key('federatedcatalogues') is True:
            self.log.debug('Configuring distributed search.')
            config.MODEL['constraints']['FederatedCatalogues'] = {}
            config.MODEL['constraints']['FederatedCatalogues']['values'] = []
            for fedcat in \
            self.config['server']['federatedcatalogues'].split(','):
                config.MODEL\
                ['constraints']['FederatedCatalogues']['values'].append(fedcat)

        self.log.debug('Configuration: %s.' % self.config)
        self.log.debug('Model: %s.' % config.MODEL)
        self.log.debug('Core Queryable mappings: %s.' %
        self.corequeryables.mappings)

        # load profiles
        self.log.debug('Loading profiles.')
        self.profiles = profile.load_profiles(
        os.path.join('server', 'profiles'), profile.Profile)

        for prof in self.profiles['plugins'].keys():
            self.profiles['loaded'][prof] = self.profiles['plugins'][prof]()
            self.profiles['loaded'][prof].extend_config(
            config.MODEL, config.NAMESPACES)

        self.log.debug('Profiles loaded: %s.' % self.profiles.keys())

    def dispatch(self):
        ''' Handle incoming HTTP request '''
        error = 0

        if hasattr(self,'response') is True:
            self._write_response()
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
            self.request = 'http://%s%s' % \
            (os.environ['HTTP_HOST'], os.environ['REQUEST_URI'])
            self.log.debug('Request type: GET.  Request:\n%s\n', self.request)
            for key in cgifs.keys():
                self.kvp[key.lower()] = cgifs[key].value

        # check if Accept-Encoding was passed as an HTTP header
        self.log.debug('HTTP Headers:\n%s.' % os.environ)

        if (os.environ.has_key('HTTP_ACCEPT_ENCODING') and
           os.environ['HTTP_ACCEPT_ENCODING'].find('gzip') != -1):
        # set for gzip compressed response 
            self.gzip = True
        else:
            self.gzip = False

        self.log.debug('Parsed request parameters: %s' % self.kvp)

        if error == 0:
            # test for the basic keyword values (service, version, request)
            for k in ['service', 'version', 'request']:
                if self.kvp.has_key(k) == False:
                    if (k == 'version' and self.kvp.has_key('request') and
                    self.kvp['request'] == 'GetCapabilities'):
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
                    text = 'Invalid value for service: %s.\
                    Value MUST be CSW' % self.kvp['service']
        
                # test version
                if (self.kvp.has_key('version') and
                    util.get_version_integer(self.kvp['version']) !=
                    util.get_version_integer('2.0.2') and
                    self.kvp['request'] != 'GetCapabilities'):
                    error = 1
                    locator = 'version'
                    code = 'InvalidParameterValue'
                    text = 'Invalid value for version: %s.\
                    Value MUST be 2.0.2' % self.kvp['version']
        
                # check for GetCapabilities acceptversions
                if self.kvp.has_key('acceptversions'):
                    for vers in self.kvp['acceptversions'].split(','):
                        if (util.get_version_integer(vers) ==
                            util.get_version_integer('2.0.2')):
                            break
                        else:
                            error = 1
                            locator = 'acceptversions'
                            code = 'VersionNegotiationFailed'
                            text = 'Invalid parameter value in acceptversions:\
                            %s. Value MUST be 2.0.2' % \
                            self.kvp['acceptversions']
        
                # test request
                if self.kvp['request'] not in config.MODEL['operations'].keys():
                    error = 1
                    locator = 'request'
                    if self.kvp['request'] in ['Transaction','Harvest']:
                        code = 'OperationNotSupported'
                        text = '%s operations are not supported' % \
                        self.kvp['request']
                    else:
                        code = 'InvalidParameterValue'
                        text = 'Invalid value for request: %s' % \
                        self.kvp['request']

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
                self.response = self.exceptionreport('InvalidParameterValue',
                'request', 'Invalid request parameter: %s' %
                self.kvp['request'])

        self._write_response()

    def exceptionreport(self, code, locator, text):
        ''' Generate ExceptionReport '''
        self.exception = True

        node = etree.Element(util.nspath_eval('ows:ExceptionReport'),
        nsmap=config.NAMESPACES, version='1.0.2',
        language=self.config['server']['language'])

        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/ows/1.0.0/owsExceptionReport.xsd' % \
        (config.NAMESPACES['ows'], self.config['server']['ogc_schemas_base'])

        exception = etree.SubElement(node, util.nspath_eval('ows:Exception'),
        exceptionCode=code, locator=locator)

        etree.SubElement(exception,
        util.nspath_eval('ows:ExceptionText')).text=text

        return node
    
    def getcapabilities(self):
        ''' Handle GetCapabilities request '''
        serviceidentification = True
        serviceprovider = True
        operationsmetadata = True
        if self.kvp.has_key('sections'):
            serviceidentification = False
            serviceprovider = False
            operationsmetadata = False
            for section in self.kvp['sections'].split(','):
                if section == 'ServiceIdentification':
                    serviceidentification = True
                if section == 'ServiceProvider':
                    serviceprovider = True
                if section == 'OperationsMetadata':
                    operationsmetadata = True

        node = etree.Element(util.nspath_eval('csw:Capabilities'),
        nsmap=config.NAMESPACES, version='2.0.2')

        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (config.NAMESPACES['csw'], self.config['server']['ogc_schemas_base'])

        if serviceidentification is True:
            self.log.debug('Writing section ServiceIdentification.')

            serviceidentification = etree.SubElement(node, \
            util.nspath_eval('ows:ServiceIdentification'))
            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Title')).text = \
            self.config['identification']['title']

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Abstract')).text = \
            self.config['identification']['abstract']

            keywords = etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Keywords'))

            for k in self.config['identification']['keywords'].split(','):
                etree.SubElement(
                keywords, util.nspath_eval('ows:Keyword')).text = k
            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:ServiceType'), codeSpace='OGC').text = 'CSW'

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:ServiceTypeVersion')).text = '2.0.2'

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Fees')).text = \
            self.config['identification']['fees']

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:AccessConstraints')).text = \
            self.config['identification']['accessconstraints']

        if serviceprovider is True:
            self.log.debug('Writing section ServiceProvider.')
            serviceprovider = etree.SubElement(node,
            util.nspath_eval('ows:ServiceProvider'))

            etree.SubElement(serviceprovider,
            util.nspath_eval('ows:ProviderName')).text = \
            self.config['provider']['name']

            providersite = etree.SubElement(serviceprovider,
            util.nspath_eval('ows:ProviderSite'))

            providersite.attrib[util.nspath_eval('xlink:type')] = 'simple'
            providersite.attrib[util.nspath_eval('xlink:href')] = \
            self.config['provider']['url']

            servicecontact = etree.SubElement(serviceprovider,
            util.nspath_eval('ows:ServiceContact'))

            etree.SubElement(servicecontact,
            util.nspath_eval('ows:IndividualName')).text = \
            self.config['contact']['name']

            etree.SubElement(servicecontact,
            util.nspath_eval('ows:PositionName')).text = \
            self.config['contact']['position']

            contactinfo = etree.SubElement(servicecontact,
            util.nspath_eval('ows:ContactInfo'))

            phone = etree.SubElement(contactinfo, util.nspath_eval('ows:Phone'))
            etree.SubElement(phone, util.nspath_eval('ows:Voice')).text = \
            self.config['contact']['phone']

            etree.SubElement(phone, util.nspath_eval('ows:Facsimile')).text = \
            self.config['contact']['fax']

            address = etree.SubElement(contactinfo,
            util.nspath_eval('ows:Address'))

            etree.SubElement(address,
            util.nspath_eval('ows:DeliveryPoint')).text = \
            self.config['contact']['address']

            etree.SubElement(address, util.nspath_eval('ows:City')).text = \
            self.config['contact']['city']

            etree.SubElement(address,
            util.nspath_eval('ows:AdministrativeArea')).text = \
            self.config['contact']['stateorprovince']

            etree.SubElement(address,
            util.nspath_eval('ows:PostalCode')).text = \
            self.config['contact']['postalcode']

            etree.SubElement(address, util.nspath_eval('ows:Country')).text = \
            self.config['contact']['country']

            etree.SubElement(address,
            util.nspath_eval('ows:ElectronicMailAddress')).text = \
            self.config['contact']['email']

            url = etree.SubElement(contactinfo,
            util.nspath_eval('ows:OnlineResource'))

            url.attrib[util.nspath_eval('xlink:type')] = 'simple'
            url.attrib[util.nspath_eval('xlink:href')] = \
            self.config['contact']['url']

            etree.SubElement(contactinfo,
                             util.nspath_eval('ows:HoursOfService')).text = \
                             self.config['contact']['hours']

            etree.SubElement(contactinfo,
            util.nspath_eval('ows:ContactInstructions')).text = \
            self.config['contact']['contactinstructions']

            etree.SubElement(servicecontact,
            util.nspath_eval('ows:Role')).text = self.config['contact']['role']

        if operationsmetadata is True:
            self.log.debug('Writing section OperationsMetadata.')
            operationsmetadata = etree.SubElement(node,
            util.nspath_eval('ows:OperationsMetadata'))

            for operation in config.MODEL['operations'].keys():
                oper = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows:Operation'), name = operation)

                dcp = etree.SubElement(oper, util.nspath_eval('ows:DCP'))
                http = etree.SubElement(dcp, util.nspath_eval('ows:HTTP'))

                if (config.MODEL['operations'][operation]['methods']['get']
                    is True):
                    get = etree.SubElement(http, util.nspath_eval('ows:Get'))
                    get.attrib[util.nspath_eval('xlink:type')] = 'simple'
                    get.attrib[util.nspath_eval('xlink:href')] = \
                    self.config['server']['url']

                if (config.MODEL['operations'][operation]['methods']['post']
                    is True):
                    post = etree.SubElement(http, util.nspath_eval('ows:Post'))
                    post.attrib[util.nspath_eval('xlink:type')] = 'simple'
                    post.attrib[util.nspath_eval('xlink:href')] = \
                    self.config['server']['url']

                for parameter in \
                config.MODEL['operations'][operation]['parameters']:
                    param = etree.SubElement(oper,
                    util.nspath_eval('ows:Parameter'), name = parameter)

                    for val in \
                    config.MODEL['operations'][operation]\
                    ['parameters'][parameter]['values']:
                        etree.SubElement(param,
                        util.nspath_eval('ows:Value')).text = val

                if operation == 'GetRecords':
                    param = etree.SubElement(oper,
                    util.nspath_eval('ows:Constraint'),
                    name = 'SupportedDublinCoreQueryables')

                    for val in self.corequeryables.mappings.keys():
                        etree.SubElement(param,
                        util.nspath_eval('ows:Value')).text = val

            for parameter in config.MODEL['parameters'].keys():
                param = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows:Parameter'), name = parameter)
                for val in config.MODEL['parameters'][parameter]['values']:
                    etree.SubElement(param,
                    util.nspath_eval('ows:Value')).text = val

            for constraint in config.MODEL['constraints'].keys():
                param = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows:Constraint'), name = constraint)
                for val in config.MODEL['constraints'][constraint]['values']:
                    etree.SubElement(param,
                    util.nspath_eval('ows:Value')).text = val
            
            extended_capabilities = etree.SubElement(operationsmetadata,
            util.nspath_eval('ows:ExtendedCapabilities'))

            for prof in self.profiles['loaded'].keys():
                extended_capabilities.append(
                self.profiles['loaded'][prof].get_extendedcapabilities())

        # always write out Filter_Capabilities
        self.log.debug('Writing section Filter_Capabilities.')
        fltcaps = etree.SubElement(node,
        util.nspath_eval('ogc:Filter_Capabilities'))
        spatialcaps = etree.SubElement(fltcaps,
        util.nspath_eval('ogc:Spatial_Capabilities'))

        geomops = etree.SubElement(spatialcaps,
        util.nspath_eval('ogc:GeometryOperands'))

        etree.SubElement(geomops,
        util.nspath_eval('ogc:GeometryOperand')).text = 'gml:Envelope'
    
        spatialops = etree.SubElement(spatialcaps,
        util.nspath_eval('ogc:SpatialOperators'))

        etree.SubElement(spatialops, util.nspath_eval('ogc:SpatialOperator'),
        name = 'BBOX')
    
        scalarcaps = etree.SubElement(fltcaps,
        util.nspath_eval('ogc:Scalar_Capabilities'))

        etree.SubElement(scalarcaps, util.nspath_eval('ogc:LogicalOperators'))
        
        cmpops = etree.SubElement(scalarcaps,
        util.nspath_eval('ogc:ComparisonOperators'))
    
        for cmpop in ['LessThan', 'GreaterThan', 'LessThanEqualTo', \
        'GreaterThanEqualTo', 'EqualTo', 'NotEqualTo', 'Like', 'Between', \
        'NullCheck']:
            etree.SubElement(cmpops,
            util.nspath_eval('ogc:ComparisonOperator')).text = cmpop
    
        idcaps = etree.SubElement(fltcaps,
        util.nspath_eval('ogc:Id_Capabilities'))

        etree.SubElement(idcaps, util.nspath_eval('ogc:EID'))
        etree.SubElement(idcaps, util.nspath_eval('ogc:FID'))

        return node
    
    def describerecord(self):
        ''' Handle DescribeRecord request '''
        csw = False
    
        if self.kvp.has_key('typename') and len(self.kvp['typename']) > 0:
            for typename in self.kvp['typename']:
                if typename == 'csw:Record':  # return only csw
                    csw = True
        else:
            csw = True
    
        if (self.kvp.has_key('outputformat') and
            self.kvp['outputformat'] not in
            config.MODEL['operations']['DescribeRecord']
            ['parameters']['outputFormat']['values']):  # bad outputformat
            return self.exceptionreport('InvalidParameterValue',
            'outputformat', 'Invalid value for outputformat: %s' %
            self.kvp['outputformat'])
    
        if (self.kvp.has_key('schemalanguage') and
            self.kvp['schemalanguage'] not in
            config.MODEL['operations']['DescribeRecord']['parameters']
            ['schemaLanguage']['values']):  # bad schemalanguage
            return self.exceptionreport('InvalidParameterValue',
            'schemalanguage', 'Invalid value for schemalanguage: %s' %
            self.kvp['schemalanguage'])

        node = etree.Element(util.nspath_eval('csw:DescribeRecordResponse'),
        nsmap = config.NAMESPACES)

        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (config.NAMESPACES['csw'], self.config['server']['ogc_schemas_base'])

        if csw is True:
            self.log.debug('Writing csw:Record schema.')
            schemacomponent = etree.SubElement(node,
            util.nspath_eval('csw:SchemaComponent'),
            schemaLanguage='XMLSCHEMA',
            targetNamespace = config.NAMESPACES['csw'])
            dublincore = etree.parse(os.path.join(self.config['server']['home'],
            'etc', 'schemas', 'ogc', 'csw', '2.0.2', 'record.xsd')).getroot()

            schemacomponent.append(dublincore)

        return node
    
    def getdomain(self):
        ''' Handle GetDomain request '''
        if (self.kvp.has_key('parametername') is False and
            self.kvp.has_key('propertyname') is False):
            return self.exceptionreport('MissingParameterValue',
            'parametername', 'Missing value. \
            One of propertyname or parametername must be specified')

        node = etree.Element(util.nspath_eval('csw:GetDomainResponse'),
        nsmap = config.NAMESPACES)

        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (config.NAMESPACES['csw'], self.config['server']['ogc_schemas_base'])

        if self.kvp.has_key('parametername'):
            for pname in self.kvp['parametername'].split(','):
                self.log.debug('Parsing parametername %s.' % pname)
                domainvalue = etree.SubElement(node,
                util.nspath_eval('csw:DomainValues'), type = 'csw:Record')
                etree.SubElement(domainvalue,
                util.nspath_eval('csw:ParameterName')).text = pname
                operation, parameter = pname.split('.')
                if (operation in config.MODEL['operations'].keys() and
                    parameter in
                    config.MODEL['operations'][operation]['parameters'].keys()):
                    listofvalues = etree.SubElement(domainvalue,
                    util.nspath_eval('csw:ListOfValues'))
                    for val in \
                    config.MODEL['operations'][operation]\
                    ['parameters'][parameter]['values']:
                        etree.SubElement(listofvalues,
                        util.nspath_eval('csw:Value')).text = val

        if self.kvp.has_key('propertyname'):
            for pname in self.kvp['propertyname'].split(','):
                self.log.debug('Parsing propertyname %s.' % pname)
                domainvalue = etree.SubElement(node,
                util.nspath_eval('csw:DomainValues'), type = 'csw:Record')
                etree.SubElement(domainvalue,
                util.nspath_eval('csw:PropertyName')).text = pname

                try:
                    tmp = self.corequeryables.mappings[pname]['obj_attr']
                    self.log.debug('Querying database on property %s (%s).' %
                    (pname, tmp))
                    results = self.database.query(propertyname=tmp)
                    self.log.debug('Results: %s' %str(len(results)))
                    listofvalues = etree.SubElement(domainvalue,
                    util.nspath_eval('csw:ListOfValues'))
                    for result in results:
                        etree.SubElement(listofvalues,
                        util.nspath_eval('csw:Value')).text = result[0]
                except Exception, err:
                    self.log.debug('No results for propertyname %s: %s.' %
                    (pname, str(err)))

        return node

    def getrecords(self):
        ''' Handle GetRecords request '''

        timestamp = util.get_today_and_now()

        if (self.kvp.has_key('elementsetname') is False and
            self.kvp.has_key('elementname') is False):
            # mutually exclusive required
            return self.exceptionreport('MissingParameterValue',
            'elementsetname',
            'Missing one of ElementSetName or ElementName parameter(s)')

        if self.kvp.has_key('outputschema') is False:
            self.kvp['outputschema'] = config.NAMESPACES['csw']

        if (self.kvp['outputschema'] not in config.MODEL['operations']
            ['GetRecords']['parameters']['outputSchema']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputschema', 'Invalid outputSchema parameter value: %s' %
            self.kvp['outputschema'])

        if self.kvp.has_key('outputformat') is False:
            self.kvp['outputformat'] = 'application/xml'
     
        if (self.kvp['outputformat'] not in config.MODEL['operations']
            ['GetRecords']['parameters']['outputFormat']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputformat', 'Invalid outputFormat parameter value: %s' %
            self.kvp['outputformat'])

        if self.kvp.has_key('resulttype') is False:
            self.kvp['resulttype'] = 'hits'

        if self.kvp['resulttype'] is not None:
            if (self.kvp['resulttype'] not in config.MODEL['operations']
            ['GetRecords']['parameters']['resultType']['values']):
                return self.exceptionreport('InvalidParameterValue',
                'resulttype', 'Invalid resultType parameter value: %s' %
                self.kvp['resulttype'])

        if ((self.kvp.has_key('elementname') is False or 
             len(self.kvp['elementname']) == 0) and
             self.kvp['elementsetname'] not in
             config.MODEL['operations']['GetRecords']['parameters']
             ['ElementSetName']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'elementsetname', 'Invalid ElementSetName parameter value: %s' %
            self.kvp['elementsetname'])

        if self.kvp['resulttype'] == 'validate':
            node = etree.Element(util.nspath_eval('csw:Acknowledgement'),
            nsmap = config.NAMESPACES, timeStamp = timestamp)

            node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
            '%s %s/csw/2.0.2/CSW-discovery.xsd' % (config.NAMESPACES['csw'], \
            self.config['server']['ogc_schemas_base'])

            node1 = etree.SubElement(node,
            util.nspath_eval('csw:EchoedRequest'))
            node1.append(etree.fromstring(self.request))

            return node

        if self.kvp.has_key('maxrecords') is False:
            self.kvp['maxrecords'] = self.config['server']['maxrecords']

        if (self.kvp.has_key('constraint') is True and
            (self.kvp.has_key('filter') is False and
             self.kvp.has_key('cql') is False)):  # GET request
            self.log.debug('csw:Constraint passed over HTTP GET.')
            if self.kvp.has_key('constraintlanguage') is False:
                return self.exceptionreport('MissingParameterValue',
                'constraintlanguage',
                'constraintlanguage required when constraint specified')
            if (self.kvp['constraintlanguage'] not in
            config.MODEL['operations']['GetRecords']['parameters']
            ['CONSTRAINTLANGUAGE']['values']):
                return self.exceptionreport('InvalidParameterValue',
                'constraintlanguage', 'Invalid constraintlanguage: %s'
                % self.kvp['constraintlanguage'])
            if self.kvp['constraintlanguage'] == 'CQL_TEXT':
                self.kvp['cql'] = self.kvp['constraint']
                self.kvp['cql'] = \
                self._cql_update_cq_mappings(self.kvp['constraint'])

                self.kvp['filter'] = None
            elif self.kvp['constraintlanguage'] == 'FILTER':

                # validate filter XML
                try:
                    schema = os.path.join(self.config['server']['home'],
                    'etc', 'schemas', 'ogc', 'filter', '1.1.0', 'filter.xsd')
                    self.log.debug('Validating Filter %s.' %
                    self.kvp['constraint'])
                    schema = etree.XMLSchema(etree.parse(schema))
                    parser = etree.XMLParser(schema=schema)
                    doc = etree.fromstring(self.kvp['constraint'], parser)
                    self.log.debug('Filter is valid XML.')
                    self.kvp['filter'] = \
                    filterencoding.Filter(doc, self.corequeryables.mappings)
                except Exception, err:
                    errortext = \
                    'Exception: document not valid.\nError: %s.' % str(err)

                    self.log.debug(errortext)
                    return self.exceptionreport('InvalidParameterValue',
                    'constraint', 'Invalid Filter query: %s' % errortext)

                self.kvp['cql'] = None

        if self.kvp.has_key('filter') is False:
            self.kvp['filter'] = None
        if self.kvp.has_key('cql') is False:
            self.kvp['cql'] = None

        if self.kvp.has_key('sortby') is False:
            self.kvp['sortby'] = None

        if self.kvp.has_key('startposition') is False:
            self.kvp['startposition'] = 1

        self.log.debug('Querying database with filter: %s,\
        cql: %s, sortby: %s.' %
        (self.kvp['filter'], self.kvp['cql'], self.kvp['sortby']))

        try:
            results = self.database.query(flt = self.kvp['filter'],
            cql = self.kvp['cql'], sortby=self.kvp['sortby'])
        except Exception, err:
            return self.exceptionreport('InvalidParameterValue', 'constraint',
            'Invalid query: %s' % err)

        if results is None:
            matched = '0'
            returned = '0'
            nextrecord = '0'

        else:
            matched = str(len(results))
            if int(matched) < int(self.kvp['maxrecords']):
                returned = str(int(matched))
                nextrecord = '0'
            else:
                returned = str(self.kvp['maxrecords'])
                nextrecord = str(int(self.kvp['startposition']) + \
                int(self.kvp['maxrecords']))
            if int(self.kvp['maxrecords']) == 0:
                nextrecord = '1'

        dsresults = []

        if (self.config['server'].has_key('federatedcatalogues') and
            self.kvp['distributedsearch'] == 'TRUE' and
            self.kvp['hopcount'] > 0):  # do distributed search

            self.log.debug('DistributedSearch specified (hopCount=%s.' %
            self.kvp['hopcount'])

            from owslib.csw import CatalogueServiceWeb
            for fedcat in \
            self.config['server']['federatedcatalogues'].split(','):
                self.log.debug('Performing distributed search on federated \
                catalogue: %s.' % fedcat)
                remotecsw = CatalogueServiceWeb(fedcat)
                remotecsw.getrecords(xml=self.request)
                self.log.debug('Distributed search results from catalogue \
                %s: %s.' % (fedcat, remotecsw.results))
                matched = str(int(matched) + int(remotecsw.results['matches']))
                dsresults.append(remotecsw.records)

        self.log.debug('Results: matched: %s, returned: %s, next: %s.' % \
        (matched, returned, nextrecord))

        node = etree.Element(util.nspath_eval('csw:GetRecordsResponse'),
        nsmap = config.NAMESPACES, version='2.0.2')

        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (config.NAMESPACES['csw'], self.config['server']['ogc_schemas_base'])

        etree.SubElement(node, util.nspath_eval('csw:SearchStatus'),
        timestamp=timestamp)

        if self.kvp['filter'] is None and self.kvp['resulttype'] is None:
            returned = '0'

        searchresults = etree.SubElement(node,
        util.nspath_eval('csw:SearchResults'),
        numberOfRecordsMatched = matched, numberOfRecordsReturned = returned,
        nextRecord = nextrecord, recordSchema = self.kvp['outputschema'])

        if self.kvp['filter'] is None and self.kvp['resulttype'] is None:
            self.log.debug('Empty result set returned.')
            return node

        max1 = int(self.kvp['startposition']) + int(self.kvp['maxrecords'])
 
        if results is not None:
            self.log.debug('Presenting records %s - %s.' %
            (self.kvp['startposition'], max1))

            for res in results[int(self.kvp['startposition'])-1:int(max1)-1]:
                searchresults.append(self._write_record(res))

        if (self.kvp.has_key('distributedsearch') and
            self.kvp['distributedsearch'] == 'TRUE' and
            self.kvp['hopcount'] > 0):
            for resultset in dsresults:
                for rec in resultset:
                    searchresults.append(etree.fromstring(resultset[rec].xml))

        return node

    def getrecordbyid(self):
        ''' Handle GetRecordById request '''

        if self.kvp.has_key('id') is False:
            return self.exceptionreport('MissingParameterValue', 'id',
            'Missing id parameter')
        if len(self.kvp['id']) < 1:
            return self.exceptionreport('InvalidParameterValue', 'id',
            'Invalid id parameter')

        ids = self.kvp['id'].split(',')

        if (self.kvp.has_key('outputformat') and
            self.kvp['outputformat'] not in
            config.MODEL['operations']['GetRecordById']['parameters']
            ['outputFormat']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputformat', 'Invalid outputformat parameter %s' %
            self.kvp['outputformat'])

        if (self.kvp.has_key('outputschema') and self.kvp['outputschema'] not in
            config.MODEL['operations']['GetRecordById']['parameters']
            ['outputSchema']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputschema', 'Invalid outputschema parameter %s' %
            self.kvp['outputschema'])

        if self.kvp.has_key('elementsetname') is False:
            self.kvp['elementsetname'] = 'summary'
        else:
            if (self.kvp['elementsetname'] not in
                config.MODEL['operations']['GetRecordById']['parameters']
                ['ElementSetName']['values']):
                return self.exceptionreport('InvalidParameterValue',
                'elementsetname', 'Invalid elementsetname parameter %s' %
                self.kvp['elementsetname'])
            if self.kvp['elementsetname'] == 'full':
                self.kvp['elementsetname'] = ''
            else:
                self.kvp['elementsetname'] = self.kvp['elementsetname']

        self.log.debug('Querying database with ids: %s.' % ids)
        results = self.database.query(ids=ids)

        node = etree.Element(util.nspath_eval('csw:GetRecordByIdResponse'),
        nsmap = config.NAMESPACES)
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (config.NAMESPACES['csw'], self.config['server']['ogc_schemas_base'])

        self.log.debug('Presenting %s records.' % str(len(results)))
        for result in results:
            node.append(self._write_record(result))

        return node

    def transaction(self):
        ''' Handle Transaction request '''

        if self.config['transactions']['enabled'] != 'true':
            return self.exceptionreport('OperationNotSupported',
            'transaction', 'Transaction operations are not supported')
        ipaddress = os.environ['REMOTE_ADDR']
        if ipaddress not in self.config['transactions']['ips'].split(','):
            return self.exceptionreport('NoApplicableCode', 'transaction',
            'Transactions not enabled from this IP address: %s' % ipaddress)

        node = etree.Element(util.nspath_eval('csw:TransactionResponse'),
        nsmap = config.NAMESPACES, version = '2.0.2')

        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/CSW-publication.xsd' % \
        (config.NAMESPACES['csw'], self.config['server']['ogc_schemas_base'])

        return node

    def harvest(self):
        ''' Handle Harvest request '''

        if self.config['transactions']['enabled'] != 'true':
            return self.exceptionreport('OperationNotSupported', 'harvest',
            'Harvest is not supported')
        ipaddress = os.environ['REMOTE_ADDR']
        if ipaddress not in self.config['transactions']['ips'].split(','):
            return self.exceptionreport('NoApplicableCode', 'harvest',
            'Harvest operations are not enabled from this IP address: %s' %
            ipaddress)

        # validate resourcetype
        if (self.kvp['resourcetype'] not in
            config.MODEL['operations']['Harvest']['parameters']['ResourceType']
            ['values']):
            return self.exceptionreport('InvalidParameterValue',
            'resourcetype', 'Invalid resource type parameter: %s.\
            Allowable resourcetype values: %s' % (self.kvp['resourcetype'],
            ','.join(config.MODEL['operations']['Harvest']['parameters']
            ['ResourceType']['values'])))

        # fetch resource
        try:
            req = urllib2.Request(self.kvp['source'])
            req.add_header('User-Agent', 'pycsw (http://pycsw.org/)')
            content = urllib2.urlopen(req).read() 
        except Exception, err:
            errortext = 'Error fetching document %s.\nError: %s.' % \
            (self.kvp['source'], str(err))
            self.log.debug(errortext)
            return self.exceptionreport('InvalidParameterValue', 'source',
            errortext)

        node = etree.Element(util.nspath_eval('csw:HarvestResponse'),
        nsmap = config.NAMESPACES)
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/CSW-publication.xsd' % (config.NAMESPACES['csw'],
        self.config['server']['ogc_schemas_base'])
        etree.SubElement(node,'hi').text = content

        return node

    def parse_postdata(self, postdata):
        ''' Parse POST XML '''

        request = {}
        try:
            self.log.debug('Parsing %s.' % postdata)
            doc = etree.fromstring(postdata)
        except Exception, err:
            errortext = \
            'Exception: document not well-formed.\nError: %s.' % str(err)

            self.log.debug(errortext)
            return errortext

        # if this is a SOAP request, get to SOAP-ENV:Body/csw:*
        if doc.tag == util.nspath_eval('soapenv:Envelope'):
            self.log.debug('SOAP request specified.')
            self.soap = True
            doc = doc.find(
            util.nspath_eval('soapenv:Body')).xpath('child::*')[0]

        if (doc.tag in [util.nspath_eval('csw:Transaction'),
            util.nspath_eval('csw:Harvest')]):
            schema = os.path.join(self.config['server']['home'], 'etc',
            'schemas', 'ogc', 'csw', '2.0.2', 'CSW-publication.xsd')
        else:
            schema = os.path.join(self.config['server']['home'], 'etc',
            'schemas', 'ogc', 'csw', '2.0.2', 'CSW-discovery.xsd')

        try:
            self.log.debug('Validating %s.' % postdata)
            schema = etree.XMLSchema(etree.parse(schema))
            parser = etree.XMLParser(schema=schema)
            if hasattr(self, 'soap') is True and self.soap is True:
            # validate the body of the SOAP request
                doc = etree.fromstring(etree.tostring(doc), parser)
            else:  # validate the request normally
                doc = etree.fromstring(postdata, parser)
            self.log.debug('Request is valid XML.')
        except Exception, err:
            errortext = \
            'Exception: the document is not valid.\nError: %s.' % str(err)
            self.log.debug(errortext)
            return errortext

        request['request'] = util.xmltag_split(doc.tag)
        self.log.debug('Request operation %s specified.' % request['request'])
        tmp = doc.find('.').attrib.get('service')
        if tmp is not None:
            request['service'] = tmp

        tmp = doc.find('.').attrib.get('version')
        if tmp is not None:
            request['version'] = tmp

        tmp = doc.find('.//%s' % util.nspath_eval('ows:Version'))
        if tmp is not None:
            request['version'] = tmp.text
    
        # DescribeRecord
        if request['request'] == 'DescribeRecord':
            request['typename'] = []
            for typename in doc.findall(util.nspath_eval('csw:TypeName')):
                request['typename'].append(typename.text)
    
            tmp = doc.find('.').attrib.get('schemaLanguage')
            if tmp is not None:
                request['schemalanguage'] = tmp
    
            tmp = doc.find('.').attrib.get('outputFormat')
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
            tmp = doc.find('.').attrib.get('outputSchema')
            if tmp is not None:
                request['outputschema'] = tmp
            else:
                request['outputschema'] = config.NAMESPACES['csw']

            tmp = doc.find('.').attrib.get('resultType')
            if tmp is not None:
                request['resulttype'] = tmp
            else:
                request['resulttype'] = None

            tmp = doc.find('.').attrib.get('outputFormat')
            if tmp is not None:
                request['outputformat'] = tmp
            else:
                request['outputformat'] = 'application/xml'

            tmp = doc.find('.').attrib.get('startPosition')
            if tmp is not None:
                request['startposition'] = tmp
            else:
                request['startposition'] = 1

            tmp = doc.find('.').attrib.get('maxRecords')
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
                hopcount = tmp.attrib.get('hopCount')
                if hopcount is not None:
                    request['hopcount'] = int(hopcount)-1
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
            for elname in \
            doc.findall(util.nspath_eval('csw:Query/csw:ElementName')):
                request['elementname'].append(elname.text)

            request['filter'] = None
            request['cql'] = None

            tmp = doc.find(util.nspath_eval('csw:Query/csw:Constraint'))
            if tmp is not None:
                ctype = tmp.xpath('child::*')

                try: 
                    if ctype[0].tag == util.nspath_eval('ogc:Filter'):
                        self.log.debug('Filter constraint specified.')
                        try:
                            request['filter'] = \
                            filterencoding.Filter(ctype[0],
                            self.corequeryables.mappings)
                        except Exception, err:
                            return 'Invalid Filter request: %s' % err
                    elif ctype[0].tag == util.nspath_eval('csw:CqlText'):
                        self.log.debug('CQL specified: %s.' % ctype[0].text)
                        request['cql'] = \
                        self._cql_update_cq_mappings(ctype[0].text)
                    else:
                        return 'ogc:Filter or csw:CqlText is required'
                except Exception, err:
                    return 'ogc:Filter or csw:CqlText is required'
            else: 
                self.log.debug('No csw:Constraint (ogc:Filter or csw:CqlText) \
                specified.')

            tmp = doc.find(util.nspath_eval('csw:Query/ogc:SortBy'))
            if tmp is not None:
                self.log.debug('Sorted query specified.')
                request['sortby'] = {}
                request['sortby']['propertyname'] = \
                tmp.find(util.nspath_eval(
                'ogc:SortProperty/ogc:PropertyName')).text
                request['sortby']['cq_mapping'] = \
                self.corequeryables.mappings[tmp.find(util.nspath_eval(\
                'ogc:SortProperty/ogc:PropertyName')).text.lower()]['db_col']

                tmp2 =  tmp.find(util.nspath_eval(
                'ogc:SortProperty/ogc:SortOrder'))
                if tmp2 is not None:                   
                    request['sortby']['order'] = tmp2.text
                else:
                    request['sortby']['order'] = 'asc'
            else:
                request['sortby'] = None

        # GetRecordById
        if request['request'] == 'GetRecordById':
            ids = []
            for id1 in doc.findall(util.nspath_eval('csw:Id')):
                ids.append(id1.text)

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
            request['resourcetype'] = \
            doc.find(util.nspath_eval('csw:ResourceType')).text

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

    def _write_record(self, recobj):
        ''' Generate csw:Record '''
        if self.kvp['elementsetname'] == 'brief':
            elname = 'BriefRecord'
        elif self.kvp['elementsetname'] == 'summary':
            elname = 'SummaryRecord'
        else:
            elname = 'Record'

        record = etree.Element(util.nspath_eval('csw:%s' % elname))

        bbox = getattr(recobj,
        self.corequeryables.mappings['ows:BoundingBox']['obj_attr'])

        if (self.kvp.has_key('elementname') is True and
            len(self.kvp['elementname']) > 0):
            for elemname in self.kvp['elementname']:
                nspace, elname = elemname.split(':')
                if elname == 'BoundingBox':
                    bboxel = write_boundingbox(bbox)
                    if bboxel is not None:
                        record.append(bboxel)
                else:
                    if (hasattr(recobj,
                        self.corequeryables.mappings[elemname]['obj_attr'])
                        is True):
                        etree.SubElement(record, util.nspath_eval('%s:%s' %
                        (nspace, elname))).text=getattr(recobj,
                        self.corequeryables.mappings[elemname]['obj_attr'])
        elif self.kvp.has_key('elementsetname') is True:
            if self.kvp['elementsetname'] == 'full':  # dump the full record
                record = etree.fromstring(getattr(recobj,
                self.corequeryables.mappings['csw:AnyText']['obj_attr']))
            else:  # dump BriefRecord (always required), summary if requested
                for i in ['dc:identifier', 'dc:title', 'dc:type']:
                    etree.SubElement(record, util.nspath_eval(i)).text = \
                    getattr(recobj, self.corequeryables.mappings[i]['obj_attr'])
                if self.kvp['elementsetname'] == 'summary':
                    subjects = getattr(recobj,
                    self.corequeryables.mappings['dc:subject']['obj_attr'])

                    if subjects is not None:
                        for subject in subjects.split(','):
                            etree.SubElement(record, 
                            util.nspath_eval('dc:subject')).text=subject

                    for i in ['dc:format', 'dc:relation', \
                    'dct:modified', 'dct:abstract']:
                        val = getattr(recobj,
                        self.corequeryables.mappings[i]['obj_attr'])
                        if val is not None:
                            etree.SubElement(record,
                            util.nspath_eval(i)).text = val
                bboxel = write_boundingbox(bbox)
                if bboxel is not None:
                    record.append(bboxel)

        return record

    def _write_response(self):
        ''' Generate response '''
        # set HTTP response headers and XML declaration
        self.log.debug('Writing response.')
        http_header = 'Content-type:%s\r\n' % self.config['server']['mimetype']
        xmldecl = '<?xml version="1.0" encoding="%s" standalone="no"?>\n' % \
        self.config['server']['encoding']
        appinfo = '<!-- pycsw %s -->\n' % config.VERSION

        if hasattr(self, 'soap') and self.soap is True:
            self._gen_soap_wrapper() 

        response = etree.tostring(self.response,
        pretty_print = self.xml_pretty_print)

        self.log.debug('Response:\n%s' % response)

        if self.gzip is True:
            import gzip
            from cStringIO import StringIO

            buf = StringIO()
            gzipfile = gzip.GzipFile(mode='wb', fileobj = buf,
            compresslevel = self.gzip_compresslevel)
            gzipfile.write('%s%s%s' % (xmldecl, appinfo, response))
            gzipfile.close()

            value = buf.getvalue()

            sys.stdout.write(http_header)
            sys.stdout.write('Content-Encoding: gzip\r\n')
            sys.stdout.write('Content-Length: %d\r\n' % len(value))
            sys.stdout.write('\r\n')
            sys.stdout.write(value)
        else:
            sys.stdout.write('%s\r\n%s%s%s' %
            (http_header, xmldecl, appinfo, response))

    def _gen_soap_wrapper(self):
        ''' Generate SOAP wrapper '''
        self.log.debug('Writing SOAP wrapper.')
        node = etree.Element(util.nspath_eval('soapenv:Envelope'),
        nsmap = config.NAMESPACES)
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s %s' % \
        (config.NAMESPACES['soapenv'], config.NAMESPACES['soapenv']) 

        node2 = etree.SubElement(node, util.nspath_eval('soapenv:Body'))

        if hasattr(self, 'exception') and self.exception is True:
            node3 = etree.SubElement(node2, util.nspath_eval('soapenv:Fault'))
            node4 = etree.SubElement(node3, util.nspath_eval('soapenv:Code'))
            etree.SubElement(node4, util.nspath_eval('soapenv:Value')).text = \
           'soap:Server'
            node4 = etree.SubElement(node3, util.nspath_eval('soapenv:Reason'))
            etree.SubElement(node4, util.nspath_eval('soapenv:Text')).text = \
            'A server exception was encountered.'
            node4 = etree.SubElement(node3, util.nspath_eval('soapenv:Detail'))
            node4.append(self.response)
        else:
            node2.append(self.response)

        self.response = node

    def _gen_transactions(self):
        ''' Update config.MODEL with CSW-T advertising '''
        if (self.config.has_key('transactions') is True and
            self.config['transactions'].has_key('enabled') is True and
            self.config['transactions']['enabled'] == 'true'):
            config.MODEL['operations']['Transaction'] = {}
            config.MODEL['operations']['Transaction']['methods'] = {}
            config.MODEL['operations']['Transaction']['methods']['get'] = False
            config.MODEL['operations']['Transaction']['methods']['post'] = True
            config.MODEL['operations']['Transaction']['parameters'] = {}

            config.MODEL['operations']['Harvest'] = {}
            config.MODEL['operations']['Harvest']['methods'] = {}
            config.MODEL['operations']['Harvest']['methods']['get'] = False
            config.MODEL['operations']['Harvest']['methods']['post'] = True
            config.MODEL['operations']['Harvest']['parameters'] = {}
            config.MODEL['operations']['Harvest']['parameters']\
            ['ResourceType'] = {}
            config.MODEL['operations']['Harvest']['parameters']['ResourceType']\
            ['values'] = config.MODEL['operations']['GetRecords']['parameters']\
            ['outputSchema']['values']

    def _cql_update_cq_mappings(self, cql):
        ''' Transform CQL query's properties to underlying DB columns '''
        self.log.debug('Raw CQL text = %s.' % cql)
        if cql is not None:
            for key in self.corequeryables.mappings.keys():
                cql = cql.replace(key,
                self.corequeryables.mappings[key]['db_col'])
            self.log.debug('Interpolated CQL text = %s.' % cql)
            return cql

def write_boundingbox(bbox):
    ''' Generate ows:BoundingBox '''
    if bbox is not None:
        bbox2 = bbox.split(',')
        if len(bbox2) == 4:
            boundingbox = etree.Element(util.nspath_eval('ows:BoundingBox'),
            crs = 'urn:x-ogc:def:crs:EPSG:6.11:4326')
            etree.SubElement(boundingbox,
            util.nspath_eval('ows:LowerCorner')).text = \
            '%s %s' % (bbox2[1], bbox2[0])
            etree.SubElement(boundingbox,
            util.nspath_eval('ows:UpperCorner')).text = \
            '%s %s' % (bbox2[3], bbox2[2])
            return boundingbox
        else:
            return None
    else:
        return None
