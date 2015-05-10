# -*- coding: iso-8859-15 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
# Copyright (c) 2015 Angelos Tzotsos
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
from pycsw import oaipmh, opensearch, sru
from pycsw.plugins.profiles import profile as pprofile
import pycsw.plugins.outputschemas
from pycsw.core import config, log, metadata, util
from pycsw.ogc.fes import fes1
from pycsw.ogc.csw import csw2
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
        self.oaipmhobj = None

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

        # define CSW implementation object (default CSW2)
        self.iface = csw2.Csw2(server_csw=self)
        # self.iface = None
        # if version:
        #     self.iface = Csw2(server_csw=self)
        
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
        except Exception as err:
            self.response = self.exceptionreport(
            'NoApplicableCode', 'service',
            'Error opening configuration %s' % rtconfig)
            return

        # set server.home safely
        # TODO: make this more abstract
        self.config.set('server', 'home', os.path.dirname(
        os.path.join(os.path.dirname(__file__), '..')))

        self.context.pycsw_home = self.config.get('server', 'home')
        self.context.url = self.config.get('server', 'url')

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

        LOGGER.debug('Setting MaxRecordDefault')
        if self.config.has_option('server', 'maxrecords'):
            self.context.model['constraints']['MaxRecordDefault']['values'] = \
            [self.config.get('server', 'maxrecords')]

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
            except Exception as err:
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
                geonode_.GeoNodeRepository(self.context)
                LOGGER.debug('GeoNode repository loaded (geonode): %s.' % \
                self.repository.dbtype)
            except Exception as err:
                self.response = self.exceptionreport(
                'NoApplicableCode', 'service',
                'Could not load repository (geonode): %s' % str(err))

        elif (self.config.has_option('repository', 'source') and
            self.config.get('repository', 'source') == 'odc'):

            # load odc repository
            from pycsw.plugins.repository.odc import odc

            try:
                self.repository = \
                odc.OpenDataCatalogRepository(self.context)
                LOGGER.debug('OpenDataCatalog repository loaded (geonode): %s.' % \
                self.repository.dbtype)
            except Exception as err:
                self.response = self.exceptionreport(
                'NoApplicableCode', 'service',
                'Could not load repository (odc): %s' % str(err))

        else:  # load default repository
            self.orm = 'sqlalchemy'
            from pycsw.core import repository
            try:
                self.repository = \
                repository.Repository(self.config.get('repository', 'database'),
                self.context, self.environ.get('local.app_root', None),
                self.config.get('repository', 'table'), repo_filter)
                LOGGER.debug('Repository loaded (local): %s.' \
                % self.repository.dbtype)
            except Exception as err:
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

    def oaipmh(self):
        ''' enable OAI-PMH '''
        if not self.oaipmhobj:
            self.oaipmhobj = oaipmh.OAIPMH(self.context, self.config)
        return self.oaipmhobj

    def dispatch(self, writer=sys.stdout, write_headers=True):
        ''' Handle incoming HTTP request '''

        # if ('version' in self.kvp):
        #     if (util.get_version_integer(self.kvp['version']) == util.get_version_integer('2.0.2')):
        #         self.iface = Csw2(server_csw=self)
        #     else:
        #         pass
        # else: # TODO: initialize CSW3 here if no version is present in kvp
        #     pass
        
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

        if (not isinstance(self.kvp, str) and
        'mode' in self.kvp and self.kvp['mode'] == 'oaipmh'):
            self.mode = 'oaipmh'
            LOGGER.debug('OAI-PMH mode detected; processing request.')
            self.oaiargs =  dict((k, v) for k, v in self.kvp.items() if k)
            self.kvp = self.oaipmh().request(self.kvp)

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
                self.response = self.iface.getcapabilities()
            elif self.kvp['request'] == 'DescribeRecord':
                self.response = self.iface.describerecord()
            elif self.kvp['request'] == 'GetDomain':
                self.response = self.iface.getdomain()
            elif self.kvp['request'] == 'GetRecords':
                if self.async:  # process asynchronously
                    threading.Thread(target=self.iface.getrecords).start()
                    self.response = self._write_acknowledgement()
                else:
                    self.response = self.iface.getrecords()
            elif self.kvp['request'] == 'GetRecordById':
                self.response = self.iface.getrecordbyid()
            elif self.kvp['request'] == 'GetRepositoryItem':
                self.response = self.iface.getrepositoryitem()
            elif self.kvp['request'] == 'Transaction':
                self.response = self.iface.transaction()
            elif self.kvp['request'] == 'Harvest':
                if self.async:  # process asynchronously
                    threading.Thread(target=self.iface.harvest).start()
                    self.response = self._write_acknowledgement()
                else:
                    self.response = self.iface.harvest()
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

        elif self.mode == 'oaipmh':
            LOGGER.debug('OAI-PMH mode detected; processing response.')
            self.response = self.oaipmh().response(self.response,
                            self.oaiargs, self.repository, self.config.get('server', 'url'))

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
        return iface.getcapabilities

    def describerecord(self):
        ''' Handle DescribeRecord request '''
        return iface.describerecord

    def getdomain(self):
        ''' Handle GetDomain request '''
        return iface.getdomain

    def getrecords(self):
        ''' Handle GetRecords request '''
        return iface.getrecords

    def getrecordbyid(self, raw=False):
        ''' Handle GetRecordById request '''
        return iface.getrecordbyid

    def getrepositoryitem(self):
        ''' Handle GetRepositoryItem request '''
        return iface.getrepositoryitem

    def transaction(self):
        ''' Handle Transaction request '''
        return iface.transaction

    def harvest(self):
        ''' Handle Harvest request '''
        return iface.harvest

    def parse_postdata(self, postdata):
        ''' Parse POST XML '''

        request = {}
        try:
            LOGGER.debug('Parsing %s.' % postdata)
            doc = etree.fromstring(postdata)
        except Exception as err:
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
            'core', 'schemas', 'ogc', 'csw', '2.0.2', 'CSW-publication.xsd')
        else:
            schema = os.path.join(self.config.get('server', 'home'),
            'core', 'schemas', 'ogc', 'csw', '2.0.2', 'CSW-discovery.xsd')

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
                parser = etree.XMLParser(schema=schema)
                if hasattr(self, 'soap') and self.soap:
                # validate the body of the SOAP request
                    doc = etree.fromstring(etree.tostring(doc), parser)
                else:  # validate the request normally
                    doc = etree.fromstring(postdata, parser)
                LOGGER.debug('Request is valid XML.')
            else:  # parse Transaction without validation
                doc = etree.fromstring(postdata)
        except Exception as err:
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
                except Exception as err:
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
                    bboxel = util.write_boundingbox(util.getqattr(recobj,
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
                self.context.md_core_model['mappings']['pycsw:XML']))

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
            bboxel = util.write_boundingbox(getattr(recobj,
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
            from pycsw.core.formats import fmt_json
            response = fmt_json.exml2json(self.response,
            self.context.namespaces, self.pretty_print)
        else:  # it's XML
            self.contenttype = self.mimetype
            response = etree.tostring(self.response,
            pretty_print=self.pretty_print, encoding='unicode')
            xmldecl = '<?xml version="1.0" encoding="%s" standalone="no"?>\n' \
            % self.encoding
            appinfo = '<!-- pycsw %s -->\n' % self.context.version

        s = (u'%s%s%s' % (xmldecl, appinfo, response)).encode(self.encoding)
        LOGGER.debug('Response:\n%s', s)
        return s


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
                query['where'], query['values'] = fes1.parse(tmp,
                self.repository.queryables['_all'], self.repository.dbtype,
                self.context.namespaces, self.orm, self.language['text'], self.repository.fts)
            except Exception as err:
                return 'Invalid Filter request: %s' % err
        tmp = element.find(util.nspath_eval('csw:CqlText', self.context.namespaces))
        if tmp is not None:
            LOGGER.debug('CQL specified: %s.' % tmp.text)
            query['type'] = 'cql'
            query['where'] = self._cql_update_queryables_mappings(tmp.text,
            self.repository.queryables['_all'])
            query['values'] = {}
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
            node1.append(etree.fromstring(self.request))
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
                except Exception as err:
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
                except Exception as err:
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
