# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#                Angelos Tzotsos <tzotsos@gmail.com>
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
import urlparse
from cStringIO import StringIO
import ConfigParser
from lxml import etree
from shapely.wkt import loads
import config, fes, log, metadata, plugins.profiles.profile, repository, util

class Csw(object):
    ''' Base CSW server '''
    def __init__(self, configfile=None):
        ''' Initialize CSW '''

        # init kvp
        self.kvp = {}

        self.mode = 'csw'
        self.gzip = False
        self.soap = False
        self.request = None
        self.exception = False
        self.profiles = None
        self.mimetype = 'application/xml; charset=UTF-8'
        self.encoding = 'UTF-8'
        self.pretty_print = 0
        self.domainquerytype = 'list'

        # load user configuration
        try:
            self.config = ConfigParser.SafeConfigParser()
            self.config.readfp(open(configfile))
        except Exception, err:
            self.response = self.exceptionreport(
            'NoApplicableCode', 'service',
            'Error opening configuration %s' % configfile)
            return

        # configure transaction support, if specified in config
        self._gen_manager()

        # configure logging
        try:
            self.log = log.initlog(self.config)
        except Exception, err:
            self.response = self.exceptionreport(
            'NoApplicableCode', 'service', str(err))
            return

        self.log.debug('running configuration %s' % configfile)
        self.log.debug(str(os.environ['QUERY_STRING']))

        # generate domain model
        config.MODEL['operations']['GetDomain'] = config.gen_domains()

        # set OGC schemas location
        if not self.config.has_option('server', 'ogc_schemas_base'):
            self.config.set('server', 'ogc_schemas_base', config.OGC_SCHEMAS_BASE)

        # set mimetype
        if self.config.has_option('server', 'mimetype'):
            self.mimetype = self.config.get('server', 'mimetype')

        # set encoding
        if self.config.has_option('server', 'encoding'):
            self.encoding = self.config.get('server', 'encoding')

        # set domainquerytype
        if self.config.has_option('server', 'domainquerytype'):
            self.domainquerytype = self.config.get('server', 'domainquerytype')

        # set XML pretty print
        if (self.config.has_option('server', 'pretty_print') and
        self.config.get('server', 'pretty_print') == 'true'):
            self.pretty_print = 1

        # set compression level
        if self.config.has_option('server', 'gzip_compresslevel'):
            self.gzip_compresslevel = \
            int(self.config.get('server', 'gzip_compresslevel'))
        else:
            self.gzip_compresslevel = 0

        # generate distributed search model, if specified in config
        if self.config.has_option('server', 'federatedcatalogues'):
            self.log.debug('Configuring distributed search.')
            config.MODEL['constraints']['FederatedCatalogues'] = {'values': []}
            for fedcat in \
            self.config.get('server', 'federatedcatalogues').split(','):
                config.MODEL\
                ['constraints']['FederatedCatalogues']['values'].append(fedcat)

        self.log.debug('Configuration: %s.' % self.config)
        self.log.debug('Model: %s.' % config.MODEL)

        # load user-defined mappings if they exist
        if self.config.has_option('repository', 'mappings'):
            # override default repository mappings
            try:
                import imp
                module = self.config.get('repository','mappings')
                modulename = '%s' % \
                os.path.splitext(module)[0].replace(os.sep, '.')
                self.log.debug(
                'Loading custom repository mappings from %s.' % module)
                mappings = imp.load_source(modulename, module)
                config.MD_CORE_MODEL = mappings.MD_CORE_MODEL
                config.refresh_dc(mappings.MD_CORE_MODEL)
            except Exception, err:
                self.response = self.exceptionreport(
                'NoApplicableCode', 'service',
                'Could not load repository.mappings %s' % str(err))

        # load profiles
        self.log.debug('Loading profiles.')

        if self.config.has_option('server', 'profiles'):
            self.profiles = plugins.profiles.profile.load_profiles(
            os.path.join('server', 'plugins', 'profiles'),
            plugins.profiles.profile.Profile,
            self.config.get('server', 'profiles'))

            for prof in self.profiles['plugins'].keys():
                tmp = self.profiles['plugins'][prof](config.MODEL, config.NAMESPACES)
                key = tmp.outputschema  # to ref by outputschema
                self.profiles['loaded'][key] = tmp
                self.profiles['loaded'][key].extend_core(
                config.MODEL, config.NAMESPACES, self.config)

            self.log.debug('Profiles loaded: %s.' %
            self.profiles['loaded'].keys())

        self.log.debug('NAMESPACES: %s' % config.NAMESPACES)

        # init repository
        if (self.config.has_option('repository', 'source') and
            self.config.get('repository', 'source') == 'geonode'):

            # load geonode repository
            from plugins.repository.geonode import geonode_

            try:
                self.repository = \
                geonode_.GeoNodeRepository(config.MODEL['typenames'])
                self.log.debug('GeoNode repository loaded (geonode): %s.' % \
                self.repository.dbtype)
            except Exception, err:
                self.response = self.exceptionreport(
                'NoApplicableCode', 'service',
                'Could not load repository (geonode): %s' % str(err))

        else:  # load default repository
            try:
                self.repository = \
                repository.Repository(self.config.get('repository', 'database'),
                'records', config.MODEL['typenames'])
                self.log.debug('Repository loaded (local): %s.' % self.repository.dbtype)
            except Exception, err:
                self.response = self.exceptionreport(
                'NoApplicableCode', 'service',
                'Could not load repository (local): %s' % str(err))

    def dispatch(self):
        ''' Handle incoming HTTP request '''

        error = 0
        async = False

        if hasattr(self,'response'):
            self._write_response()
            return

        cgifs = cgi.FieldStorage(keep_blank_values=1)
    
        if cgifs.file:  # it's a POST request
            postdata = cgifs.file.read()
            self.requesttype = 'POST'
            self.request = postdata
            self.log.debug('Request type: POST.  Request:\n%s\n', self.request)
            self.kvp = self.parse_postdata(postdata)
            if isinstance(self.kvp, str):  # it's an exception
                error = 1
                locator = 'service'
                code = 'InvalidRequest'
                text = self.kvp
    
        else:  # it's a GET request
            self.requesttype = 'GET'
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

        self.log.debug('Parsed request parameters: %s' % self.kvp)

        if (isinstance(self.kvp, str) is False and
        self.kvp.has_key('mode') and self.kvp['mode'] == 'sru'):
            import sru
            self.mode = 'sru'
            self.log.debug('SRU mode detected; processing request.')
            self.kvp = sru.request_sru2csw(self.kvp,
            config.MODEL['operations']['GetRecords']['parameters']\
            ['typeNames']['values'])

        if (isinstance(self.kvp, str) is False and
        self.kvp.has_key('mode') and self.kvp['mode'] == 'opensearch'):
            self.mode = 'opensearch'
            self.log.debug('OpenSearch mode detected; processing request.')
            self.kvp['outputschema'] = 'http://www.w3.org/2005/Atom'

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

            if self.kvp.has_key('responsehandler'):
                # set flag to process asynchronously
                import threading
                async = True

            if self.kvp['request'] == 'GetCapabilities':
                self.response = self.getcapabilities()
            elif self.kvp['request'] == 'DescribeRecord':
                self.response = self.describerecord()
            elif self.kvp['request'] == 'GetDomain':
                self.response = self.getdomain()
            elif self.kvp['request'] == 'GetRecords':
                if async:  # process asynchronously
                    threading.Thread(target=self.getrecords).start()
                    self.response = self._write_acknowledgement()
                else:
                    self.response = self.getrecords()
            elif self.kvp['request'] == 'GetRecordById':
                self.response = self.getrecordbyid()
            elif self.kvp['request'] == 'GetRepositoryItem':
                self.response = self.getrepositoryitem()
            elif self.kvp['request'] == 'Transaction':
                self.response = self.transaction()
            elif self.kvp['request'] == 'Harvest':
                if async:  # process asynchronously
                    threading.Thread(target=self.harvest).start()
                    self.response = self._write_acknowledgement()
                else:
                    self.response = self.harvest()
            else:
                self.response = self.exceptionreport('InvalidParameterValue',
                'request', 'Invalid request parameter: %s' %
                self.kvp['request'])

        if self.mode == 'sru':
            self.log.debug('SRU mode detected; processing response.')
            self.response = sru.response_csw2sru(self.response)
        elif self.mode == 'opensearch':
            import opensearch
            self.log.debug('OpenSearch mode detected; processing response.')
            self.response = opensearch.response_csw2opensearch(self.response,
                 self.config)

        self._write_response()

    def exceptionreport(self, code, locator, text):
        ''' Generate ExceptionReport '''
        self.exception = True

        try:
            language = self.config.get('server', 'language')
            ogc_schemas_base = self.config.get('server', 'ogc_schemas_base')
        except:
            language = 'en-US'
            ogc_schemas_base = config.OGC_SCHEMAS_BASE

        node = etree.Element(util.nspath_eval('ows:ExceptionReport'),
        nsmap=config.NAMESPACES, version='1.2.0',
        language=language)

        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/ows/1.0.0/owsExceptionReport.xsd' % \
        (config.NAMESPACES['ows'], ogc_schemas_base)

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

        # check extra parameters that may be def'd by profiles
        if self.profiles is not None:
            for prof in self.profiles['loaded'].keys():
                result = \
                self.profiles['loaded'][prof].check_parameters(self.kvp)
                if result is not None:
                    return self.exceptionreport(result['code'],
                    result['locator'], result['text'])

        # @updateSequence: get latest update to repository
        try:
            updatesequence = \
            util.get_time_iso2unix(self.repository.query_latest_insert())
        except:
            updatesequence = None

        node = etree.Element(util.nspath_eval('csw:Capabilities'),
        nsmap=config.NAMESPACES, version='2.0.2',
        updateSequence=str(updatesequence))

        if self.kvp.has_key('updatesequence'):
            if int(self.kvp['updatesequence']) == updatesequence:
                return node
            elif int(self.kvp['updatesequence']) > updatesequence:
                return self.exceptionreport('InvalidUpdateSequence',
                'updatesequence', 
                'outputsequence specified (%s) is higher than server\'s \
                updatesequence (%s)' % (self.kvp['updatesequence'], 
                updatesequence))

        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (config.NAMESPACES['csw'], self.config.get('server', 'ogc_schemas_base'))

        metadata_main = dict(self.config.items('metadata:main'))

        if serviceidentification:
            self.log.debug('Writing section ServiceIdentification.')

            serviceidentification = etree.SubElement(node, \
            util.nspath_eval('ows:ServiceIdentification'))

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Title')).text = \
            metadata_main.get('identification_title', 'missing')

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Abstract')).text = \
            metadata_main.get('identification_abstract', 'missing')

            keywords = etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Keywords'))

            for k in \
            metadata_main.get('identification_keywords').split(','):
                etree.SubElement(
                keywords, util.nspath_eval('ows:Keyword')).text = k

            etree.SubElement(keywords,
            util.nspath_eval('ows:Type'), codeSpace='ISOTC211/19115').text = \
            metadata_main.get('identification_keywords_type', 'missing')

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:ServiceType'), codeSpace='OGC').text = 'CSW'

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:ServiceTypeVersion')).text = '2.0.2'

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Fees')).text = \
            metadata_main.get('identification_fees', 'missing')

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:AccessConstraints')).text = \
            metadata_main.get('identification_accessconstraints', 'missing')

        if serviceprovider:
            self.log.debug('Writing section ServiceProvider.')
            serviceprovider = etree.SubElement(node,
            util.nspath_eval('ows:ServiceProvider'))

            etree.SubElement(serviceprovider,
            util.nspath_eval('ows:ProviderName')).text = \
            metadata_main.get('provider_name', 'missing')

            providersite = etree.SubElement(serviceprovider,
            util.nspath_eval('ows:ProviderSite'))

            providersite.attrib[util.nspath_eval('xlink:type')] = 'simple'
            providersite.attrib[util.nspath_eval('xlink:href')] = \
            metadata_main.get('provider_url', 'missing')

            servicecontact = etree.SubElement(serviceprovider,
            util.nspath_eval('ows:ServiceContact'))

            etree.SubElement(servicecontact,
            util.nspath_eval('ows:IndividualName')).text = \
            metadata_main.get('contact_name', 'missing')

            etree.SubElement(servicecontact,
            util.nspath_eval('ows:PositionName')).text = \
            metadata_main.get('contact_position', 'missing')

            contactinfo = etree.SubElement(servicecontact,
            util.nspath_eval('ows:ContactInfo'))

            phone = etree.SubElement(contactinfo, util.nspath_eval('ows:Phone'))
            etree.SubElement(phone, util.nspath_eval('ows:Voice')).text = \
            metadata_main.get('contact_phone', 'missing')

            etree.SubElement(phone, util.nspath_eval('ows:Facsimile')).text = \
            metadata_main.get('contact_fax', 'missing')

            address = etree.SubElement(contactinfo,
            util.nspath_eval('ows:Address'))

            etree.SubElement(address,
            util.nspath_eval('ows:DeliveryPoint')).text = \
            metadata_main.get('contact_address', 'missing')

            etree.SubElement(address, util.nspath_eval('ows:City')).text = \
            metadata_main.get('contact_city', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows:AdministrativeArea')).text = \
            metadata_main.get('contact_stateorprovince', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows:PostalCode')).text = \
            metadata_main.get('contact_postalcode', 'missing')

            etree.SubElement(address, util.nspath_eval('ows:Country')).text = \
            metadata_main.get('contact_country', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows:ElectronicMailAddress')).text = \
            metadata_main.get('contact_email', 'missing')

            url = etree.SubElement(contactinfo,
            util.nspath_eval('ows:OnlineResource'))

            url.attrib[util.nspath_eval('xlink:type')] = 'simple'
            url.attrib[util.nspath_eval('xlink:href')] = \
            metadata_main.get('contact_url', 'missing')

            etree.SubElement(contactinfo,
            util.nspath_eval('ows:HoursOfService')).text = \
            metadata_main.get('contact_hours', 'missing')

            etree.SubElement(contactinfo,
            util.nspath_eval('ows:ContactInstructions')).text = \
            metadata_main.get('contact_instructions', 'missing')

            etree.SubElement(servicecontact,
            util.nspath_eval('ows:Role'), codeSpace='ISOTC211/19115').text = \
            metadata_main.get('contact_role', 'missing')

        if operationsmetadata:
            self.log.debug('Writing section OperationsMetadata.')
            operationsmetadata = etree.SubElement(node,
            util.nspath_eval('ows:OperationsMetadata'))

            for operation in config.MODEL['operations'].keys():
                oper = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows:Operation'), name = operation)

                dcp = etree.SubElement(oper, util.nspath_eval('ows:DCP'))
                http = etree.SubElement(dcp, util.nspath_eval('ows:HTTP'))

                if config.MODEL['operations'][operation]['methods']['get']:
                    get = etree.SubElement(http, util.nspath_eval('ows:Get'))
                    get.attrib[util.nspath_eval('xlink:type')] = 'simple'
                    get.attrib[util.nspath_eval('xlink:href')] = \
                    self.config.get('server', 'url')

                if config.MODEL['operations'][operation]['methods']['post']:
                    post = etree.SubElement(http, util.nspath_eval('ows:Post'))
                    post.attrib[util.nspath_eval('xlink:type')] = 'simple'
                    post.attrib[util.nspath_eval('xlink:href')] = \
                    self.config.get('server', 'url')

                for parameter in \
                config.MODEL['operations'][operation]['parameters']:
                    param = etree.SubElement(oper,
                    util.nspath_eval('ows:Parameter'), name = parameter)

                    for val in \
                    config.MODEL['operations'][operation]\
                    ['parameters'][parameter]['values']:
                        etree.SubElement(param,
                        util.nspath_eval('ows:Value')).text = val

                if operation == 'GetRecords':  # advertise queryables
                    for qbl in self.repository.queryables.keys():
                        if qbl != '_all':
                            param = etree.SubElement(oper,
                            util.nspath_eval('ows:Constraint'), name = qbl)
    
                            for qbl2 in self.repository.queryables[qbl]:
                                etree.SubElement(param,
                                util.nspath_eval('ows:Value')).text = qbl2

                    if self.profiles is not None:
                        for con in config.MODEL[\
                        'operations']['GetRecords']['constraints'].keys():
                            param = etree.SubElement(oper,
                            util.nspath_eval('ows:Constraint'), name = con)
                            for val in config.MODEL['operations']\
                            ['GetRecords']['constraints'][con]['values']:
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
            
            if self.profiles is not None:
                for prof in self.profiles['loaded'].keys():
                    ecnode = \
                    self.profiles['loaded'][prof].get_extendedcapabilities()
                    if ecnode is not None:
                        operationsmetadata.append(ecnode)

        # always write out Filter_Capabilities
        self.log.debug('Writing section Filter_Capabilities.')
        fltcaps = etree.SubElement(node,
        util.nspath_eval('ogc:Filter_Capabilities'))

        spatialcaps = etree.SubElement(fltcaps,
        util.nspath_eval('ogc:Spatial_Capabilities'))

        geomops = etree.SubElement(spatialcaps,
        util.nspath_eval('ogc:GeometryOperands'))

        for geomtype in \
        fes.MODEL['GeometryOperands']['values']:
            etree.SubElement(geomops,
            util.nspath_eval('ogc:GeometryOperand')).text = geomtype
    
        spatialops = etree.SubElement(spatialcaps,
        util.nspath_eval('ogc:SpatialOperators'))

        for spatial_comparison in \
        fes.MODEL['SpatialOperators']['values']:
            etree.SubElement(spatialops,
            util.nspath_eval('ogc:SpatialOperator'), name = spatial_comparison)
    
        scalarcaps = etree.SubElement(fltcaps,
        util.nspath_eval('ogc:Scalar_Capabilities'))

        etree.SubElement(scalarcaps, util.nspath_eval('ogc:LogicalOperators'))
        
        cmpops = etree.SubElement(scalarcaps,
        util.nspath_eval('ogc:ComparisonOperators'))
    
        for cmpop in fes.MODEL['ComparisonOperators'].keys():
            etree.SubElement(cmpops,
            util.nspath_eval('ogc:ComparisonOperator')).text = \
            fes.MODEL['ComparisonOperators'][cmpop]['opname']

        arithops = etree.SubElement(scalarcaps,
        util.nspath_eval('ogc:ArithmeticOperators'))

        functions = etree.SubElement(arithops,
        util.nspath_eval('ogc:Functions'))

        functionames = etree.SubElement(functions,
        util.nspath_eval('ogc:FunctionNames'))

        for fnop in sorted(fes.MODEL['Functions'].keys()):
            etree.SubElement(functionames,
            util.nspath_eval('ogc:FunctionName'),
            nArgs=fes.MODEL['Functions'][fnop]['args']).text = fnop

        idcaps = etree.SubElement(fltcaps,
        util.nspath_eval('ogc:Id_Capabilities'))

        for idcap in fes.MODEL['Ids']['values']:
            etree.SubElement(idcaps, util.nspath_eval('ogc:%s' % idcap))

        return node
    
    def describerecord(self):
        ''' Handle DescribeRecord request '''
    
        if self.kvp.has_key('typename') is False or \
        len(self.kvp['typename']) == 0:  # missing typename
        # set to return all typenames
            self.kvp['typename'] = ['csw:Record']

            if self.profiles is not None:
                for prof in self.profiles['loaded'].keys():
                    self.kvp['typename'].append(
                    self.profiles['loaded'][prof].typename)

        elif self.requesttype == 'GET':  # pass via GET
            self.kvp['typename'] = self.kvp['typename'].split(',')

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
        (config.NAMESPACES['csw'],
        self.config.get('server', 'ogc_schemas_base'))

        for typename in self.kvp['typename']:
            if typename == 'csw:Record':   # load core schema    
                self.log.debug('Writing csw:Record schema.')
                schemacomponent = etree.SubElement(node,
                util.nspath_eval('csw:SchemaComponent'),
                schemaLanguage='XMLSCHEMA',
                targetNamespace = config.NAMESPACES['csw'])
                dublincore = etree.parse(os.path.join(
                self.config.get('server', 'home'),
                'etc', 'schemas', 'ogc', 'csw',
                '2.0.2', 'record.xsd')).getroot()

                schemacomponent.append(dublincore)

            if self.profiles is not None:
                for prof in self.profiles['loaded'].keys():
                    if self.profiles['loaded'][prof].typename == typename:
                        scnodes = \
                        self.profiles['loaded'][prof].get_schemacomponents()
                        if scnodes is not None:
                            map(node.append, scnodes)
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
        (config.NAMESPACES['csw'],
        self.config.get('server', 'ogc_schemas_base'))

        if self.kvp.has_key('parametername'):
            for pname in self.kvp['parametername'].split(','):
                self.log.debug('Parsing parametername %s.' % pname)
                domainvalue = etree.SubElement(node,
                util.nspath_eval('csw:DomainValues'), type = 'csw:Record')
                etree.SubElement(domainvalue,
                util.nspath_eval('csw:ParameterName')).text = pname
                try:
                    operation, parameter = pname.split('.')
                except:
                    return node
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

                if pname.find('/') == 0:  # it's an XPath
                    pname2 = pname
                else:  # it's a core queryable, map to internal typename model
                    try:
                        pname2 = self.repository.queryables['_all'][pname]['dbcol']
                    except:
                        pname2 = pname

                # decipher typename
                dvtype = None
                if self.profiles is not None:
                    for prof in self.profiles['loaded'].keys():
                        for prefix in self.profiles['loaded'][prof].prefixes:
                            if pname2.find(prefix) != -1:
                                dvtype = self.profiles['loaded'][prof].typename
                                break
                if not dvtype:
                    dvtype = 'csw:Record'

                domainvalue = etree.SubElement(node,
                util.nspath_eval('csw:DomainValues'), type = dvtype)
                etree.SubElement(domainvalue,
                util.nspath_eval('csw:PropertyName')).text = pname

                try:
                    self.log.debug(
                    'Querying repository property %s, typename %s, \
                    domainquerytype %s.' % \
                    (pname2, dvtype, self.domainquerytype))

                    results = self.repository.query_domain(
                    pname2, dvtype, self.domainquerytype)

                    self.log.debug('Results: %s' % str(len(results)))

                    if self.domainquerytype == 'range':
                        rangeofvalues = etree.SubElement(domainvalue,
                        util.nspath_eval('csw:RangeOfValues'))

                        etree.SubElement(rangeofvalues,
                        util.nspath_eval('csw:MinValue')).text = results[0][0]

                        etree.SubElement(rangeofvalues,
                        util.nspath_eval('csw:MaxValue')).text = results[0][1]
                    else:
                        listofvalues = etree.SubElement(domainvalue,
                        util.nspath_eval('csw:ListOfValues'))
                        for result in results:
                            self.log.debug(str(result))
                            if (result is not None and
                                result[0] is not None):  # drop null values
                                etree.SubElement(listofvalues,
                                util.nspath_eval('csw:Value')).text = result[0]
                except Exception, err:
                    self.log.debug('No results for propertyname %s: %s.' %
                    (pname2, str(err)))
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

        if (self.kvp.has_key('elementname') and
            self.requesttype == 'GET'):  # passed via GET
            self.kvp['elementname'] = self.kvp['elementname'].split(',')
            self.kvp['elementsetname'] = 'summary'

        if self.kvp.has_key('typenames') is False:
            return self.exceptionreport('MissingParameterValue',
            'typenames', 'Missing typenames parameter')

        if (self.kvp.has_key('typenames') and
            self.requesttype == 'GET'):  # passed via GET
            self.kvp['typenames'] = self.kvp['typenames'].split(',')

        if self.kvp.has_key('typenames'):
            for tname in self.kvp['typenames']:
                if (tname not in config.MODEL['operations']['GetRecords']
                    ['parameters']['typeNames']['values']):
                    return self.exceptionreport('InvalidParameterValue',
                    'typenames', 'Invalid typeNames parameter value: %s' %
                    tname)

        # check elementname's
        if self.kvp.has_key('elementname'):
            for ename in self.kvp['elementname']:
                enamelist = self.repository.queryables['_all'].keys()
                if ename not in enamelist:
                    return self.exceptionreport('InvalidParameterValue',
                    'elementname', 'Invalid ElementName parameter value: %s' %
                    ename)

        if self.kvp['resulttype'] == 'validate':
            return self._write_acknowledgement()

        if self.kvp.has_key('maxrecords') is False:
            self.kvp['maxrecords'] = self.config.get('server', 'maxrecords')

        if self.requesttype == 'GET':
            if self.kvp.has_key('constraint'):
                # GET request
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
                    tmp = self.kvp['constraint']
                    self.kvp['constraint'] = {}
                    self.kvp['constraint']['type'] = 'cql'
                    self.kvp['constraint']['where'] = \
                    self._cql_update_queryables_mappings(tmp,
                    self.repository.queryables['_all'])
                elif self.kvp['constraintlanguage'] == 'FILTER':
                    # validate filter XML
                    try:
                        schema = os.path.join(self.config.get('server', 'home'),
                        'etc', 'schemas', 'ogc', 'filter', '1.1.0', 'filter.xsd')
                        self.log.debug('Validating Filter %s.' %
                        self.kvp['constraint'])
                        schema = etree.XMLSchema(etree.parse(schema))
                        parser = etree.XMLParser(schema=schema)
                        doc = etree.fromstring(self.kvp['constraint'], parser)
                        self.log.debug('Filter is valid XML.')
                        self.kvp['constraint'] = {}
                        self.kvp['constraint']['type'] = 'filter'
                        self.kvp['constraint']['where'] = \
                        fes.parse(doc,
                        self.repository.queryables['_all'].keys(),
                        self.repository.dbtype)
                    except Exception, err:
                        errortext = \
                        'Exception: document not valid.\nError: %s.' % str(err)
    
                        self.log.debug(errortext)
                        return self.exceptionreport('InvalidParameterValue',
                        'constraint', 'Invalid Filter query: %s' % errortext)
            else:
                self.kvp['constraint'] = {}

        if self.kvp.has_key('sortby') is False:
            self.kvp['sortby'] = None

        if self.kvp.has_key('startposition') is False:
            self.kvp['startposition'] = 1

        # query repository
        self.log.debug('Querying repository with constraint: %s,\
        sortby: %s, typenames: %s, maxrecords: %s, startposition: %s.' %
        (self.kvp['constraint'], self.kvp['sortby'], self.kvp['typenames'],
        self.kvp['maxrecords'], self.kvp['startposition']))

        try:
            matched, results = self.repository.query(
            constraint=self.kvp['constraint'],
            sortby=self.kvp['sortby'], typenames=self.kvp['typenames'],
            maxrecords=self.kvp['maxrecords'],
            startposition=int(self.kvp['startposition'])-1)
        except Exception, err:
            return self.exceptionreport('InvalidParameterValue', 'constraint',
            'Invalid query: %s' % err)

        dsresults = []

        if (self.config.has_option('server', 'federatedcatalogues') and
            self.kvp.has_key('distributedsearch') and
            self.kvp['distributedsearch'] and self.kvp['hopcount'] > 0):
            # do distributed search

            self.log.debug('DistributedSearch specified (hopCount: %s).' %
            self.kvp['hopcount'])

            from owslib.csw import CatalogueServiceWeb
            for fedcat in \
            self.config.get('server', 'federatedcatalogues').split(','):
                self.log.debug('Performing distributed search on federated \
                catalogue: %s.' % fedcat)
                remotecsw = CatalogueServiceWeb(fedcat, skip_caps=True)
                try:
                    remotecsw.getrecords(xml=self.request)
                    if hasattr(remotecsw, 'results'):
                        self.log.debug(
                        'Distributed search results from catalogue \
                        %s: %s.' % (fedcat, remotecsw.results))

                        if int(remotecsw.results['matches']) > 0:
                            matched = str(int(matched) + \
                            int(remotecsw.results['matches']))
                            dsresults.append(etree.Comment(
                            '%s results from %s' %
                            (remotecsw.results['matches'], fedcat)))

                            dsresults.append(remotecsw.records)

                except Exception, err:
                    self.log.debug(str(err))

        if int(matched) == 0:
            returned = nextrecord = '0'
        else:
            if int(matched) < int(self.kvp['maxrecords']):
                returned = matched
                nextrecord = '0'
            else:
                returned = str(self.kvp['maxrecords'])
                nextrecord = str(int(self.kvp['startposition']) + \
                int(self.kvp['maxrecords']))

        self.log.debug('Results: matched: %s, returned: %s, next: %s.' % \
        (matched, returned, nextrecord))

        node = etree.Element(util.nspath_eval('csw:GetRecordsResponse'),
        nsmap = config.NAMESPACES, version='2.0.2')

        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (config.NAMESPACES['csw'], self.config.get('server', 'ogc_schemas_base'))

        etree.SubElement(node, util.nspath_eval('csw:SearchStatus'),
        timestamp=timestamp)

        if self.kvp['constraint'].has_key('where') is False and \
        self.kvp['resulttype'] is None:
            returned = '0'

        searchresults = etree.SubElement(node,
        util.nspath_eval('csw:SearchResults'),
        numberOfRecordsMatched=matched, numberOfRecordsReturned=returned,
        nextRecord=nextrecord, recordSchema=self.kvp['outputschema'])

        if self.kvp['elementsetname'] is not None:
            searchresults.attrib['elementSet'] = self.kvp['elementsetname']

        if self.kvp['constraint'].has_key('where') is False \
        and self.kvp['resulttype'] is None:
            self.log.debug('Empty result set returned.')
            return node

        if self.kvp['resulttype'] == 'hits':
            return node

 
        if results is not None:
            if len(results) < self.kvp['maxrecords']:
                max1 = len(results)
            else:
                max1 = int(self.kvp['startposition']) + (int(self.kvp['maxrecords'])-1)
            self.log.debug('Presenting records %s - %s.' %
            (self.kvp['startposition'], max1))

            for res in results:
                try:
                    if (self.kvp['outputschema'] == 
                        'http://www.opengis.net/cat/csw/2.0.2' and
                        'csw:Record' in self.kvp['typenames']):
                        # serialize csw:Record inline
                        searchresults.append(self._write_record(
                        res, self.repository.queryables['_all']))
                    elif (self.kvp['outputschema'] ==
                        'http://www.opengis.net/cat/csw/2.0.2' and
                        'csw:Record' not in self.kvp['typenames']):
                        # serialize into csw:Record model
    
                        for prof in self.profiles['loaded']:
                            # find source typename
                            if self.profiles['loaded'][prof].typename in \
                            self.kvp['typenames']:
                                typename = self.profiles['loaded'][prof].typename
                                break
    
                        util.transform_mappings(self.repository.queryables['_all'],
                        config.MODEL['typenames'][typename]\
                        ['mappings']['csw:Record'], reverse=True)
    
                        searchresults.append(self._write_record(
                        res, self.repository.queryables['_all']))
                    else:  # use profile serializer
                        searchresults.append(
                        self.profiles['loaded'][self.kvp['outputschema']].\
                        write_record(res, self.kvp['elementsetname'],
                        self.kvp['outputschema'],
                        self.repository.queryables['_all']))
                except Exception, err:
                    self.response = self.exceptionreport(
                    'NoApplicableCode', 'service',
                    'Record serialization failed: %s' % str(err))
                    return self.response

        if len(dsresults) > 0:  # return DistributedSearch results
            for resultset in dsresults:
                if isinstance(resultset, etree._Comment):
                    searchresults.append(resultset)
                for rec in resultset:
                    searchresults.append(etree.fromstring(resultset[rec].xml))

        if self.kvp.has_key('responsehandler'):  # process the handler
            self._process_responsehandler(etree.tostring(node,
            pretty_print=self.pretty_print))
        else:
            return node

    def getrecordbyid(self, raw=False):
        ''' Handle GetRecordById request '''

        if self.kvp.has_key('id') is False:
            return self.exceptionreport('MissingParameterValue', 'id',
            'Missing id parameter')
        if len(self.kvp['id']) < 1:
            return self.exceptionreport('InvalidParameterValue', 'id',
            'Invalid id parameter')
        if self.kvp.has_key('outputschema') is False:
            self.kvp['outputschema'] = config.NAMESPACES['csw']

        if self.requesttype == 'GET':
            self.kvp['id'] = self.kvp['id'].split(',')

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

        node = etree.Element(util.nspath_eval('csw:GetRecordByIdResponse'),
        nsmap = config.NAMESPACES)
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (config.NAMESPACES['csw'], self.config.get('server', 'ogc_schemas_base'))

        # query repository
        self.log.debug('Querying repository with ids: %s.' % self.kvp['id'][0])
        results = self.repository.query_ids(self.kvp['id'])

        if raw:  # GetRepositoryItem request
            self.log.debug('GetRepositoryItem request.')
            if len(results) > 0:
                return etree.fromstring(util.getqattr(results[0],
                config.MD_CORE_MODEL['mappings']['pycsw:XML']))

        for result in results:
            if (util.getqattr(result,
            config.MD_CORE_MODEL['mappings']['pycsw:Typename']) == 'csw:Record'
            and self.kvp['outputschema'] ==
            'http://www.opengis.net/cat/csw/2.0.2'):
                # serialize record inline
                node.append(self._write_record(
                result, self.repository.queryables['_all']))
            elif (self.kvp['outputschema'] ==
                'http://www.opengis.net/cat/csw/2.0.2'):
                # serialize into csw:Record model

                for prof in self.profiles['loaded']:  # find source typename
                    if self.profiles['loaded'][prof].typename in \
                    [util.getqattr(result, config.MD_CORE_MODEL['mappings']['pycsw:Typename'])]:
                        typename = self.profiles['loaded'][prof].typename
                        break

                util.transform_mappings(self.repository.queryables['_all'],
                config.MODEL['typenames'][typename]\
                ['mappings']['csw:Record'], reverse=True)

                node.append(self._write_record(
                result, self.repository.queryables['_all']))
            else:  # it's a profile output
                node.append(
                self.profiles['loaded'][self.kvp['outputschema']].write_record(
                result, self.kvp['elementsetname'],
                self.kvp['outputschema'], self.repository.queryables['_all']))

        if raw and len(results) == 0:
            return None

        return node

    def getrepositoryitem(self):
        ''' Handle GetRepositoryItem request '''

        # similar to GetRecordById without csw:* wrapping
        node = self.getrecordbyid(raw=True)
        if node is None:
            return self.exceptionreport('NotFound', 'id',
            'No repository item found for \'%s\'' % self.kvp['id'])
        else:
            return node

    def transaction(self):
        ''' Handle Transaction request '''

        try:
            self._test_manager()
        except Exception, err:
            return self.exceptionreport('NoApplicableCode', 'transaction',
            str(err))

        inserted = 0
        updated = 0
        deleted = 0

        insertresults = []

        self.log.debug('Transaction list: %s' % self.kvp['transactions'])

        for ttype in self.kvp['transactions']:
            if ttype['type'] == 'insert':
                try:
                    record = metadata.parse_record(ttype['xml'],
                    self.repository)[0]
                except Exception, err:
                    return self.exceptionreport('NoApplicableCode', 'insert',
                    'Transaction (insert) failed: record parsing failed: %s' \
                    % str(err))

                self.log.debug('Transaction operation: %s' % record)

                if hasattr(record,
                config.MD_CORE_MODEL['mappings']['pycsw:Identifier']) is False:
                    return self.exceptionreport('NoApplicableCode',
                    'insert', 'Record requires an identifier')

                # insert new record
                try:
                    self.repository.insert(record, 'local',
                    util.get_today_and_now())

                    inserted += 1
                    insertresults.append(
                    {'identifier': getattr(record, 
                    config.MD_CORE_MODEL['mappings']['pycsw:Identifier']),
                    'title': getattr(record,
                    config.MD_CORE_MODEL['mappings']['pycsw:Title'])})
                except Exception, err:
                    return self.exceptionreport('NoApplicableCode',
                    'insert', 'Transaction (insert) failed: %s.' % str(err))

            elif ttype['type'] == 'update':
                if ttype.has_key('constraint') is False:
                    # update full existing resource in repository
                    try:
                        record = metadata.parse_record(ttype['xml'],
                        self.repository)[0]
                        identifier = getattr(record,
                        config.MD_CORE_MODEL['mappings']['pycsw:Identifier'])
                    except Exception, err:
                        return self.exceptionreport('NoApplicableCode', 'insert',
                        'Transaction (update) failed: record parsing failed: %s' \
                        % str(err))
            
                    # query repository to see if record already exists
                    self.log.debug('checking if record exists (%s)' % \
                    identifier)

                    results = self.repository.query_ids(ids=[identifier])
            
                    if len(results) == 0:
                        self.log.debug('id %s does not exist in repository' % \
                        identifier)
                    else:  # existing record, it's an update
                        try:
                            self.repository.update(record)
                            updated += 1
                        except Exception, err:
                            return self.exceptionreport('NoApplicableCode',
                            'update',
                            'Transaction (update) failed: %s.' % str(err))
                else:  # update by record property and constraint
                    # get / set XPath for property names
                    for rp in ttype['recordproperty']:
                        rp['rp']= \
                        self.repository.queryables['_all'][rp['name']]

                    self.log.debug('Record Properties: %s.' %
                    ttype['recordproperty']) 
                    try:
                        updated += self.repository.update(record=None,
                        recprops=ttype['recordproperty'],
                        constraint=ttype['constraint'])
                    except Exception, err:
                        return self.exceptionreport('NoApplicableCode',
                        'update',
                        'Transaction (update) failed: %s.' % str(err))

            elif ttype['type'] == 'delete':
                deleted += self.repository.delete(ttype['constraint'])

        node = etree.Element(util.nspath_eval('csw:TransactionResponse'),
        nsmap = config.NAMESPACES, version = '2.0.2')

        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/CSW-publication.xsd' % \
        (config.NAMESPACES['csw'], self.config.get('server', 'ogc_schemas_base'))

        node.append(
        self._write_transactionsummary(
        inserted=inserted, updated=updated, deleted=deleted))

        if (len(insertresults) > 0 and self.kvp['verboseresponse']):
            # show insert result identifiers
            insertresult = etree.Element(util.nspath_eval('csw:InsertResult'))
            for ir in insertresults:
                briefrec = etree.SubElement(insertresult,
                           util.nspath_eval('csw:BriefRecord'))
                etree.SubElement(briefrec,
                util.nspath_eval('dc:identifier')).text = ir['identifier']

                etree.SubElement(briefrec,
                util.nspath_eval('dc:title')).text = ir['title']

            node.append(insertresult)

        return node

    def harvest(self):
        ''' Handle Harvest request '''

        try:
            self._test_manager()
        except Exception, err:
            return self.exceptionreport('NoApplicableCode', 'harvest', str(err))

        # validate resourcetype
        if (self.kvp['resourcetype'] not in
            config.MODEL['operations']['Harvest']['parameters']['ResourceType']
            ['values']):
            return self.exceptionreport('InvalidParameterValue',
            'resourcetype', 'Invalid resource type parameter: %s.\
            Allowable resourcetype values: %s' % (self.kvp['resourcetype'],
            ','.join(config.MODEL['operations']['Harvest']['parameters']
            ['ResourceType']['values'])))

        if self.kvp['resourcetype'].find('opengis.net') == -1:
            # fetch content-based resource
            self.log.debug('Fetching resource %s' % self.kvp['source'])
            try:
                req = urllib2.Request(self.kvp['source'])
                req.add_header('User-Agent', 'pycsw (http://pycsw.org/)')
                content = urllib2.urlopen(req).read() 
            except Exception, err:
                errortext = 'Error fetching resource %s.\nError: %s.' % \
                (self.kvp['source'], str(err))
                self.log.debug(errortext)
                return self.exceptionreport('InvalidParameterValue', 'source',
                errortext)
        else:  # it's a service URL
            content = self.kvp['source']
            # query repository to see if service already exists
            self.log.debug('checking if service exists (%s)' % content)
            results = self.repository.query_source(content)

            if len(results) > 0:  # exists, don't insert
                return self.exceptionreport('NoApplicableCode',
                'source', 'Insert failed: service %s in repository' % content)

        # parse resource into record
        try:
            records_parsed = metadata.parse_record(content, self.repository,
            self.kvp['resourcetype'])
        except Exception, err:
            return self.exceptionreport('NoApplicableCode', 'source',
            'Harvest failed: record parsing failed: %s' % str(err))

        inserted = 0
        updated = 0

        for record in records_parsed:
            setattr(record, config.MD_CORE_MODEL['mappings']['pycsw:Source'],
            self.kvp['source'])

            setattr(record, config.MD_CORE_MODEL['mappings']['pycsw:InsertDate'],
            util.get_today_and_now())

            identifier = getattr(record,
            config.MD_CORE_MODEL['mappings']['pycsw:Identifier'])
            source = getattr(record,
            config.MD_CORE_MODEL['mappings']['pycsw:Source'])
            insert_date = getattr(record,
            config.MD_CORE_MODEL['mappings']['pycsw:InsertDate'])

            # query repository to see if record already exists
            self.log.debug('checking if record exists (%s)' % identifier)
            results = self.repository.query_ids(ids=[identifier])

            if len(results) == 0:  # new record, it's a new insert
                inserted += 1
                try:
                    self.repository.insert(record, source, insert_date)
                except Exception, err:
                    return self.exceptionreport('NoApplicableCode',
                    'source', 'Harvest (insert) failed: %s.' % str(err))
            else:  # existing record, it's an update
                if record.source != results[0].source:
                    # same identifier, but different source
                    return self.exceptionreport('NoApplicableCode',
                    'source', 'Insert failed: identifier %s in repository\
                    has source %s.' % str(err))

                try:
                    self.repository.update(record)
                except Exception, err:
                    return self.exceptionreport('NoApplicableCode',
                    'source', 'Harvest (update) failed: %s.' % str(err))
                updated += 1

        node = etree.Element(util.nspath_eval('csw:HarvestResponse'),
        nsmap = config.NAMESPACES)
        node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
        '%s %s/csw/2.0.2/CSW-publication.xsd' % (config.NAMESPACES['csw'],
        self.config.get('server', 'ogc_schemas_base'))

        node2 = etree.SubElement(node,
        util.nspath_eval('csw:TransactionResponse'), version='2.0.2')

        node2.append(
        self._write_transactionsummary(inserted=inserted, updated=updated))

        if self.kvp.has_key('responsehandler'):  # process the handler
            self._process_responsehandler(etree.tostring(node,
            pretty_print=self.pretty_print))
        else:
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
            schema = os.path.join(self.config.get('server', 'home'), 'etc',
            'schemas', 'ogc', 'csw', '2.0.2', 'CSW-publication.xsd')
        else:
            schema = os.path.join(self.config.get('server', 'home'), 'etc',
            'schemas', 'ogc', 'csw', '2.0.2', 'CSW-discovery.xsd')

        try:
            # it is virtually impossible to validate a csw:Transaction
            # csw:Insert|csw:Update (with single child) XML document.
            # Only validate non csw:Transaction XML

            if doc.find('.//%s' % util.nspath_eval('csw:Insert')) is None and \
            len(doc.xpath('//csw:Update/child::*',
            namespaces=config.NAMESPACES)) == 0:

                self.log.debug('Validating %s.' % postdata)
                schema = etree.XMLSchema(etree.parse(schema))
                parser = etree.XMLParser(schema=schema)
                if hasattr(self, 'soap') and self.soap:
                # validate the body of the SOAP request
                    doc = etree.fromstring(etree.tostring(doc), parser)
                else:  # validate the request normally
                    doc = etree.fromstring(postdata, parser)
                self.log.debug('Request is valid XML.')
            else:  # parse Transaction without validation
                doc = etree.fromstring(postdata)
        except Exception, err:
            errortext = \
            'Exception: the document is not valid.\nError: %s' % str(err)
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
    
        tmp = doc.find('.').attrib.get('updateSequence')
        if tmp is not None:
            request['updatesequence'] = tmp

        # DescribeRecord
        if request['request'] == 'DescribeRecord':
            request['typename'] = [typename.text for typename in \
            doc.findall(util.nspath_eval('csw:TypeName'))]
    
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
            request['outputschema'] = tmp if tmp is not None \
            else config.NAMESPACES['csw']

            tmp = doc.find('.').attrib.get('resultType')
            request['resulttype'] = tmp if tmp is not None else None

            tmp = doc.find('.').attrib.get('outputFormat')
            request['outputformat'] = tmp if tmp is not None \
            else 'application/xml'

            tmp = doc.find('.').attrib.get('startPosition')
            request['startposition'] = tmp if tmp is not None else 1

            tmp = doc.find('.').attrib.get('maxRecords')
            request['maxrecords'] = tmp if tmp is not None else \
            self.config.get('server', 'maxrecords')

            client_mr = int(request['maxrecords'])
            server_mr = int(self.config.get('server', 'maxrecords'))

            if client_mr < server_mr:
                request['maxrecords'] = client_mr

            tmp = doc.find(util.nspath_eval('csw:DistributedSearch'))
            if tmp is not None:
                request['distributedsearch'] = True
                hopcount = tmp.attrib.get('hopCount')
                request['hopcount'] = int(hopcount)-1 if hopcount is not None \
                else 1
            else:
                request['distributedsearch'] = False

            tmp = doc.find(util.nspath_eval('csw:ResponseHandler'))
            if tmp is not None:
                request['responsehandler'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw:Query/csw:ElementSetName'))
            request['elementsetname'] = tmp.text if tmp is not None else None

            tmp = doc.find(util.nspath_eval(
            'csw:Query')).attrib.get('typeNames')
            request['typenames'] = tmp.split() if tmp is not None \
            else 'csw:Record'

            request['elementname'] = [elname.text for elname in \
            doc.findall(util.nspath_eval('csw:Query/csw:ElementName'))]

            request['constraint'] = {}
            tmp = doc.find(util.nspath_eval('csw:Query/csw:Constraint'))

            if tmp is not None:
                request['constraint'] = self._parse_constraint(tmp)
                if isinstance(request['constraint'], str):  # parse error
                    return 'Invalid Constraint: %s' % request['constraint']
            else: 
                self.log.debug('No csw:Constraint (ogc:Filter or csw:CqlText) \
                specified.')

            tmp = doc.find(util.nspath_eval('csw:Query/ogc:SortBy'))
            if tmp is not None:
                self.log.debug('Sorted query specified.')
                request['sortby'] = {}

                try:
                    request['sortby']['propertyname'] = \
                    self.repository.queryables['_all']\
                    [tmp.find(util.nspath_eval(
                    'ogc:SortProperty/ogc:PropertyName')).text]['dbcol']
                except Exception, err:
                    errortext = \
                    'Invalid ogc:SortProperty/ogc:PropertyName: %s' % str(err)
                    self.log.debug(errortext)
                    return errortext       

                tmp2 =  tmp.find(util.nspath_eval(
                'ogc:SortProperty/ogc:SortOrder'))
                request['sortby']['order'] = tmp2.text if tmp2 is not None \
                else 'asc'
            else:
                request['sortby'] = None

        # GetRecordById
        if request['request'] == 'GetRecordById':
            request['id'] = [id1.text for id1 in \
            doc.findall(util.nspath_eval('csw:Id'))]

            tmp = doc.find(util.nspath_eval('csw:ElementSetName'))
            request['elementsetname'] = tmp.text if tmp is not None \
            else 'summary'

            tmp = doc.find('.').attrib.get('outputSchema')
            request['outputschema'] = tmp if tmp is not None \
            else config.NAMESPACES['csw']

            tmp = doc.find('.').attrib.get('outputFormat')
            if tmp is not None:
                request['outputformat'] = tmp

        # Transaction
        if request['request'] == 'Transaction':
            request['verboseresponse'] = True
            tmp = doc.find('.').attrib.get('verboseResponse')
            if tmp is not None:
                if tmp in ['false', '0']:
                    request['verboseresponse'] = False

            request['transactions'] = []

            for ttype in \
            doc.xpath('//csw:Insert', namespaces=config.NAMESPACES):
                tname = ttype.attrib.get('typeName')

                for mdrec in ttype.xpath('child::*'):
                    xml = mdrec
                    request['transactions'].append(
                    {'type': 'insert', 'typename': tname, 'xml': xml})

            for ttype in \
            doc.xpath('//csw:Update', namespaces=config.NAMESPACES):
                child = ttype.xpath('child::*')
                update = {'type': 'update'}

                if len(child) == 1:  # it's a wholesale update
                    update['xml'] = child[0]
                else:  # it's a RecordProperty with Constraint Update
                    update['recordproperty'] = []

                    for recprop in ttype.findall(
                    util.nspath_eval('csw:RecordProperty')):
                        rpname = recprop.find(util.nspath_eval('csw:Name')).text
                        rpvalue = recprop.find(
                        util.nspath_eval('csw:Value')).text

                        update['recordproperty'].append(
                        {'name': rpname, 'value': rpvalue})

                    update['constraint'] = self._parse_constraint(
                    ttype.find(util.nspath_eval('csw:Constraint')))

                request['transactions'].append(update)

            for ttype in \
            doc.xpath('//csw:Delete', namespaces=config.NAMESPACES):
                tname = ttype.attrib.get('typeName')
                constraint = self._parse_constraint(
                ttype.find(util.nspath_eval('csw:Constraint')))

                if isinstance(constraint, str):  # parse error
                    return 'Invalid Constraint: %s' % constraint

                request['transactions'].append(
                {'type': 'delete', 'typename': tname, 'constraint': constraint})

        # Harvest
        if request['request'] == 'Harvest':
            request['source'] = doc.find(util.nspath_eval('csw:Source')).text

            request['resourcetype'] = \
            doc.find(util.nspath_eval('csw:ResourceType')).text

            tmp = doc.find(util.nspath_eval('csw:ResourceFormat'))
            if tmp is not None:
                request['resourceformat'] = tmp.text
            else:
                request['resourceformat'] = 'application/xml'

            tmp = doc.find(util.nspath_eval('csw:HarvestInterval'))
            if tmp is not None:
                request['harvestinterval'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw:ResponseHandler'))
            if tmp is not None:
                request['responsehandler'] = tmp.text
        return request

    def _write_record(self, recobj, queryables):
        ''' Generate csw:Record '''
        if self.kvp['elementsetname'] == 'brief':
            elname = 'BriefRecord'
        elif self.kvp['elementsetname'] == 'summary':
            elname = 'SummaryRecord'
        else:
            elname = 'Record'

        record = etree.Element(util.nspath_eval('csw:%s' % elname))

        if (self.kvp.has_key('elementname') and
            len(self.kvp['elementname']) > 0):
            for elemname in self.kvp['elementname']:
                if (elemname.find('BoundingBox') != -1 or
                    elemname.find('Envelope') != -1):
                    bboxel = write_boundingbox(util.getqattr(recobj, 
                    config.MD_CORE_MODEL['mappings']['pycsw:BoundingBox']))
                    if bboxel is not None:
                        record.append(bboxel)
                else:
                    value = util.getqattr(recobj, queryables[elemname]['dbcol'])
                    if value:
                        etree.SubElement(record,
                        util.nspath_eval(elemname)).text = value
        elif self.kvp.has_key('elementsetname'):
            if (self.kvp['elementsetname'] == 'full' and
            util.getqattr(recobj, config.MD_CORE_MODEL['mappings']\
            ['pycsw:Typename']) == 'csw:Record'):
                # dump record as is and exit
                return etree.fromstring(util.getqattr(recobj,
                config.MD_CORE_MODEL['mappings']['pycsw:XML']))

            etree.SubElement(record,
            util.nspath_eval('dc:identifier')).text = \
            util.getqattr(recobj,
            config.MD_CORE_MODEL['mappings']['pycsw:Identifier'])

            for i in ['dc:title', 'dc:type']:
                val = util.getqattr(recobj, queryables[i]['dbcol'])
                if not val:
                    val = ''
                etree.SubElement(record, util.nspath_eval(i)).text = val

            if self.kvp['elementsetname'] in ['summary', 'full']:
                # add summary elements
                keywords = util.getqattr(recobj, queryables['dc:subject']['dbcol'])
                if keywords is not None:
                    for keyword in keywords.split(','):
                        etree.SubElement(record, 
                        util.nspath_eval('dc:subject')).text = keyword

                val = util.getqattr(recobj, queryables['dc:format']['dbcol'])
                if val:
                    etree.SubElement(record,
                    util.nspath_eval('dc:format')).text = val

                # links
                rlinks = util.getqattr(recobj,
                config.MD_CORE_MODEL['mappings']['pycsw:Links'])

                if rlinks:
                    links = rlinks.split('^')
                    for link in links:
                        linkset = link.split(',')
                        etree.SubElement(record,
                        util.nspath_eval('dct:references'),
                        scheme=linkset[2]).text = linkset[-1]

                for i in ['dc:relation', 'dct:modified', 'dct:abstract']:
                    val = util.getqattr(recobj, queryables[i]['dbcol'])
                    if val is not None:
                        etree.SubElement(record,
                        util.nspath_eval(i)).text = val

            if self.kvp['elementsetname'] == 'full':  # add full elements
                for i in ['dc:date', 'dc:creator', \
                'dc:publisher', 'dc:contributor', 'dc:source', \
                'dc:language', 'dc:rights']:
                    val = util.getqattr(recobj, queryables[i]['dbcol'])
                    if val:
                        etree.SubElement(record,
                        util.nspath_eval(i)).text = val

            # always write out ows:BoundingBox 
            bboxel = write_boundingbox(getattr(recobj,
            config.MD_CORE_MODEL['mappings']['pycsw:BoundingBox']))
            if bboxel is not None:
                record.append(bboxel)
        return record

    def _write_response(self):
        ''' Generate response '''
        # set HTTP response headers and XML declaration

        xmldecl=''
        appinfo=''

        if hasattr(self, 'log'):
            self.log.debug('Writing response.')

        if hasattr(self, 'soap') and self.soap:
            self._gen_soap_wrapper() 

        if (isinstance(self.kvp, dict) and self.kvp.has_key('outputformat') and
            self.kvp['outputformat'] == 'application/json'):
            http_header = 'Content-type:%s\r\n' % self.kvp['outputformat']
            from formats import fmt_json
            response = fmt_json.exml2json(self.response, config.NAMESPACES, self.pretty_print)
        else:  # it's XML
            http_header = 'Content-type:%s\r\n' % self.mimetype
            response = etree.tostring(self.response,
            pretty_print=self.pretty_print)
            xmldecl = '<?xml version="1.0" encoding="%s" standalone="no"?>\n' % self.encoding
            appinfo = '<!-- pycsw %s -->\n' % config.VERSION

        if hasattr(self, 'log'):
            self.log.debug('Response:\n%s' % response)

        if self.gzip and self.gzip_compresslevel > 0:
            import gzip

            buf = StringIO()
            gzipfile = gzip.GzipFile(mode='wb', fileobj=buf,
            compresslevel=self.gzip_compresslevel)
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

        if hasattr(self, 'exception') and self.exception:
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

    def _gen_manager(self):
        ''' Update config.MODEL with CSW-T advertising '''
        if (self.config.has_option('manager', 'transactions') and
            self.config.get('manager', 'transactions') == 'true'):
            config.MODEL['operations']['Transaction'] = \
            {'methods': {'get': False, 'post': True}, 'parameters': {}}

            config.MODEL['operations']['Harvest'] = \
            {'methods': {'get': False, 'post': True}, 'parameters': \
            {'ResourceType': {'values': \
            ['http://www.opengis.net/cat/csw/2.0.2']}}}

    def _parse_constraint(self, element):
        ''' Parse csw:Constraint '''

        query = {}

        tmp = element.find(util.nspath_eval('ogc:Filter'))
        if tmp is not None:
            self.log.debug('Filter constraint specified.')
            try:
                query['type'] = 'filter'
                query['where'] = fes.parse(tmp,
                self.repository.queryables['_all'], self.repository.dbtype)
            except Exception, err:
                return 'Invalid Filter request: %s' % err
        tmp = element.find(util.nspath_eval('csw:CqlText'))
        if tmp is not None:
            self.log.debug('CQL specified: %s.' % tmp.text)
            query['type'] = 'cql'
            query['where'] = self._cql_update_queryables_mappings(tmp.text,
            self.repository.queryables['_all'])
        return query

    def _test_manager(self):
        ''' Verify that transactions are allowed '''

        if self.config.get('manager', 'transactions') != 'true':
            raise RuntimeError, 'CSW-T interface is disabled'

        ipaddress = os.environ['REMOTE_ADDR']

        if self.config.has_option('manager', 'allowed_ips') is False or \
        (self.config.has_option('manager', 'allowed_ips') and ipaddress not in
        self.config.get('manager', 'allowed_ips').split(',')):
            raise RuntimeError, \
            'CSW-T operations not allowed for this IP address: %s' % ipaddress

    def _cql_update_queryables_mappings(self, cql, mappings):
        ''' Transform CQL query's properties to underlying DB columns '''
        self.log.debug('Raw CQL text = %s.' % cql)
        self.log.debug(str(mappings.keys()))
        if cql is not None:
            for key in mappings.keys():
                try:
                    cql = cql.replace(key, mappings[key]['dbcol'])
                except:
                    cql = cql.replace(key, mappings[key])
            self.log.debug('Interpolated CQL text = %s.' % cql)
            return cql

    def _write_transactionsummary(self, inserted=0, updated=0, deleted=0):
        ''' Write csw:TransactionSummary construct '''
        node = etree.Element(util.nspath_eval('csw:TransactionSummary'))
        etree.SubElement(node,
        util.nspath_eval('csw:totalInserted')).text = str(inserted)

        etree.SubElement(node,
        util.nspath_eval('csw:totalUpdated')).text = str(updated)

        etree.SubElement(node,
        util.nspath_eval('csw:totalDeleted')).text = str(deleted)
        return node

    def _write_acknowledgement(self, root=True):
        ''' Generate csw:Acknowledgement '''
        node = etree.Element(util.nspath_eval('csw:Acknowledgement'),
        nsmap = config.NAMESPACES, timeStamp=util.get_today_and_now())

        if root:
            node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
            '%s %s/csw/2.0.2/CSW-discovery.xsd' % (config.NAMESPACES['csw'], \
            self.config.get('server', 'ogc_schemas_base'))
    
        node1 = etree.SubElement(node, util.nspath_eval('csw:EchoedRequest'))
        if self.requesttype == 'POST':
            node1.append(etree.fromstring(self.request))
        else:  # GET
            node2 = etree.SubElement(node1, util.nspath_eval('ows:Get'))

            node2.text = self.request

        return node

    def _process_responsehandler(self, xml):
        ''' Process response handler '''

        if self.kvp['responsehandler'] is not None:
            self.log.debug('Processing responsehandler %s.' %
            self.kvp['responsehandler'])

            uprh = urlparse.urlparse(self.kvp['responsehandler'])

            if uprh.scheme == 'mailto':  # email
                import smtplib

                self.log.debug('Email detected.')

                smtp_host = 'localhost'
                if self.config.has_option('server', 'smtp_host'):
                    smtp_host = self.config.get('server', 'smtp_host')

                body = 'Subject: pycsw %s results\n\n%s' % \
                (self.kvp['request'], xml)

                try:
                    self.log.debug('Sending email.')
                    msg = smtplib.SMTP(smtp_host)
                    msg.sendmail(
                    self.config.get('metadata:main', 'contact_email'),
                    uprh.path, body)
                    msg.quit()
                    self.log.debug('Email sent successfully.')
                except Exception, err:
                    self.log.debug('Error processing email: %s.' % str(err))

            elif uprh.scheme == 'ftp':
                import ftplib

                self.log.debug('FTP detected.')

                try:
                    self.log.debug('Sending to FTP server.')
                    ftp = ftplib.FTP(uprh.hostname)
                    if uprh.username is not None:
                        ftp.login(uprh.username, uprh.password)
                    ftp.storbinary('STOR %s' % uprh.path[1:], StringIO(xml))
                    ftp.quit()
                    self.log.debug('FTP sent successfully.')
                except Exception, err:
                    self.log.debug('Error processing FTP: %s.' % str(err))

def write_boundingbox(bbox):
    ''' Generate ows:BoundingBox '''

    if bbox is not None:
        if bbox.find('SRID') != -1:  # it's EWKT; chop off 'SRID=\d+;'
            tmp = loads(bbox.split(';')[-1])
        else:
            tmp = loads(bbox)
        bbox2 = tmp.envelope.bounds

        if len(bbox2) == 4:
            boundingbox = etree.Element(util.nspath_eval('ows:BoundingBox'),
            crs='urn:x-ogc:def:crs:EPSG:6.11:4326', dimensions='2')

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
