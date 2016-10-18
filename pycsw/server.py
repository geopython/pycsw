# -*- coding: iso-8859-15 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
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
from urllib2 import quote, unquote
import urlparse
from cStringIO import StringIO
from ConfigParser import SafeConfigParser
from lxml import etree
from pycsw.plugins.profiles import profile as pprofile
import pycsw.plugins.outputschemas
from pycsw import config, fes, log, metadata, util, sru, opensearch
from pycsw.cql import cql2fes1
import logging

LOGGER = logging.getLogger(__name__)


class Csw(object):
    ''' Base CSW server '''
    def __init__(self, rtconfig=None, env=None):
        ''' Initialize CSW '''

        if not env:
            self.environ = os.environ
        else:
            self.environ = env

        self.context = config.StaticContext()

        # Lazy load this when needed
        # (it will permanently update global cfg namespaces)
        self.sruobj = None
        self.opensearchobj = None

        # init kvp
        self.kvp = {}

        self.mode = 'csw'
        self.async = False
        self.soap = False
        self.request = None
        self.exception = False
        self.profiles = None
        self.outputschemas = {}
        self.mimetype = 'application/xml; charset=UTF-8'
        self.encoding = 'UTF-8'
        self.pretty_print = 0
        self.domainquerytype = 'list'
        self.orm = 'django'
        self.language = {'639_code': 'en', 'text': 'english'}

        # load user configuration
        try:
            if isinstance(rtconfig, SafeConfigParser):  # serialized already
                self.config = rtconfig
            else:
                self.config = SafeConfigParser()
                if isinstance(rtconfig, dict):  # dictionary
                    for section, options in rtconfig.iteritems():
                        self.config.add_section(section)
                        for k, v in options.iteritems():
                            self.config.set(section, k, v)
                else:  # configuration file
                    import codecs
                    with codecs.open(rtconfig, encoding='utf-8') as scp:
                        self.config.readfp(scp)
        except Exception, err:
            self.response = self.exceptionreport(
            'NoApplicableCode', 'service',
            'Error opening configuration %s' % rtconfig)
            return

        # set server.home safely
        # TODO: make this more abstract
        self.config.set('server', 'home', os.path.dirname(
        os.path.join(os.path.dirname(__file__), '..')))

        self.context.pycsw_home = self.config.get('server', 'home')

        # configure transaction support, if specified in config
        self._gen_manager()

        log.setup_logger(self.config)

        LOGGER.debug('running configuration %s' % rtconfig)
        LOGGER.debug(str(self.environ['QUERY_STRING']))

        # generate domain model
        # NOTE: We should probably avoid this sort of mutable state for WSGI
        if 'GetDomain' not in self.context.model['operations']:
            self.context.model['operations']['GetDomain'] = \
            self.context.gen_domains()

        # set OGC schemas location
        if not self.config.has_option('server', 'ogc_schemas_base'):
            self.config.set('server', 'ogc_schemas_base',
            self.context.ogc_schemas_base)

        # set mimetype
        if self.config.has_option('server', 'mimetype'):
            self.mimetype = self.config.get('server', 'mimetype').encode()

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
        
        # set Spatial Ranking option
        if (self.config.has_option('server', 'spatial_ranking') and
        self.config.get('server', 'spatial_ranking') == 'true'):
            util.ranking_enabled = True

        # set language default
        if (self.config.has_option('server', 'language')):
            try:
                LOGGER.info('Setting language')
                lang_code = self.config.get('server', 'language').split('-')[0]
                self.language['639_code'] = lang_code
                self.language['text'] = self.context.languages[lang_code]
            except:
                pass

        # generate distributed search model, if specified in config
        if self.config.has_option('server', 'federatedcatalogues'):
            LOGGER.debug('Configuring distributed search.')

            self.context.model['constraints']['FederatedCatalogues'] = \
            {'values': []}

            for fedcat in \
            self.config.get('server', 'federatedcatalogues').split(','):
                self.context.model\
                ['constraints']['FederatedCatalogues']['values'].append(fedcat)

        LOGGER.debug('Configuration: %s.' % self.config)
        LOGGER.debug('Model: %s.' % self.context.model)

        # load user-defined mappings if they exist
        if self.config.has_option('repository', 'mappings'):
            # override default repository mappings
            try:
                import imp
                module = self.config.get('repository','mappings')
                modulename = '%s' % \
                os.path.splitext(module)[0].replace(os.sep, '.')
                LOGGER.debug(
                'Loading custom repository mappings from %s.' % module)
                mappings = imp.load_source(modulename, module)
                self.context.md_core_model = mappings.MD_CORE_MODEL
                self.context.refresh_dc(mappings.MD_CORE_MODEL)
            except Exception, err:
                self.response = self.exceptionreport(
                'NoApplicableCode', 'service',
                'Could not load repository.mappings %s' % str(err))

        # load profiles
        LOGGER.debug('Loading profiles.')

        if self.config.has_option('server', 'profiles'):
            self.profiles = pprofile.load_profiles(
            os.path.join('pycsw', 'plugins', 'profiles'),
            pprofile.Profile,
            self.config.get('server', 'profiles'))

            for prof in self.profiles['plugins'].keys():
                tmp = self.profiles['plugins'][prof](self.context.model,
                self.context.namespaces, self.context)

                key = tmp.outputschema  # to ref by outputschema
                self.profiles['loaded'][key] = tmp
                self.profiles['loaded'][key].extend_core(
                self.context.model, self.context.namespaces,
                self.config)

            LOGGER.debug('Profiles loaded: %s.' %
            self.profiles['loaded'].keys())

        # load profiles
        LOGGER.debug('Loading outputschemas.')

        for osch in pycsw.plugins.outputschemas.__all__:
            mod = getattr(__import__('pycsw.plugins.outputschemas.%s' % osch).plugins.outputschemas, osch)
            self.context.model['operations']['GetRecords']['parameters']['outputSchema']['values'].append(mod.NAMESPACE)
            self.context.model['operations']['GetRecordById']['parameters']['outputSchema']['values'].append(mod.NAMESPACE)
            if 'Harvest' in self.context.model['operations']:
                self.context.model['operations']['Harvest']['parameters']['ResourceType']['values'].append(mod.NAMESPACE)
            self.outputschemas[mod.NAMESPACE] = mod

        LOGGER.debug('Outputschemas loaded: %s.' % self.outputschemas)

        LOGGER.debug('Namespaces: %s' % self.context.namespaces)

        # init repository
        # look for tablename, set 'records' as default
        if not self.config.has_option('repository', 'table'):
            self.config.set('repository', 'table', 'records')

        repo_filter = None
        if self.config.has_option('repository', 'filter'):
            repo_filter = self.config.get('repository', 'filter')

        if (self.config.has_option('repository', 'source') and
            self.config.get('repository', 'source') == 'geonode'):

            # load geonode repository
            from pycsw.plugins.repository.geonode import geonode_

            try:
                self.repository = \
                geonode_.GeoNodeRepository(self.context, repo_filter)
                LOGGER.debug('GeoNode repository loaded (geonode): %s.' % \
                self.repository.dbtype)
            except Exception, err:
                self.response = self.exceptionreport(
                'NoApplicableCode', 'service',
                'Could not load repository (geonode): %s' % str(err))

        elif (self.config.has_option('repository', 'source') and
            self.config.get('repository', 'source') == 'odc'):

            # load odc repository
            from pycsw.plugins.repository.odc import odc

            try:
                self.repository = \
                odc.OpenDataCatalogRepository(self.context, repo_filter)
                LOGGER.debug('OpenDataCatalog repository loaded (geonode): %s.' % \
                self.repository.dbtype)
            except Exception, err:
                self.response = self.exceptionreport(
                'NoApplicableCode', 'service',
                'Could not load repository (odc): %s' % str(err))

        else:  # load default repository
            self.orm = 'sqlalchemy'
            from pycsw import repository
            try:
                self.repository = \
                repository.Repository(self.config.get('repository', 'database'),
                self.context, self.environ.get('local.app_root', None),
                self.config.get('repository', 'table'), repo_filter)
                LOGGER.debug('Repository loaded (local): %s.' \
                % self.repository.dbtype)
            except Exception, err:
                self.response = self.exceptionreport(
                'NoApplicableCode', 'service',
                'Could not load repository (local): %s' % str(err))

    def expand_path(self, path):
        ''' return safe path for WSGI environments '''
        if 'local.app_root' in self.environ and not os.path.isabs(path):
            return os.path.join(self.environ['local.app_root'], path)
        else:
            return path

    def dispatch_cgi(self):
        ''' CGI handler '''

        if hasattr(self,'response'):
            return self._write_response()

        LOGGER.debug('CGI mode detected')

        cgifs = cgi.FieldStorage(keep_blank_values=1)

        if cgifs.file:  # it's a POST request
            postdata = cgifs.file.read()
            self.requesttype = 'POST'
            self.request = postdata
            LOGGER.debug('Request type: POST.  Request:\n%s\n', self.request)
            self.kvp = self.parse_postdata(postdata)

        else:  # it's a GET request
            self.requesttype = 'GET'
            self.request = 'http://%s%s' % \
            (self.environ['HTTP_HOST'], self.environ['REQUEST_URI'])
            LOGGER.debug('Request type: GET.  Request:\n%s\n', self.request)
            for key in cgifs.keys():
                self.kvp[key.lower()] = cgifs[key].value

        return self.dispatch()

    def dispatch_wsgi(self):
        ''' WSGI handler '''

        if hasattr(self,'response'):
            return self._write_response()

        LOGGER.debug('WSGI mode detected')

        if self.environ['REQUEST_METHOD'] == 'POST':
            try:
                request_body_size = int(self.environ.get('CONTENT_LENGTH', 0))
            except (ValueError):
                request_body_size = 0

            postdata = self.environ['wsgi.input'].read(request_body_size)

            self.requesttype = 'POST'
            self.request = postdata
            LOGGER.debug('Request type: POST.  Request:\n%s\n', self.request)
            self.kvp = self.parse_postdata(postdata)

        else:  # it's a GET request
            self.requesttype = 'GET'

            scheme = '%s://' % self.environ['wsgi.url_scheme']

            if self.environ.get('HTTP_HOST'):
                url = '%s%s' % (scheme, self.environ['HTTP_HOST'])
            else:
                url = '%s%s' % (scheme, self.environ['SERVER_NAME'])

                if self.environ['wsgi.url_scheme'] == 'https':
                    if self.environ['SERVER_PORT'] != '443':
                        url += ':' + self.environ['SERVER_PORT']
                else:
                    if self.environ['SERVER_PORT'] != '80':
                        url += ':' + self.environ['SERVER_PORT']

            url += quote(self.environ.get('SCRIPT_NAME', ''))
            url += quote(self.environ.get('PATH_INFO', ''))

            if self.environ.get('QUERY_STRING'):
                url += '?' + self.environ['QUERY_STRING']

            self.request = url
            LOGGER.debug('Request type: GET.  Request:\n%s\n', self.request)

            pairs = self.environ.get('QUERY_STRING').split("&")

            kvp = {}

            for pairstr in pairs:
                pair = pairstr.split("=")
                pair[0] = pair[0].lower()
                pair = [unquote(a) for a in pair]

                if len(pair) is 1:
                    kvp[pair[0]] = ""
                else:
                    kvp[pair[0]] = pair[1]

            self.kvp = kvp

        return self.dispatch()

    def opensearch(self):
        ''' enable OpenSearch '''
        if not self.opensearchobj:
            self.opensearchobj = opensearch.OpenSearch(self.context)

        return self.opensearchobj

    def sru(self):
        ''' enable SRU '''
        if not self.sruobj:
            self.sruobj = sru.Sru(self.context)

        return self.sruobj

    def dispatch(self, writer=sys.stdout, write_headers=True):
        ''' Handle incoming HTTP request '''

        error = 0

        if isinstance(self.kvp, str):  # it's an exception
            error = 1
            locator = 'service'
            text = self.kvp
            if (self.kvp.find('the document is not valid') != -1 or
                self.kvp.find('document not well-formed') != -1):
                code = 'NoApplicableCode'
            else:
                code = 'InvalidParameterValue'

        LOGGER.debug('HTTP Headers:\n%s.' % self.environ)
        LOGGER.debug('Parsed request parameters: %s' % self.kvp)

        if (not isinstance(self.kvp, str) and
        'mode' in self.kvp and self.kvp['mode'] == 'sru'):
            self.mode = 'sru'
            LOGGER.debug('SRU mode detected; processing request.')
            self.kvp = self.sru().request_sru2csw(self.kvp)

        if (not isinstance(self.kvp, str) and
        'mode' in self.kvp and self.kvp['mode'] == 'opensearch'):
            self.mode = 'opensearch'
            LOGGER.debug('OpenSearch mode detected; processing request.')
            self.kvp['outputschema'] = 'http://www.w3.org/2005/Atom'

        if error == 0:
            # test for the basic keyword values (service, version, request)
            for k in ['service', 'version', 'request']:
                if k not in self.kvp:
                    if (k == 'version' and 'request' in self.kvp and
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
                if ('version' in self.kvp and
                    util.get_version_integer(self.kvp['version']) !=
                    util.get_version_integer('2.0.2') and
                    self.kvp['request'] != 'GetCapabilities'):
                    error = 1
                    locator = 'version'
                    code = 'InvalidParameterValue'
                    text = 'Invalid value for version: %s.\
                    Value MUST be 2.0.2' % self.kvp['version']

                # check for GetCapabilities acceptversions
                if 'acceptversions' in self.kvp:
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
                if self.kvp['request'] not in \
                    self.context.model['operations'].keys():
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

            if 'responsehandler' in self.kvp:
                # set flag to process asynchronously
                import threading
                self.async = True
                if ('requestid' not in self.kvp
                or self.kvp['requestid'] is None):
                    import uuid
                    self.kvp['requestid'] = str(uuid.uuid4())

            if self.kvp['request'] == 'GetCapabilities':
                self.response = self.getcapabilities()
            elif self.kvp['request'] == 'DescribeRecord':
                self.response = self.describerecord()
            elif self.kvp['request'] == 'GetDomain':
                self.response = self.getdomain()
            elif self.kvp['request'] == 'GetRecords':
                if self.async:  # process asynchronously
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
                if self.async:  # process asynchronously
                    threading.Thread(target=self.harvest).start()
                    self.response = self._write_acknowledgement()
                else:
                    self.response = self.harvest()
            else:
                self.response = self.exceptionreport('InvalidParameterValue',
                'request', 'Invalid request parameter: %s' %
                self.kvp['request'])

        if self.mode == 'sru':
            LOGGER.debug('SRU mode detected; processing response.')
            self.response = self.sru().response_csw2sru(self.response,
                            self.environ)
        elif self.mode == 'opensearch':
            LOGGER.debug('OpenSearch mode detected; processing response.')
            self.response = self.opensearch().response_csw2opensearch(
                            self.response, self.config)

        return self._write_response()

    def exceptionreport(self, code, locator, text):
        ''' Generate ExceptionReport '''
        self.exception = True

        try:
            language = self.config.get('server', 'language')
            ogc_schemas_base = self.config.get('server', 'ogc_schemas_base')
        except:
            language = 'en-US'
            ogc_schemas_base = self.context.ogc_schemas_base

        node = etree.Element(util.nspath_eval('ows:ExceptionReport',
        self.context.namespaces), nsmap=self.context.namespaces,
        version='1.2.0', language=language)

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.context.namespaces)] = \
        '%s %s/ows/1.0.0/owsExceptionReport.xsd' % \
        (self.context.namespaces['ows'], ogc_schemas_base)

        exception = etree.SubElement(node, util.nspath_eval('ows:Exception',
        self.context.namespaces),
        exceptionCode=code, locator=locator)

        etree.SubElement(exception,
        util.nspath_eval('ows:ExceptionText',
        self.context.namespaces)).text = text

        return node

    def getcapabilities(self):
        ''' Handle GetCapabilities request '''
        serviceidentification = True
        serviceprovider = True
        operationsmetadata = True
        if 'sections' in self.kvp:
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

        node = etree.Element(util.nspath_eval('csw:Capabilities',
        self.context.namespaces),
        nsmap=self.context.namespaces, version='2.0.2',
        updateSequence=str(updatesequence))

        if 'updatesequence' in self.kvp:
            if int(self.kvp['updatesequence']) == updatesequence:
                return node
            elif int(self.kvp['updatesequence']) > updatesequence:
                return self.exceptionreport('InvalidUpdateSequence',
                'updatesequence',
                'outputsequence specified (%s) is higher than server\'s \
                updatesequence (%s)' % (self.kvp['updatesequence'],
                updatesequence))

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.context.namespaces)] = '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (self.context.namespaces['csw'],
         self.config.get('server', 'ogc_schemas_base'))

        metadata_main = dict(self.config.items('metadata:main'))

        if serviceidentification:
            LOGGER.debug('Writing section ServiceIdentification.')

            serviceidentification = etree.SubElement(node, \
            util.nspath_eval('ows:ServiceIdentification',
            self.context.namespaces))

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Title', self.context.namespaces)).text = \
            metadata_main.get('identification_title', 'missing')

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Abstract', self.context.namespaces)).text = \
            metadata_main.get('identification_abstract', 'missing')

            keywords = etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Keywords', self.context.namespaces))

            for k in \
            metadata_main.get('identification_keywords').split(','):
                etree.SubElement(
                keywords, util.nspath_eval('ows:Keyword',
                self.context.namespaces)).text = k

            etree.SubElement(keywords,
            util.nspath_eval('ows:Type', self.context.namespaces),
            codeSpace='ISOTC211/19115').text = \
            metadata_main.get('identification_keywords_type', 'missing')

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:ServiceType', self.context.namespaces),
            codeSpace='OGC').text = 'CSW'

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:ServiceTypeVersion',
            self.context.namespaces)).text = '2.0.2'

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Fees', self.context.namespaces)).text = \
            metadata_main.get('identification_fees', 'missing')

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:AccessConstraints',
            self.context.namespaces)).text = \
            metadata_main.get('identification_accessconstraints', 'missing')

        if serviceprovider:
            LOGGER.debug('Writing section ServiceProvider.')
            serviceprovider = etree.SubElement(node,
            util.nspath_eval('ows:ServiceProvider', self.context.namespaces))

            etree.SubElement(serviceprovider,
            util.nspath_eval('ows:ProviderName', self.context.namespaces)).text = \
            metadata_main.get('provider_name', 'missing')

            providersite = etree.SubElement(serviceprovider,
            util.nspath_eval('ows:ProviderSite', self.context.namespaces))

            providersite.attrib[util.nspath_eval('xlink:type',
            self.context.namespaces)] = 'simple'

            providersite.attrib[util.nspath_eval('xlink:href',
            self.context.namespaces)] = \
            metadata_main.get('provider_url', 'missing')

            servicecontact = etree.SubElement(serviceprovider,
            util.nspath_eval('ows:ServiceContact', self.context.namespaces))

            etree.SubElement(servicecontact,
            util.nspath_eval('ows:IndividualName',
            self.context.namespaces)).text = \
            metadata_main.get('contact_name', 'missing')

            etree.SubElement(servicecontact,
            util.nspath_eval('ows:PositionName',
            self.context.namespaces)).text = \
            metadata_main.get('contact_position', 'missing')

            contactinfo = etree.SubElement(servicecontact,
            util.nspath_eval('ows:ContactInfo', self.context.namespaces))

            phone = etree.SubElement(contactinfo, util.nspath_eval('ows:Phone',
            self.context.namespaces))

            etree.SubElement(phone, util.nspath_eval('ows:Voice',
            self.context.namespaces)).text = \
            metadata_main.get('contact_phone', 'missing')

            etree.SubElement(phone, util.nspath_eval('ows:Facsimile',
            self.context.namespaces)).text = \
            metadata_main.get('contact_fax', 'missing')

            address = etree.SubElement(contactinfo,
            util.nspath_eval('ows:Address', self.context.namespaces))

            etree.SubElement(address,
            util.nspath_eval('ows:DeliveryPoint',
            self.context.namespaces)).text = \
            metadata_main.get('contact_address', 'missing')

            etree.SubElement(address, util.nspath_eval('ows:City',
            self.context.namespaces)).text = \
            metadata_main.get('contact_city', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows:AdministrativeArea',
            self.context.namespaces)).text = \
            metadata_main.get('contact_stateorprovince', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows:PostalCode',
            self.context.namespaces)).text = \
            metadata_main.get('contact_postalcode', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows:Country', self.context.namespaces)).text = \
            metadata_main.get('contact_country', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows:ElectronicMailAddress',
            self.context.namespaces)).text = \
            metadata_main.get('contact_email', 'missing')

            url = etree.SubElement(contactinfo,
            util.nspath_eval('ows:OnlineResource', self.context.namespaces))

            url.attrib[util.nspath_eval('xlink:type',
            self.context.namespaces)] = 'simple'

            url.attrib[util.nspath_eval('xlink:href',
            self.context.namespaces)] = \
            metadata_main.get('contact_url', 'missing')

            etree.SubElement(contactinfo,
            util.nspath_eval('ows:HoursOfService',
            self.context.namespaces)).text = \
            metadata_main.get('contact_hours', 'missing')

            etree.SubElement(contactinfo,
            util.nspath_eval('ows:ContactInstructions',
            self.context.namespaces)).text = \
            metadata_main.get('contact_instructions', 'missing')

            etree.SubElement(servicecontact,
            util.nspath_eval('ows:Role', self.context.namespaces),
            codeSpace='ISOTC211/19115').text = \
            metadata_main.get('contact_role', 'missing')

        if operationsmetadata:
            LOGGER.debug('Writing section OperationsMetadata.')
            operationsmetadata = etree.SubElement(node,
            util.nspath_eval('ows:OperationsMetadata',
            self.context.namespaces))

            for operation in self.context.model['operations'].keys():
                oper = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows:Operation', self.context.namespaces),
                name=operation)

                dcp = etree.SubElement(oper, util.nspath_eval('ows:DCP',
                self.context.namespaces))

                http = etree.SubElement(dcp, util.nspath_eval('ows:HTTP',
                self.context.namespaces))

                if self.context.model['operations'][operation]['methods']['get']:
                    get = etree.SubElement(http, util.nspath_eval('ows:Get',
                    self.context.namespaces))

                    get.attrib[util.nspath_eval('xlink:type',\
                    self.context.namespaces)] = 'simple'

                    get.attrib[util.nspath_eval('xlink:href',\
                    self.context.namespaces)] = self.config.get('server', 'url')

                if self.context.model['operations'][operation]['methods']['post']:
                    post = etree.SubElement(http, util.nspath_eval('ows:Post',
                    self.context.namespaces))
                    post.attrib[util.nspath_eval('xlink:type',
                    self.context.namespaces)] = 'simple'
                    post.attrib[util.nspath_eval('xlink:href',
                    self.context.namespaces)] = \
                    self.config.get('server', 'url')

                for parameter in \
                self.context.model['operations'][operation]['parameters']:
                    param = etree.SubElement(oper,
                    util.nspath_eval('ows:Parameter',
                    self.context.namespaces), name=parameter)

                    for val in \
                    self.context.model['operations'][operation]\
                    ['parameters'][parameter]['values']:
                        etree.SubElement(param,
                        util.nspath_eval('ows:Value',
                        self.context.namespaces)).text = val

                if operation == 'GetRecords':  # advertise queryables
                    for qbl in self.repository.queryables.keys():
                        if qbl != '_all':
                            param = etree.SubElement(oper,
                            util.nspath_eval('ows:Constraint',
                            self.context.namespaces), name=qbl)

                            for qbl2 in self.repository.queryables[qbl]:
                                etree.SubElement(param,
                                util.nspath_eval('ows:Value',
                                self.context.namespaces)).text = qbl2

                    if self.profiles is not None:
                        for con in self.context.model[\
                        'operations']['GetRecords']['constraints'].keys():
                            param = etree.SubElement(oper,
                            util.nspath_eval('ows:Constraint',
                            self.context.namespaces), name = con)
                            for val in self.context.model['operations']\
                            ['GetRecords']['constraints'][con]['values']:
                                etree.SubElement(param,
                                util.nspath_eval('ows:Value',
                                self.context.namespaces)).text = val

            for parameter in self.context.model['parameters'].keys():
                param = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows:Parameter', self.context.namespaces),
                name=parameter)

                for val in self.context.model['parameters'][parameter]['values']:
                    etree.SubElement(param, util.nspath_eval('ows:Value',
                    self.context.namespaces)).text = val

            for constraint in self.context.model['constraints'].keys():
                param = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows:Constraint', self.context.namespaces),
                name=constraint)

                for val in self.context.model['constraints'][constraint]['values']:
                    etree.SubElement(param, util.nspath_eval('ows:Value',
                    self.context.namespaces)).text = val

            if self.profiles is not None:
                for prof in self.profiles['loaded'].keys():
                    ecnode = \
                    self.profiles['loaded'][prof].get_extendedcapabilities()
                    if ecnode is not None:
                        operationsmetadata.append(ecnode)

        # always write out Filter_Capabilities
        LOGGER.debug('Writing section Filter_Capabilities.')
        fltcaps = etree.SubElement(node,
        util.nspath_eval('ogc:Filter_Capabilities', self.context.namespaces))

        spatialcaps = etree.SubElement(fltcaps,
        util.nspath_eval('ogc:Spatial_Capabilities', self.context.namespaces))

        geomops = etree.SubElement(spatialcaps,
        util.nspath_eval('ogc:GeometryOperands', self.context.namespaces))

        for geomtype in \
        fes.MODEL['GeometryOperands']['values']:
            etree.SubElement(geomops,
            util.nspath_eval('ogc:GeometryOperand',
            self.context.namespaces)).text = geomtype

        spatialops = etree.SubElement(spatialcaps,
        util.nspath_eval('ogc:SpatialOperators', self.context.namespaces))

        for spatial_comparison in \
        fes.MODEL['SpatialOperators']['values']:
            etree.SubElement(spatialops,
            util.nspath_eval('ogc:SpatialOperator', self.context.namespaces),
            name=spatial_comparison)

        scalarcaps = etree.SubElement(fltcaps,
        util.nspath_eval('ogc:Scalar_Capabilities', self.context.namespaces))

        etree.SubElement(scalarcaps, util.nspath_eval('ogc:LogicalOperators',
        self.context.namespaces))

        cmpops = etree.SubElement(scalarcaps,
        util.nspath_eval('ogc:ComparisonOperators', self.context.namespaces))

        for cmpop in fes.MODEL['ComparisonOperators'].keys():
            etree.SubElement(cmpops,
            util.nspath_eval('ogc:ComparisonOperator',
            self.context.namespaces)).text = \
            fes.MODEL['ComparisonOperators'][cmpop]['opname']

        arithops = etree.SubElement(scalarcaps,
        util.nspath_eval('ogc:ArithmeticOperators', self.context.namespaces))

        functions = etree.SubElement(arithops,
        util.nspath_eval('ogc:Functions', self.context.namespaces))

        functionames = etree.SubElement(functions,
        util.nspath_eval('ogc:FunctionNames', self.context.namespaces))

        for fnop in sorted(fes.MODEL['Functions'].keys()):
            etree.SubElement(functionames,
            util.nspath_eval('ogc:FunctionName', self.context.namespaces),
            nArgs=fes.MODEL['Functions'][fnop]['args']).text = fnop

        idcaps = etree.SubElement(fltcaps,
        util.nspath_eval('ogc:Id_Capabilities', self.context.namespaces))

        for idcap in fes.MODEL['Ids']['values']:
            etree.SubElement(idcaps, util.nspath_eval('ogc:%s' % idcap,
            self.context.namespaces))

        return node

    def describerecord(self):
        ''' Handle DescribeRecord request '''

        if 'typename' not in self.kvp or \
        len(self.kvp['typename']) == 0:  # missing typename
        # set to return all typenames
            self.kvp['typename'] = ['csw:Record']

            if self.profiles is not None:
                for prof in self.profiles['loaded'].keys():
                    self.kvp['typename'].append(
                    self.profiles['loaded'][prof].typename)

        elif self.requesttype == 'GET':  # pass via GET
            self.kvp['typename'] = self.kvp['typename'].split(',')

        if ('outputformat' in self.kvp and
            self.kvp['outputformat'] not in
            self.context.model['operations']['DescribeRecord']
            ['parameters']['outputFormat']['values']):  # bad outputformat
            return self.exceptionreport('InvalidParameterValue',
            'outputformat', 'Invalid value for outputformat: %s' %
            self.kvp['outputformat'])

        if ('schemalanguage' in self.kvp and
            self.kvp['schemalanguage'] not in
            self.context.model['operations']['DescribeRecord']['parameters']
            ['schemaLanguage']['values']):  # bad schemalanguage
            return self.exceptionreport('InvalidParameterValue',
            'schemalanguage', 'Invalid value for schemalanguage: %s' %
            self.kvp['schemalanguage'])

        node = etree.Element(util.nspath_eval('csw:DescribeRecordResponse',
        self.context.namespaces), nsmap=self.context.namespaces)

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.context.namespaces)] = \
        '%s %s/csw/2.0.2/CSW-discovery.xsd' % (self.context.namespaces['csw'],
        self.config.get('server', 'ogc_schemas_base'))

        for typename in self.kvp['typename']:
            if typename.find(':') == -1:  # unqualified typename
                return self.exceptionreport('InvalidParameterValue',
                'typename', 'Typename not qualified: %s' % typename)
            if typename == 'csw:Record':   # load core schema
                LOGGER.debug('Writing csw:Record schema.')
                schemacomponent = etree.SubElement(node,
                util.nspath_eval('csw:SchemaComponent', self.context.namespaces),
                schemaLanguage='XMLSCHEMA',
                targetNamespace=self.context.namespaces['csw'])

                path = os.path.join(self.config.get('server', 'home'),
                'schemas', 'ogc', 'csw', '2.0.2', 'record.xsd')

                dublincore = etree.parse(path, self.context.parser).getroot()

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
        if ('parametername' not in self.kvp and
            'propertyname' not in self.kvp):
            return self.exceptionreport('MissingParameterValue',
            'parametername', 'Missing value. \
            One of propertyname or parametername must be specified')

        node = etree.Element(util.nspath_eval('csw:GetDomainResponse',
        self.context.namespaces), nsmap=self.context.namespaces)

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.context.namespaces)] = '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (self.context.namespaces['csw'],
        self.config.get('server', 'ogc_schemas_base'))

        if 'parametername' in self.kvp:
            for pname in self.kvp['parametername'].split(','):
                LOGGER.debug('Parsing parametername %s.' % pname)
                domainvalue = etree.SubElement(node,
                util.nspath_eval('csw:DomainValues', self.context.namespaces),
                type='csw:Record')
                etree.SubElement(domainvalue,
                util.nspath_eval('csw:ParameterName',
                self.context.namespaces)).text = pname
                try:
                    operation, parameter = pname.split('.')
                except:
                    return node
                if (operation in self.context.model['operations'].keys() and
                    parameter in
                    self.context.model['operations'][operation]['parameters'].keys()):
                    listofvalues = etree.SubElement(domainvalue,
                    util.nspath_eval('csw:ListOfValues', self.context.namespaces))
                    for val in \
                    self.context.model['operations'][operation]\
                    ['parameters'][parameter]['values']:
                        etree.SubElement(listofvalues,
                        util.nspath_eval('csw:Value',
                        self.context.namespaces)).text = val

        if 'propertyname' in self.kvp:
            for pname in self.kvp['propertyname'].split(','):
                LOGGER.debug('Parsing propertyname %s.' % pname)

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
                util.nspath_eval('csw:DomainValues', self.context.namespaces),
                type=dvtype)
                etree.SubElement(domainvalue,
                util.nspath_eval('csw:PropertyName',
                self.context.namespaces)).text = pname

                try:
                    LOGGER.debug(
                    'Querying repository property %s, typename %s, \
                    domainquerytype %s.' % \
                    (pname2, dvtype, self.domainquerytype))

                    count = False

                    if (self.config.has_option('server', 'domaincounts') and
                        self.config.get('server', 'domaincounts') == 'true'):
                        count = True

                    results = self.repository.query_domain(
                    pname2, dvtype, self.domainquerytype, count)

                    LOGGER.debug('Results: %s' % str(len(results)))

                    if self.domainquerytype == 'range':
                        rangeofvalues = etree.SubElement(domainvalue,
                        util.nspath_eval('csw:RangeOfValues',
                        self.context.namespaces))

                        etree.SubElement(rangeofvalues,
                        util.nspath_eval('csw:MinValue',
                        self.context.namespaces)).text = results[0][0]

                        etree.SubElement(rangeofvalues,
                        util.nspath_eval('csw:MaxValue',
                        self.context.namespaces)).text = results[0][1]
                    else:
                        listofvalues = etree.SubElement(domainvalue,
                        util.nspath_eval('csw:ListOfValues',
                        self.context.namespaces))
                        for result in results:
                            LOGGER.debug(str(result))
                            if (result is not None and
                                result[0] is not None):  # drop null values
                                if count:  # show counts
                                    val = '%s (%s)' % (result[0], result[1])
                                else:
                                    val = result[0]
                                etree.SubElement(listofvalues,
                                util.nspath_eval('csw:Value',
                                self.context.namespaces)).text = val
                except Exception, err:
                    LOGGER.debug('No results for propertyname %s: %s.' %
                    (pname2, str(err)))
        return node

    def getrecords(self):
        ''' Handle GetRecords request '''

        timestamp = util.get_today_and_now()

        if ('elementsetname' not in self.kvp and
            'elementname' not in self.kvp):
            # mutually exclusive required
            return self.exceptionreport('MissingParameterValue',
            'elementsetname',
            'Missing one of ElementSetName or ElementName parameter(s)')

        if 'outputschema' not in self.kvp:
            self.kvp['outputschema'] = self.context.namespaces['csw']

        if (self.kvp['outputschema'] not in self.context.model['operations']
            ['GetRecords']['parameters']['outputSchema']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputschema', 'Invalid outputSchema parameter value: %s' %
            self.kvp['outputschema'])

        if 'outputformat' not in self.kvp:
            self.kvp['outputformat'] = 'application/xml'

        if (self.kvp['outputformat'] not in self.context.model['operations']
            ['GetRecords']['parameters']['outputFormat']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputformat', 'Invalid outputFormat parameter value: %s' %
            self.kvp['outputformat'])

        if 'resulttype' not in self.kvp:
            self.kvp['resulttype'] = 'hits'

        if self.kvp['resulttype'] is not None:
            if (self.kvp['resulttype'] not in self.context.model['operations']
            ['GetRecords']['parameters']['resultType']['values']):
                return self.exceptionreport('InvalidParameterValue',
                'resulttype', 'Invalid resultType parameter value: %s' %
                self.kvp['resulttype'])

        if (('elementname' not in self.kvp or
             len(self.kvp['elementname']) == 0) and
             self.kvp['elementsetname'] not in
             self.context.model['operations']['GetRecords']['parameters']
             ['ElementSetName']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'elementsetname', 'Invalid ElementSetName parameter value: %s' %
            self.kvp['elementsetname'])

        if ('elementname' in self.kvp and
            self.requesttype == 'GET'):  # passed via GET
            self.kvp['elementname'] = self.kvp['elementname'].split(',')
            self.kvp['elementsetname'] = 'summary'

        if 'typenames' not in self.kvp:
            return self.exceptionreport('MissingParameterValue',
            'typenames', 'Missing typenames parameter')

        if ('typenames' in self.kvp and
            self.requesttype == 'GET'):  # passed via GET
            self.kvp['typenames'] = self.kvp['typenames'].split(',')

        if 'typenames' in self.kvp:
            for tname in self.kvp['typenames']:
                if (tname not in self.context.model['operations']['GetRecords']
                    ['parameters']['typeNames']['values']):
                    return self.exceptionreport('InvalidParameterValue',
                    'typenames', 'Invalid typeNames parameter value: %s' %
                    tname)

        # check elementname's
        if 'elementname' in self.kvp:
            for ename in self.kvp['elementname']:
                enamelist = self.repository.queryables['_all'].keys()
                if ename not in enamelist:
                    return self.exceptionreport('InvalidParameterValue',
                    'elementname', 'Invalid ElementName parameter value: %s' %
                    ename)

        if self.kvp['resulttype'] == 'validate':
            return self._write_acknowledgement()

        maxrecords_cfg = -1  # not set in config server.maxrecords

        if self.config.has_option('server', 'maxrecords'):
            maxrecords_cfg = int(self.config.get('server', 'maxrecords'))

        if 'maxrecords' not in self.kvp:  # not specified by client
            if maxrecords_cfg > -1:  # specified in config
                self.kvp['maxrecords'] = maxrecords_cfg
            else:  # spec default
                self.kvp['maxrecords'] = 10
        else:  # specified by client
            if maxrecords_cfg > -1:  # set in config
                if int(self.kvp['maxrecords']) > maxrecords_cfg:
                    self.kvp['maxrecords'] = maxrecords_cfg

        if self.requesttype == 'GET':
            if 'constraint' in self.kvp:
                # GET request
                LOGGER.debug('csw:Constraint passed over HTTP GET.')
                if 'constraintlanguage' not in self.kvp:
                    return self.exceptionreport('MissingParameterValue',
                    'constraintlanguage',
                    'constraintlanguage required when constraint specified')
                if (self.kvp['constraintlanguage'] not in
                self.context.model['operations']['GetRecords']['parameters']
                ['CONSTRAINTLANGUAGE']['values']):
                    return self.exceptionreport('InvalidParameterValue',
                    'constraintlanguage', 'Invalid constraintlanguage: %s'
                    % self.kvp['constraintlanguage'])
                if self.kvp['constraintlanguage'] == 'CQL_TEXT':
                    tmp = self.kvp['constraint']
                    try:
                        LOGGER.debug('Transforming CQL into fes1')
                        LOGGER.debug('CQL: %s', tmp)
                        self.kvp['constraint'] = {}
                        self.kvp['constraint']['type'] = 'filter'
                        cql = cql2fes1(tmp, self.context.namespaces)
                        self.kvp['constraint']['where'], self.kvp['constraint']['values'] = fes.parse(cql,
                        self.repository.queryables['_all'], self.repository.dbtype,
                        self.context.namespaces, self.orm, self.language['text'], self.repository.fts)
                    except Exception as err:
                        LOGGER.error('Invalid CQL query %s', tmp)
                        LOGGER.error('Error message: %s', err, exc_info=True)
                        return self.exceptionreport('InvalidParameterValue',
                        'constraint', 'Invalid Filter syntax')
                elif self.kvp['constraintlanguage'] == 'FILTER':
                    # validate filter XML
                    try:
                        schema = os.path.join(self.config.get('server', 'home'),
                        'schemas', 'ogc', 'filter', '1.1.0', 'filter.xsd')
                        LOGGER.debug('Validating Filter %s.' %
                        self.kvp['constraint'])
                        schema = etree.XMLSchema(file=schema)
                        parser = etree.XMLParser(schema=schema, resolve_entities=False)
                        doc = etree.fromstring(self.kvp['constraint'], parser)
                        LOGGER.debug('Filter is valid XML.')
                        self.kvp['constraint'] = {}
                        self.kvp['constraint']['type'] = 'filter'
                        self.kvp['constraint']['where'], self.kvp['constraint']['values'] = \
                        fes.parse(doc,
                        self.repository.queryables['_all'].keys(),
                        self.repository.dbtype,
                        self.context.namespaces, self.orm, self.language['text'], self.repository.fts)
                    except Exception, err:
                        errortext = \
                        'Exception: document not valid.\nError: %s.' % str(err)

                        LOGGER.debug(errortext)
                        return self.exceptionreport('InvalidParameterValue',
                        'constraint', 'Invalid Filter query: %s' % errortext)
            else:
                self.kvp['constraint'] = {}

        if 'sortby' not in self.kvp:
            self.kvp['sortby'] = None
        elif 'sortby' in self.kvp and self.requesttype == 'GET':
            LOGGER.debug('Sorted query specified.')
            tmp = self.kvp['sortby']
            self.kvp['sortby'] = {}

            try:
                name, order = tmp.rsplit(':', 1)
            except:
                return self.exceptionreport('InvalidParameterValue',
                'sortby', 'Invalid SortBy value: must be in the format\
                propertyname:A or propertyname:D')

            try:
                self.kvp['sortby']['propertyname'] = \
                self.repository.queryables['_all'][name]['dbcol']
                if name.find('BoundingBox') != -1 or name.find('Envelope') != -1:
                    # it's a spatial sort
                    self.kvp['sortby']['spatial'] = True
            except Exception, err:
                return self.exceptionreport('InvalidParameterValue',
                'sortby', 'Invalid SortBy propertyname: %s' % name)

            if order not in ['A', 'D']:
                return self.exceptionreport('InvalidParameterValue',
                'sortby', 'Invalid SortBy value: sort order must be "A" or "D"')

            if order == 'D':
                self.kvp['sortby']['order'] = 'DESC'
            else:
                self.kvp['sortby']['order'] = 'ASC'

        if 'startposition' not in self.kvp:
            self.kvp['startposition'] = 1

        # query repository
        LOGGER.debug('Querying repository with constraint: %s,\
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
            LOGGER.debug('Invalid query syntax.  Query: %s', self.kvp['constraint'])
            LOGGER.debug('Invalid query syntax.  Result: %s', err)
            return self.exceptionreport('InvalidParameterValue', 'constraint',
            'Invalid query syntax')

        dsresults = []

        if (self.config.has_option('server', 'federatedcatalogues') and
            'distributedsearch' in self.kvp and
            self.kvp['distributedsearch'] and self.kvp['hopcount'] > 0):
            # do distributed search

            LOGGER.debug('DistributedSearch specified (hopCount: %s).' %
            self.kvp['hopcount'])

            from owslib.csw import CatalogueServiceWeb
            for fedcat in \
            self.config.get('server', 'federatedcatalogues').split(','):
                LOGGER.debug('Performing distributed search on federated \
                catalogue: %s.' % fedcat)
                remotecsw = CatalogueServiceWeb(fedcat, skip_caps=True)
                try:
                    remotecsw.getrecords2(xml=self.request)
                    if hasattr(remotecsw, 'results'):
                        LOGGER.debug(
                        'Distributed search results from catalogue \
                        %s: %s.' % (fedcat, remotecsw.results))

                        remotecsw_matches = int(remotecsw.results['matches'])
                        plural = 's' if remotecsw_matches != 1 else ''
                        if remotecsw_matches > 0:
                            matched = str(int(matched) + remotecsw_matches)
                            dsresults.append(etree.Comment(
                            ' %d result%s from %s ' %
                            (remotecsw_matches, plural, fedcat)))

                            dsresults.append(remotecsw.records)

                except Exception, err:
                    error_string = 'remote CSW %s returned error: ' % fedcat
                    dsresults.append(etree.Comment(
                    ' %s\n\n%s ' % (error_string, remotecsw.response)))
                    LOGGER.debug(str(err))

        if int(matched) == 0:
            returned = nextrecord = '0'
        else:
            if int(matched) < int(self.kvp['maxrecords']):
                returned = matched
                nextrecord = '0'
            else:
                returned = str(self.kvp['maxrecords'])
                if int(self.kvp['startposition']) + int(self.kvp['maxrecords']) >= int(matched):
                    nextrecord = '0'
                else:
                    nextrecord = str(int(self.kvp['startposition']) + \
                    int(self.kvp['maxrecords']))

        LOGGER.debug('Results: matched: %s, returned: %s, next: %s.' % \
        (matched, returned, nextrecord))

        node = etree.Element(util.nspath_eval('csw:GetRecordsResponse',
        self.context.namespaces),
        nsmap=self.context.namespaces, version='2.0.2')

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.context.namespaces)] = \
        '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (self.context.namespaces['csw'], self.config.get('server', 'ogc_schemas_base'))

        if 'requestid' in self.kvp and self.kvp['requestid'] is not None:
            etree.SubElement(node, util.nspath_eval('csw:RequestId',
            self.context.namespaces)).text = self.kvp['requestid']

        etree.SubElement(node, util.nspath_eval('csw:SearchStatus',
        self.context.namespaces), timestamp=timestamp)

        if 'where' not in self.kvp['constraint'] and \
        self.kvp['resulttype'] is None:
            returned = '0'

        searchresults = etree.SubElement(node,
        util.nspath_eval('csw:SearchResults', self.context.namespaces),
        numberOfRecordsMatched=matched, numberOfRecordsReturned=returned,
        nextRecord=nextrecord, recordSchema=self.kvp['outputschema'])

        if self.kvp['elementsetname'] is not None:
            searchresults.attrib['elementSet'] = self.kvp['elementsetname']

        if 'where' not in self.kvp['constraint'] \
        and self.kvp['resulttype'] is None:
            LOGGER.debug('Empty result set returned.')
            return node

        if self.kvp['resulttype'] == 'hits':
            return node


        if results is not None:
            if len(results) < self.kvp['maxrecords']:
                max1 = len(results)
            else:
                max1 = int(self.kvp['startposition']) + (int(self.kvp['maxrecords'])-1)
            LOGGER.debug('Presenting records %s - %s.' %
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
                        self.context.model['typenames'][typename]\
                        ['mappings']['csw:Record'], reverse=True)

                        searchresults.append(self._write_record(
                        res, self.repository.queryables['_all']))
                    elif self.kvp['outputschema'] in self.outputschemas.keys():  # use outputschema serializer
                        searchresults.append(self.outputschemas[self.kvp['outputschema']].write_record(res, self.kvp['elementsetname'], self.context, self.config.get('server', 'url')))
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
                    searchresults.append(etree.fromstring(resultset[rec].xml, self.context.parser))

        if 'responsehandler' in self.kvp:  # process the handler
            self._process_responsehandler(etree.tostring(node,
            pretty_print=self.pretty_print))
        else:
            return node

    def getrecordbyid(self, raw=False):
        ''' Handle GetRecordById request '''

        if 'id' not in self.kvp:
            return self.exceptionreport('MissingParameterValue', 'id',
            'Missing id parameter')
        if len(self.kvp['id']) < 1:
            return self.exceptionreport('InvalidParameterValue', 'id',
            'Invalid id parameter')
        if 'outputschema' not in self.kvp:
            self.kvp['outputschema'] = self.context.namespaces['csw']

        if self.requesttype == 'GET':
            self.kvp['id'] = self.kvp['id'].split(',')

        if ('outputformat' in self.kvp and
            self.kvp['outputformat'] not in
            self.context.model['operations']['GetRecordById']['parameters']
            ['outputFormat']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputformat', 'Invalid outputformat parameter %s' %
            self.kvp['outputformat'])

        if ('outputschema' in self.kvp and self.kvp['outputschema'] not in
            self.context.model['operations']['GetRecordById']['parameters']
            ['outputSchema']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputschema', 'Invalid outputschema parameter %s' %
            self.kvp['outputschema'])

        if 'elementsetname' not in self.kvp:
            self.kvp['elementsetname'] = 'summary'
        else:
            if (self.kvp['elementsetname'] not in
                self.context.model['operations']['GetRecordById']['parameters']
                ['ElementSetName']['values']):
                return self.exceptionreport('InvalidParameterValue',
                'elementsetname', 'Invalid elementsetname parameter %s' %
                self.kvp['elementsetname'])

        node = etree.Element(util.nspath_eval('csw:GetRecordByIdResponse',
        self.context.namespaces), nsmap=self.context.namespaces)

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.context.namespaces)] = '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (self.context.namespaces['csw'], self.config.get('server', 'ogc_schemas_base'))

        # query repository
        LOGGER.debug('Querying repository with ids: %s.' % self.kvp['id'][0])
        results = self.repository.query_ids(self.kvp['id'])

        if raw:  # GetRepositoryItem request
            LOGGER.debug('GetRepositoryItem request.')
            if len(results) > 0:
                return etree.fromstring(util.getqattr(results[0],
                self.context.md_core_model['mappings']['pycsw:XML']), self.context.parser)

        for result in results:
            if (util.getqattr(result,
            self.context.md_core_model['mappings']['pycsw:Typename']) == 'csw:Record'
            and self.kvp['outputschema'] ==
            'http://www.opengis.net/cat/csw/2.0.2'):
                # serialize record inline
                node.append(self._write_record(
                result, self.repository.queryables['_all']))
            elif (self.kvp['outputschema'] ==
                'http://www.opengis.net/cat/csw/2.0.2'):
                # serialize into csw:Record model
                typename = None

                for prof in self.profiles['loaded']:  # find source typename
                    if self.profiles['loaded'][prof].typename in \
                    [util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Typename'])]:
                        typename = self.profiles['loaded'][prof].typename
                        break

                if typename is not None:
                    util.transform_mappings(self.repository.queryables['_all'],
                    self.context.model['typenames'][typename]\
                    ['mappings']['csw:Record'], reverse=True)

                node.append(self._write_record(
                result, self.repository.queryables['_all']))
            elif self.kvp['outputschema'] in self.outputschemas.keys():  # use outputschema serializer
                node.append(self.outputschemas[self.kvp['outputschema']].write_record(result, self.kvp['elementsetname'], self.context, self.config.get('server', 'url')))
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

        LOGGER.debug('Transaction list: %s' % self.kvp['transactions'])

        for ttype in self.kvp['transactions']:
            if ttype['type'] == 'insert':
                try:
                    record = metadata.parse_record(self.context,
                    ttype['xml'], self.repository)[0]
                except Exception, err:
                    return self.exceptionreport('NoApplicableCode', 'insert',
                    'Transaction (insert) failed: record parsing failed: %s' \
                    % str(err))

                LOGGER.debug('Transaction operation: %s' % record)

                if not hasattr(record,
                self.context.md_core_model['mappings']['pycsw:Identifier']):
                    return self.exceptionreport('NoApplicableCode',
                    'insert', 'Record requires an identifier')

                # insert new record
                try:
                    self.repository.insert(record, 'local',
                    util.get_today_and_now())

                    inserted += 1
                    insertresults.append(
                    {'identifier': getattr(record,
                    self.context.md_core_model['mappings']['pycsw:Identifier']),
                    'title': getattr(record,
                    self.context.md_core_model['mappings']['pycsw:Title'])})
                except Exception, err:
                    return self.exceptionreport('NoApplicableCode',
                    'insert', 'Transaction (insert) failed: %s.' % str(err))

            elif ttype['type'] == 'update':
                if 'constraint' not in ttype:
                    # update full existing resource in repository
                    try:
                        record = metadata.parse_record(self.context,
                        ttype['xml'], self.repository)[0]
                        identifier = getattr(record,
                        self.context.md_core_model['mappings']['pycsw:Identifier'])
                    except Exception, err:
                        return self.exceptionreport('NoApplicableCode', 'insert',
                        'Transaction (update) failed: record parsing failed: %s' \
                        % str(err))

                    # query repository to see if record already exists
                    LOGGER.debug('checking if record exists (%s)' % \
                    identifier)

                    results = self.repository.query_ids(ids=[identifier])

                    if len(results) == 0:
                        LOGGER.debug('id %s does not exist in repository' % \
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
                        if rp['name'] not in self.repository.queryables['_all']:
                            # is it an XPath?
                            if rp['name'].find('/') != -1:
                                # scan outputschemas; if match, bind
                                for osch in self.outputschemas.values():
                                    for key, value in osch.XPATH_MAPPINGS.iteritems():
                                        if value == rp['name']:  # match
                                            rp['rp'] = {'xpath': value, 'name': key}
                                            rp['rp']['dbcol'] = self.repository.queryables['_all'][key]
                                            break
                            else:
                                return self.exceptionreport('NoApplicableCode',
                                       'update', 'Transaction (update) failed: invalid property2: %s.' % str(rp['name']))
                        else:
                            rp['rp']= \
                            self.repository.queryables['_all'][rp['name']]

                    LOGGER.debug('Record Properties: %s.' %
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

        node = etree.Element(util.nspath_eval('csw:TransactionResponse',
        self.context.namespaces), nsmap=self.context.namespaces, version='2.0.2')

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.context.namespaces)] = '%s %s/csw/2.0.2/CSW-publication.xsd' % \
        (self.context.namespaces['csw'], self.config.get('server', 'ogc_schemas_base'))

        node.append(
        self._write_transactionsummary(
        inserted=inserted, updated=updated, deleted=deleted))

        if (len(insertresults) > 0 and self.kvp['verboseresponse']):
            # show insert result identifiers
            node.append(self._write_verboseresponse(insertresults))

        return node

    def harvest(self):
        ''' Handle Harvest request '''

        try:
            self._test_manager()
        except Exception, err:
            return self.exceptionreport('NoApplicableCode', 'harvest', str(err))

        if self.requesttype == 'GET':
            if 'resourcetype' not in self.kvp:
                return self.exceptionreport('MissingParameterValue',
                'resourcetype', 'Missing resourcetype parameter')
            if 'source' not in self.kvp:
                return self.exceptionreport('MissingParameterValue',
                'source', 'Missing source parameter')

        # validate resourcetype
        if (self.kvp['resourcetype'] not in
            self.context.model['operations']['Harvest']['parameters']['ResourceType']
            ['values']):
            return self.exceptionreport('InvalidParameterValue',
            'resourcetype', 'Invalid resource type parameter: %s.\
            Allowable resourcetype values: %s' % (self.kvp['resourcetype'],
            ','.join(self.context.model['operations']['Harvest']['parameters']
            ['ResourceType']['values'])))

        if (self.kvp['resourcetype'].find('opengis.net') == -1 and
            self.kvp['resourcetype'].find('urn:geoss:waf') == -1):
            # fetch content-based resource
            LOGGER.debug('Fetching resource %s' % self.kvp['source'])
            try:
                content = util.http_request('GET', self.kvp['source'])
            except Exception, err:
                errortext = 'Error fetching resource %s.\nError: %s.' % \
                (self.kvp['source'], str(err))
                LOGGER.debug(errortext)
                return self.exceptionreport('InvalidParameterValue', 'source',
                errortext)
        else:  # it's a service URL
            content = self.kvp['source']
            # query repository to see if service already exists
            LOGGER.debug('checking if service exists (%s)' % content)
            results = self.repository.query_source(content)

            if len(results) > 0:  # exists, don't insert
                return self.exceptionreport('NoApplicableCode', 'source',
                'Insert failed: service %s already in repository' % content)

        # parse resource into record
        try:
            records_parsed = metadata.parse_record(self.context,
            content, self.repository, self.kvp['resourcetype'],
            pagesize=self.csw_harvest_pagesize)
        except Exception, err:
            return self.exceptionreport('NoApplicableCode', 'source',
            'Harvest failed: record parsing failed: %s' % str(err))

        inserted = 0
        updated = 0
        ir = []

        for record in records_parsed:
            if self.kvp['resourcetype'] == 'urn:geoss:waf':
                src = record.source
            else:
                src = self.kvp['source']

            setattr(record, self.context.md_core_model['mappings']['pycsw:Source'],
                    src)

            setattr(record, self.context.md_core_model['mappings']['pycsw:InsertDate'],
            util.get_today_and_now())

            identifier = getattr(record,
            self.context.md_core_model['mappings']['pycsw:Identifier'])
            source = getattr(record,
            self.context.md_core_model['mappings']['pycsw:Source'])
            insert_date = getattr(record,
            self.context.md_core_model['mappings']['pycsw:InsertDate'])
            title = getattr(record,
            self.context.md_core_model['mappings']['pycsw:Title'])


            ir.append({'identifier': identifier, 'title': title})

            # query repository to see if record already exists
            LOGGER.debug('checking if record exists (%s)' % identifier)
            results = self.repository.query_ids(ids=[identifier])

            LOGGER.debug(str(results))

            if len(results) == 0:  # new record, it's a new insert
                inserted += 1
                try:
                    self.repository.insert(record, source, insert_date)
                except Exception, err:
                    return self.exceptionreport('NoApplicableCode',
                    'source', 'Harvest (insert) failed: %s.' % str(err))
            else:  # existing record, it's an update
                if source != results[0].source:
                    # same identifier, but different source
                    return self.exceptionreport('NoApplicableCode',
                    'source', 'Insert failed: identifier %s in repository\
                    has source %s.' % (identifier, source))

                try:
                    self.repository.update(record)
                except Exception, err:
                    return self.exceptionreport('NoApplicableCode',
                    'source', 'Harvest (update) failed: %s.' % str(err))
                updated += 1

        node = etree.Element(util.nspath_eval('csw:HarvestResponse',
        self.context.namespaces), nsmap=self.context.namespaces)

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.context.namespaces)] = \
        '%s %s/csw/2.0.2/CSW-publication.xsd' % (self.context.namespaces['csw'],
        self.config.get('server', 'ogc_schemas_base'))

        node2 = etree.SubElement(node,
        util.nspath_eval('csw:TransactionResponse',
        self.context.namespaces), version='2.0.2')

        node2.append(
        self._write_transactionsummary(inserted=inserted, updated=updated))

        if inserted > 0:
            # show insert result identifiers
            node2.append(self._write_verboseresponse(ir))

        if 'responsehandler' in self.kvp:  # process the handler
            self._process_responsehandler(etree.tostring(node,
            pretty_print=self.pretty_print))
        else:
            return node

    def parse_postdata(self, postdata):
        ''' Parse POST XML '''

        request = {}
        try:
            LOGGER.debug('Parsing %s.' % postdata)
            doc = etree.fromstring(postdata, self.context.parser)
        except Exception, err:
            errortext = \
            'Exception: document not well-formed.\nError: %s.' % str(err)

            LOGGER.debug(errortext)
            return errortext

        # if this is a SOAP request, get to SOAP-ENV:Body/csw:*
        if (doc.tag == util.nspath_eval('soapenv:Envelope',
            self.context.namespaces)):

            LOGGER.debug('SOAP request specified.')
            self.soap = True

            doc = doc.find(
            util.nspath_eval('soapenv:Body',
            self.context.namespaces)).xpath('child::*')[0]

        if (doc.tag in [util.nspath_eval('csw:Transaction',
            self.context.namespaces), util.nspath_eval('csw:Harvest',
            self.context.namespaces)]):
            schema = os.path.join(self.config.get('server', 'home'),
            'schemas', 'ogc', 'csw', '2.0.2', 'CSW-publication.xsd')
        else:
            schema = os.path.join(self.config.get('server', 'home'),
            'schemas', 'ogc', 'csw', '2.0.2', 'CSW-discovery.xsd')

        try:
            # it is virtually impossible to validate a csw:Transaction
            # csw:Insert|csw:Update (with single child) XML document.
            # Only validate non csw:Transaction XML

            if doc.find('.//%s' % util.nspath_eval('csw:Insert',
            self.context.namespaces)) is None and \
            len(doc.xpath('//csw:Update/child::*',
            namespaces=self.context.namespaces)) == 0:

                LOGGER.debug('Validating %s.' % postdata)
                schema = etree.XMLSchema(file=schema)
                parser = etree.XMLParser(schema=schema, resolve_entities=False)
                if hasattr(self, 'soap') and self.soap:
                # validate the body of the SOAP request
                    doc = etree.fromstring(etree.tostring(doc), parser)
                else:  # validate the request normally
                    doc = etree.fromstring(postdata, parser)
                LOGGER.debug('Request is valid XML.')
            else:  # parse Transaction without validation
                doc = etree.fromstring(postdata, self.context.parser)
        except Exception, err:
            errortext = \
            'Exception: the document is not valid.\nError: %s' % str(err)
            LOGGER.debug(errortext)
            return errortext

        request['request'] = util.xmltag_split(doc.tag)
        LOGGER.debug('Request operation %s specified.' % request['request'])
        tmp = doc.find('.').attrib.get('service')
        if tmp is not None:
            request['service'] = tmp

        tmp = doc.find('.').attrib.get('version')
        if tmp is not None:
            request['version'] = tmp

        tmp = doc.find('.//%s' % util.nspath_eval('ows:Version',
        self.context.namespaces))

        if tmp is not None:
            request['version'] = tmp.text

        tmp = doc.find('.').attrib.get('updateSequence')
        if tmp is not None:
            request['updatesequence'] = tmp

        # GetCapabilities
        if request['request'] == 'GetCapabilities':
            tmp = doc.find(util.nspath_eval('ows:Sections',
                  self.context.namespaces))
            if tmp is not None:
                request['sections'] = ','.join([section.text for section in \
                doc.findall(util.nspath_eval('ows:Sections/ows:Section',
                self.context.namespaces))])

        # DescribeRecord
        if request['request'] == 'DescribeRecord':
            request['typename'] = [typename.text for typename in \
            doc.findall(util.nspath_eval('csw:TypeName',
            self.context.namespaces))]

            tmp = doc.find('.').attrib.get('schemaLanguage')
            if tmp is not None:
                request['schemalanguage'] = tmp

            tmp = doc.find('.').attrib.get('outputFormat')
            if tmp is not None:
                request['outputformat'] = tmp

        # GetDomain
        if request['request'] == 'GetDomain':
            tmp = doc.find(util.nspath_eval('csw:ParameterName',
                  self.context.namespaces))
            if tmp is not None:
                request['parametername'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw:PropertyName',
                  self.context.namespaces))
            if tmp is not None:
                request['propertyname'] = tmp.text

        # GetRecords
        if request['request'] == 'GetRecords':
            tmp = doc.find('.').attrib.get('outputSchema')
            request['outputschema'] = tmp if tmp is not None \
            else self.context.namespaces['csw']

            tmp = doc.find('.').attrib.get('resultType')
            request['resulttype'] = tmp if tmp is not None else None

            tmp = doc.find('.').attrib.get('outputFormat')
            request['outputformat'] = tmp if tmp is not None \
            else 'application/xml'

            tmp = doc.find('.').attrib.get('startPosition')
            request['startposition'] = tmp if tmp is not None else 1

            tmp = doc.find('.').attrib.get('requestId')
            request['requestid'] = tmp if tmp is not None else None

            tmp = doc.find('.').attrib.get('maxRecords')
            if tmp is not None:
                request['maxrecords'] = tmp

            tmp = doc.find(util.nspath_eval('csw:DistributedSearch',
                  self.context.namespaces))
            if tmp is not None:
                request['distributedsearch'] = True
                hopcount = tmp.attrib.get('hopCount')
                request['hopcount'] = int(hopcount)-1 if hopcount is not None \
                else 1
            else:
                request['distributedsearch'] = False

            tmp = doc.find(util.nspath_eval('csw:ResponseHandler',
                  self.context.namespaces))
            if tmp is not None:
                request['responsehandler'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw:Query/csw:ElementSetName',
                  self.context.namespaces))
            request['elementsetname'] = tmp.text if tmp is not None else None

            tmp = doc.find(util.nspath_eval(
            'csw:Query', self.context.namespaces)).attrib.get('typeNames')
            request['typenames'] = tmp.split() if tmp is not None \
            else 'csw:Record'

            request['elementname'] = [elname.text for elname in \
            doc.findall(util.nspath_eval('csw:Query/csw:ElementName',
            self.context.namespaces))]

            request['constraint'] = {}
            tmp = doc.find(util.nspath_eval('csw:Query/csw:Constraint',
            self.context.namespaces))

            if tmp is not None:
                request['constraint'] = self._parse_constraint(tmp)
                if isinstance(request['constraint'], str):  # parse error
                    return 'Invalid Constraint: %s' % request['constraint']
            else:
                LOGGER.debug('No csw:Constraint (ogc:Filter or csw:CqlText) \
                specified.')

            tmp = doc.find(util.nspath_eval('csw:Query/ogc:SortBy',
                  self.context.namespaces))
            if tmp is not None:
                LOGGER.debug('Sorted query specified.')
                request['sortby'] = {}


                try:
                    elname = tmp.find(util.nspath_eval(
                    'ogc:SortProperty/ogc:PropertyName',
                    self.context.namespaces)).text

                    request['sortby']['propertyname'] = \
                    self.repository.queryables['_all'][elname]['dbcol']

                    if (elname.find('BoundingBox') != -1 or
                        elname.find('Envelope') != -1):
                        # it's a spatial sort
                        request['sortby']['spatial'] = True
                except Exception, err:
                    errortext = \
                    'Invalid ogc:SortProperty/ogc:PropertyName: %s' % str(err)
                    LOGGER.debug(errortext)
                    return errortext

                tmp2 =  tmp.find(util.nspath_eval(
                'ogc:SortProperty/ogc:SortOrder', self.context.namespaces))
                request['sortby']['order'] = tmp2.text if tmp2 is not None \
                else 'ASC'
            else:
                request['sortby'] = None

        # GetRecordById
        if request['request'] == 'GetRecordById':
            request['id'] = [id1.text for id1 in \
            doc.findall(util.nspath_eval('csw:Id', self.context.namespaces))]

            tmp = doc.find(util.nspath_eval('csw:ElementSetName',
                  self.context.namespaces))
            request['elementsetname'] = tmp.text if tmp is not None \
            else 'summary'

            tmp = doc.find('.').attrib.get('outputSchema')
            request['outputschema'] = tmp if tmp is not None \
            else self.context.namespaces['csw']

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

            tmp = doc.find('.').attrib.get('requestId')
            request['requestid'] = tmp if tmp is not None else None

            request['transactions'] = []

            for ttype in \
            doc.xpath('//csw:Insert', namespaces=self.context.namespaces):
                tname = ttype.attrib.get('typeName')

                for mdrec in ttype.xpath('child::*'):
                    xml = mdrec
                    request['transactions'].append(
                    {'type': 'insert', 'typename': tname, 'xml': xml})

            for ttype in \
            doc.xpath('//csw:Update', namespaces=self.context.namespaces):
                child = ttype.xpath('child::*')
                update = {'type': 'update'}

                if len(child) == 1:  # it's a wholesale update
                    update['xml'] = child[0]
                else:  # it's a RecordProperty with Constraint Update
                    update['recordproperty'] = []

                    for recprop in ttype.findall(
                    util.nspath_eval('csw:RecordProperty',
                        self.context.namespaces)):
                        rpname = recprop.find(util.nspath_eval('csw:Name',
                        self.context.namespaces)).text
                        rpvalue = recprop.find(
                        util.nspath_eval('csw:Value',
                        self.context.namespaces)).text

                        update['recordproperty'].append(
                        {'name': rpname, 'value': rpvalue})

                    update['constraint'] = self._parse_constraint(
                    ttype.find(util.nspath_eval('csw:Constraint',
                    self.context.namespaces)))

                request['transactions'].append(update)

            for ttype in \
            doc.xpath('//csw:Delete', namespaces=self.context.namespaces):
                tname = ttype.attrib.get('typeName')
                constraint = self._parse_constraint(
                ttype.find(util.nspath_eval('csw:Constraint',
                self.context.namespaces)))

                if isinstance(constraint, str):  # parse error
                    return 'Invalid Constraint: %s' % constraint

                request['transactions'].append(
                {'type': 'delete', 'typename': tname, 'constraint': constraint})

        # Harvest
        if request['request'] == 'Harvest':
            request['source'] = doc.find(util.nspath_eval('csw:Source',
            self.context.namespaces)).text

            request['resourcetype'] = \
            doc.find(util.nspath_eval('csw:ResourceType',
            self.context.namespaces)).text

            tmp = doc.find(util.nspath_eval('csw:ResourceFormat',
                  self.context.namespaces))
            if tmp is not None:
                request['resourceformat'] = tmp.text
            else:
                request['resourceformat'] = 'application/xml'

            tmp = doc.find(util.nspath_eval('csw:HarvestInterval',
                  self.context.namespaces))
            if tmp is not None:
                request['harvestinterval'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw:ResponseHandler',
                  self.context.namespaces))
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

        record = etree.Element(util.nspath_eval('csw:%s' % elname,
                 self.context.namespaces))

        if ('elementname' in self.kvp and
            len(self.kvp['elementname']) > 0):
            for elemname in self.kvp['elementname']:
                if (elemname.find('BoundingBox') != -1 or
                    elemname.find('Envelope') != -1):
                    bboxel = write_boundingbox(util.getqattr(recobj,
                    self.context.md_core_model['mappings']['pycsw:BoundingBox']),
                    self.context.namespaces)
                    if bboxel is not None:
                        record.append(bboxel)
                else:
                    value = util.getqattr(recobj, queryables[elemname]['dbcol'])
                    if value:
                        etree.SubElement(record,
                        util.nspath_eval(elemname,
                        self.context.namespaces)).text = value
        elif 'elementsetname' in self.kvp:
            if (self.kvp['elementsetname'] == 'full' and
            util.getqattr(recobj, self.context.md_core_model['mappings']\
            ['pycsw:Typename']) == 'csw:Record' and
            util.getqattr(recobj, self.context.md_core_model['mappings']\
            ['pycsw:Schema']) == 'http://www.opengis.net/cat/csw/2.0.2' and
            util.getqattr(recobj, self.context.md_core_model['mappings']\
            ['pycsw:Type']) != 'service'):
                # dump record as is and exit
                return etree.fromstring(util.getqattr(recobj,
                self.context.md_core_model['mappings']['pycsw:XML']), self.context.parser)

            etree.SubElement(record,
            util.nspath_eval('dc:identifier', self.context.namespaces)).text = \
            util.getqattr(recobj,
            self.context.md_core_model['mappings']['pycsw:Identifier'])

            for i in ['dc:title', 'dc:type']:
                val = util.getqattr(recobj, queryables[i]['dbcol'])
                if not val:
                    val = ''
                etree.SubElement(record, util.nspath_eval(i,
                self.context.namespaces)).text = val

            if self.kvp['elementsetname'] in ['summary', 'full']:
                # add summary elements
                keywords = util.getqattr(recobj, queryables['dc:subject']['dbcol'])
                if keywords is not None:
                    for keyword in keywords.split(','):
                        etree.SubElement(record,
                        util.nspath_eval('dc:subject',
                        self.context.namespaces)).text = keyword

                val = util.getqattr(recobj, queryables['dc:format']['dbcol'])
                if val:
                    etree.SubElement(record,
                    util.nspath_eval('dc:format',
                    self.context.namespaces)).text = val

                # links
                rlinks = util.getqattr(recobj,
                self.context.md_core_model['mappings']['pycsw:Links'])

                if rlinks:
                    links = rlinks.split('^')
                    for link in links:
                        linkset = link.split(',')
                        etree.SubElement(record,
                        util.nspath_eval('dct:references',
                        self.context.namespaces),
                        scheme=linkset[2]).text = linkset[-1]

                for i in ['dc:relation', 'dct:modified', 'dct:abstract']:
                    val = util.getqattr(recobj, queryables[i]['dbcol'])
                    if val is not None:
                        etree.SubElement(record,
                        util.nspath_eval(i, self.context.namespaces)).text = val

            if self.kvp['elementsetname'] == 'full':  # add full elements
                for i in ['dc:date', 'dc:creator', \
                'dc:publisher', 'dc:contributor', 'dc:source', \
                'dc:language', 'dc:rights']:
                    val = util.getqattr(recobj, queryables[i]['dbcol'])
                    if val:
                        etree.SubElement(record,
                        util.nspath_eval(i, self.context.namespaces)).text = val

            # always write out ows:BoundingBox
            bboxel = write_boundingbox(getattr(recobj,
            self.context.md_core_model['mappings']['pycsw:BoundingBox']),
            self.context.namespaces)

            if bboxel is not None:
                record.append(bboxel)
        return record

    def _write_response(self):
        ''' Generate response '''
        # set HTTP response headers and XML declaration

        xmldecl=''
        appinfo=''

        LOGGER.debug('Writing response.')

        if hasattr(self, 'soap') and self.soap:
            self._gen_soap_wrapper()

        if (isinstance(self.kvp, dict) and 'outputformat' in self.kvp and
            self.kvp['outputformat'] == 'application/json'):
            self.contenttype = self.kvp['outputformat']
            from pycsw.formats import fmt_json
            response = fmt_json.exml2json(self.response,
            self.context.namespaces, self.pretty_print)
        else:  # it's XML
            self.contenttype = self.mimetype
            response = etree.tostring(self.response,
            pretty_print=self.pretty_print)
            xmldecl = '<?xml version="1.0" encoding="%s" standalone="no"?>\n' \
            % self.encoding
            appinfo = '<!-- pycsw %s -->\n' % self.context.version

        LOGGER.debug('Response:\n%s' % response)

        s = '%s%s%s' % (xmldecl, appinfo, response)
        return s.encode()


    def _gen_soap_wrapper(self):
        ''' Generate SOAP wrapper '''
        LOGGER.debug('Writing SOAP wrapper.')
        node = etree.Element(util.nspath_eval('soapenv:Envelope',
        self.context.namespaces), nsmap=self.context.namespaces)

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.context.namespaces)] = '%s %s' % \
        (self.context.namespaces['soapenv'], self.context.namespaces['soapenv'])

        node2 = etree.SubElement(node, util.nspath_eval('soapenv:Body',
        self.context.namespaces))

        if hasattr(self, 'exception') and self.exception:
            node3 = etree.SubElement(node2, util.nspath_eval('soapenv:Fault',
                    self.context.namespaces))
            node4 = etree.SubElement(node3, util.nspath_eval('soapenv:Code',
                    self.context.namespaces))

            etree.SubElement(node4, util.nspath_eval('soapenv:Value',
            self.context.namespaces)).text = 'soap:Server'

            node4 = etree.SubElement(node3, util.nspath_eval('soapenv:Reason',
                    self.context.namespaces))

            etree.SubElement(node4, util.nspath_eval('soapenv:Text',
            self.context.namespaces)).text = 'A server exception was encountered.'

            node4 = etree.SubElement(node3, util.nspath_eval('soapenv:Detail',
                    self.context.namespaces))
            node4.append(self.response)
        else:
            node2.append(self.response)

        self.response = node

    def _gen_manager(self):
        ''' Update self.context.model with CSW-T advertising '''
        if (self.config.has_option('manager', 'transactions') and
            self.config.get('manager', 'transactions') == 'true'):
            self.context.model['operations']['Transaction'] = \
            {'methods': {'get': False, 'post': True}, 'parameters': {}}

            self.context.model['operations']['Harvest'] = \
            {'methods': {'get': False, 'post': True}, 'parameters': \
            {'ResourceType': {'values': \
            ['http://www.opengis.net/cat/csw/2.0.2',
             'http://www.opengis.net/wms',
             'http://www.opengis.net/wfs',
             'http://www.opengis.net/wcs',
             'http://www.opengis.net/wps/1.0.0',
             'http://www.opengis.net/sos/1.0',
             'http://www.opengis.net/sos/2.0',
             'http://www.isotc211.org/2005/gmi',
             'urn:geoss:waf',
            ]}}}

            self.csw_harvest_pagesize = 10
            if self.config.has_option('manager', 'csw_harvest_pagesize'):
                self.csw_harvest_pagesize = int(self.config.get('manager',
                'csw_harvest_pagesize'))

    def _parse_constraint(self, element):
        ''' Parse csw:Constraint '''

        query = {}

        tmp = element.find(util.nspath_eval('ogc:Filter', self.context.namespaces))
        if tmp is not None:
            LOGGER.debug('Filter constraint specified.')
            try:
                query['type'] = 'filter'
                query['where'], query['values'] = fes.parse(tmp,
                self.repository.queryables['_all'], self.repository.dbtype,
                self.context.namespaces, self.orm, self.language['text'], self.repository.fts)
            except Exception, err:
                return 'Invalid Filter request: %s' % err

        tmp = element.find(util.nspath_eval('csw:CqlText', self.context.namespaces))
        if tmp is not None:
            LOGGER.debug('CQL specified: %s.' % tmp.text)
            try:
                LOGGER.debug('Transforming CQL into OGC Filter')
                query['type'] = 'filter'
                cql = cql2fes1(tmp.text, self.context.namespaces)
                query['where'], query['values'] = fes.parse(cql,
                self.repository.queryables['_all'], self.repository.dbtype,
                self.context.namespaces, self.orm, self.language['text'], self.repository.fts)
            except Exception as err:
                LOGGER.error('Invalid CQL request: %s', tmp.text)
                LOGGER.error('Error message: %s', err, exc_info=True)
                return 'Invalid CQL request'
        return query

    def _test_manager(self):
        ''' Verify that transactions are allowed '''

        if self.config.get('manager', 'transactions') != 'true':
            raise RuntimeError('CSW-T interface is disabled')

        ipaddress = self.environ['REMOTE_ADDR']

        if not self.config.has_option('manager', 'allowed_ips') or \
        (self.config.has_option('manager', 'allowed_ips') and not 
         util.ipaddress_in_whitelist(ipaddress,
                        self.config.get('manager', 'allowed_ips').split(','))):
            raise RuntimeError(
            'CSW-T operations not allowed for this IP address: %s' % ipaddress)

    def _cql_update_queryables_mappings(self, cql, mappings):
        ''' Transform CQL query's properties to underlying DB columns '''
        LOGGER.debug('Raw CQL text = %s.' % cql)
        LOGGER.debug(str(mappings.keys()))
        if cql is not None:
            for key in mappings.keys():
                try:
                    cql = cql.replace(key, mappings[key]['dbcol'])
                except:
                    cql = cql.replace(key, mappings[key])
            LOGGER.debug('Interpolated CQL text = %s.' % cql)
            return cql

    def _write_transactionsummary(self, inserted=0, updated=0, deleted=0):
        ''' Write csw:TransactionSummary construct '''
        node = etree.Element(util.nspath_eval('csw:TransactionSummary',
               self.context.namespaces))

        if 'requestid' in self.kvp and self.kvp['requestid'] is not None:
            node.attrib['requestId'] = self.kvp['requestid']

        etree.SubElement(node, util.nspath_eval('csw:totalInserted',
        self.context.namespaces)).text = str(inserted)

        etree.SubElement(node, util.nspath_eval('csw:totalUpdated',
        self.context.namespaces)).text = str(updated)

        etree.SubElement(node, util.nspath_eval('csw:totalDeleted',
        self.context.namespaces)).text = str(deleted)

        return node

    def _write_acknowledgement(self, root=True):
        ''' Generate csw:Acknowledgement '''
        node = etree.Element(util.nspath_eval('csw:Acknowledgement',
               self.context.namespaces),
        nsmap = self.context.namespaces, timeStamp=util.get_today_and_now())

        if root:
            node.attrib[util.nspath_eval('xsi:schemaLocation',
            self.context.namespaces)] = \
            '%s %s/csw/2.0.2/CSW-discovery.xsd' % (self.context.namespaces['csw'], \
            self.config.get('server', 'ogc_schemas_base'))

        node1 = etree.SubElement(node, util.nspath_eval('csw:EchoedRequest',
                self.context.namespaces))
        if self.requesttype == 'POST':
            node1.append(etree.fromstring(self.request, self.context.parser))
        else:  # GET
            node2 = etree.SubElement(node1, util.nspath_eval('ows:Get',
                    self.context.namespaces))

            node2.text = self.request

        if self.async:
            etree.SubElement(node, util.nspath_eval('csw:RequestId',
            self.context.namespaces)).text = self.kvp['requestid']

        return node

    def _process_responsehandler(self, xml):
        ''' Process response handler '''

        if self.kvp['responsehandler'] is not None:
            LOGGER.debug('Processing responsehandler %s.' %
            self.kvp['responsehandler'])

            uprh = urlparse.urlparse(self.kvp['responsehandler'])

            if uprh.scheme == 'mailto':  # email
                import smtplib

                LOGGER.debug('Email detected.')

                smtp_host = 'localhost'
                if self.config.has_option('server', 'smtp_host'):
                    smtp_host = self.config.get('server', 'smtp_host')

                body = 'Subject: pycsw %s results\n\n%s' % \
                (self.kvp['request'], xml)

                try:
                    LOGGER.debug('Sending email.')
                    msg = smtplib.SMTP(smtp_host)
                    msg.sendmail(
                    self.config.get('metadata:main', 'contact_email'),
                    uprh.path, body)
                    msg.quit()
                    LOGGER.debug('Email sent successfully.')
                except Exception, err:
                    LOGGER.debug('Error processing email: %s.' % str(err))

            elif uprh.scheme == 'ftp':
                import ftplib

                LOGGER.debug('FTP detected.')

                try:
                    LOGGER.debug('Sending to FTP server.')
                    ftp = ftplib.FTP(uprh.hostname)
                    if uprh.username is not None:
                        ftp.login(uprh.username, uprh.password)
                    ftp.storbinary('STOR %s' % uprh.path[1:], StringIO(xml))
                    ftp.quit()
                    LOGGER.debug('FTP sent successfully.')
                except Exception, err:
                    LOGGER.debug('Error processing FTP: %s.' % str(err))

    def _write_verboseresponse(self, insertresults):
        ''' show insert result identifiers '''
        insertresult = etree.Element(util.nspath_eval('csw:InsertResult',
        self.context.namespaces))
        for ir in insertresults:
            briefrec = etree.SubElement(insertresult,
                       util.nspath_eval('csw:BriefRecord',
                       self.context.namespaces))

            etree.SubElement(briefrec,
            util.nspath_eval('dc:identifier',
            self.context.namespaces)).text = ir['identifier']

            etree.SubElement(briefrec,
            util.nspath_eval('dc:title',
            self.context.namespaces)).text = ir['title']

        return insertresult

def write_boundingbox(bbox, nsmap):
    ''' Generate ows:BoundingBox '''

    if bbox is not None:
        try:
            bbox2 = util.wkt2geom(bbox)
        except:
            return None

        if len(bbox2) == 4:
            boundingbox = etree.Element(util.nspath_eval('ows:BoundingBox',
            nsmap), crs='urn:x-ogc:def:crs:EPSG:6.11:4326',
            dimensions='2')

            etree.SubElement(boundingbox, util.nspath_eval('ows:LowerCorner',
            nsmap)).text = '%s %s' % (bbox2[1], bbox2[0])

            etree.SubElement(boundingbox, util.nspath_eval('ows:UpperCorner',
            nsmap)).text = '%s %s' % (bbox2[3], bbox2[2])

            return boundingbox
        else:
            return None
    else:
        return None
