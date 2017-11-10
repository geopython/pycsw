# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2016 Tom Kralidis
# Copyright (c) 2015 Angelos Tzotsos
# Copyright (c) 2016 James Dickens
# Copyright (c) 2016 Ricardo Silva
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

import logging
import os
from six.moves.urllib.parse import parse_qsl
from six.moves.urllib.parse import splitquery
from six.moves.urllib.parse import urlparse
from six import StringIO
from six.moves.configparser import SafeConfigParser
import sys
from time import time
import wsgiref.util

from pycsw.core.etree import etree
from pycsw import oaipmh, opensearch, sru
from pycsw.plugins.profiles import profile as pprofile
import pycsw.plugins.outputschemas
from pycsw.core import config, log, util
from pycsw.ogc.csw import csw2, csw3

LOGGER = logging.getLogger(__name__)


class Csw(object):
    """ Base CSW server """
    def __init__(self, rtconfig=None, env=None, version='3.0.0'):
        """ Initialize CSW """

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
        self.status = 'OK'
        self.profiles = None
        self.manager = False
        self.outputschemas = {}
        self.mimetype = 'application/xml; charset=UTF-8'
        self.encoding = 'UTF-8'
        self.pretty_print = 0
        self.domainquerytype = 'list'
        self.orm = 'django'
        self.language = {'639_code': 'en', 'text': 'english'}
        self.process_time_start = time()

        # define CSW implementation object (default CSW3)
        self.iface = csw3.Csw3(server_csw=self)
        self.request_version = version

        if self.request_version == '2.0.2':
            self.iface = csw2.Csw2(server_csw=self)
            self.context.set_model('csw')

        # load user configuration
        try:
            LOGGER.info('Loading user configuration')
            if isinstance(rtconfig, SafeConfigParser):  # serialized already
                self.config = rtconfig
            else:
                self.config = SafeConfigParser()
                if isinstance(rtconfig, dict):  # dictionary
                    for section, options in rtconfig.items():
                        self.config.add_section(section)
                        for k, v in options.items():
                            self.config.set(section, k, v)
                else:  # configuration file
                    import codecs
                    with codecs.open(rtconfig, encoding='utf-8') as scp:
                        self.config.readfp(scp)
        except Exception as err:
            msg = 'Could not load configuration'
            LOGGER.exception('%s %s: %s', msg, rtconfig, err)
            self.response = self.iface.exceptionreport(
                'NoApplicableCode', 'service', msg)
            return

        # set server.home safely
        # TODO: make this more abstract
        self.config.set(
            'server', 'home',
            os.path.dirname(os.path.join(os.path.dirname(__file__), '..'))
        )

        self.context.pycsw_home = self.config.get('server', 'home')
        self.context.url = self.config.get('server', 'url')

        log.setup_logger(self.config)

        LOGGER.info('running configuration %s', rtconfig)
        LOGGER.debug('QUERY_STRING: %s', self.environ['QUERY_STRING'])

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
        if self.config.has_option('server', 'language'):
            try:
                LOGGER.info('Setting language')
                lang_code = self.config.get('server', 'language').split('-')[0]
                self.language['639_code'] = lang_code
                self.language['text'] = self.context.languages[lang_code]
            except Exception as err:
                LOGGER.exception('Could not set language: %s', err)
                pass

        LOGGER.debug('Configuration: %s.', self.config)
        LOGGER.debug('Model: %s.', self.context.model)

        # load user-defined mappings if they exist
        if self.config.has_option('repository', 'mappings'):
            # override default repository mappings
            try:
                import imp
                module = self.config.get('repository', 'mappings')
                if '/' in module:  # filepath
                    modulename = '%s' % os.path.splitext(module)[0].replace(
                        os.sep, '.')
                    mappings = imp.load_source(modulename, module)
                else:  # dotted name
                    mappings = __import__(module, fromlist=[''])
                LOGGER.info('Loading custom repository mappings '
                             'from %s', module)
                self.context.md_core_model = mappings.MD_CORE_MODEL
                self.context.refresh_dc(mappings.MD_CORE_MODEL)
            except Exception as err:
                LOGGER.exception('Could not load custom mappings: %s', err)
                self.response = self.iface.exceptionreport(
                    'NoApplicableCode', 'service',
                    'Could not load repository.mappings')

        # load outputschemas
        LOGGER.info('Loading outputschemas')

        for osch in pycsw.plugins.outputschemas.__all__:
            output_schema_module = __import__(
                'pycsw.plugins.outputschemas.%s' % osch)
            mod = getattr(output_schema_module.plugins.outputschemas, osch)
            self.outputschemas[mod.NAMESPACE] = mod

        LOGGER.debug('Outputschemas loaded: %s.', self.outputschemas)
        LOGGER.debug('Namespaces: %s', self.context.namespaces)

    def expand_path(self, path):
        """ return safe path for WSGI environments """
        if 'local.app_root' in self.environ and not os.path.isabs(path):
            return os.path.join(self.environ['local.app_root'], path)
        else:
            return path

    def dispatch_wsgi(self):
        """ WSGI handler """

        if hasattr(self, 'response'):
            return self._write_response()

        LOGGER.debug('WSGI mode detected')

        if self.environ['REQUEST_METHOD'] == 'POST':
            try:
                request_body_size = int(self.environ.get('CONTENT_LENGTH', 0))
            except (ValueError):
                request_body_size = 0

            self.requesttype = 'POST'
            self.request = self.environ['wsgi.input'].read(request_body_size)
            LOGGER.debug('Request type: POST.  Request:\n%s\n', self.request)

        else:  # it's a GET request
            self.requesttype = 'GET'
            self.request = wsgiref.util.request_uri(self.environ)
            try:
                query_part = splitquery(self.request)[-1]
                self.kvp = dict(parse_qsl(query_part, keep_blank_values=True))
            except AttributeError as err:
                LOGGER.exception('Could not parse query string')
                self.kvp = {}
            LOGGER.debug('Request type: GET.  Request:\n%s\n', self.request)
        return self.dispatch()

    def opensearch(self):
        """ enable OpenSearch """
        if not self.opensearchobj:
            self.opensearchobj = opensearch.OpenSearch(self.context)

        return self.opensearchobj

    def sru(self):
        """ enable SRU """
        if not self.sruobj:
            self.sruobj = sru.Sru(self.context)

        return self.sruobj

    def oaipmh(self):
        """ enable OAI-PMH """
        if not self.oaipmhobj:
            self.oaipmhobj = oaipmh.OAIPMH(self.context, self.config)
        return self.oaipmhobj

    def dispatch(self, writer=sys.stdout, write_headers=True):
        """ Handle incoming HTTP request """

        error = 0
        if self.requesttype == 'GET':
            self.kvp = self.normalize_kvp(self.kvp)
            version_202 = ('version' in self.kvp and
                           self.kvp['version'] == '2.0.2')
            accept_version_202 = ('acceptversions' in self.kvp and
                                  '2.0.2' in self.kvp['acceptversions'])
            if version_202 or accept_version_202:
                self.request_version = '2.0.2'
        elif self.requesttype == 'POST':
            if self.request.find(b'cat/csw/2.0.2') != -1:
                self.request_version = '2.0.2'
            elif self.request.find(b'cat/csw/3.0') != -1:
                self.request_version = '3.0.0'

        if (not isinstance(self.kvp, str) and 'mode' in self.kvp and
                self.kvp['mode'] == 'sru'):
            self.mode = 'sru'
            self.request_version = '2.0.2'
            LOGGER.info('SRU mode detected; processing request')
            self.kvp = self.sru().request_sru2csw(self.kvp)

        if (not isinstance(self.kvp, str) and 'mode' in self.kvp and
                self.kvp['mode'] == 'oaipmh'):
            self.mode = 'oaipmh'
            self.request_version = '2.0.2'
            LOGGER.info('OAI-PMH mode detected; processing request.')
            self.oaiargs = dict((k, v) for k, v in self.kvp.items() if k)
            self.kvp = self.oaipmh().request(self.kvp)

        if self.request_version == '2.0.2':
            self.iface = csw2.Csw2(server_csw=self)
            self.context.set_model('csw')

        # configure transaction support, if specified in config
        self._gen_manager()

        namespaces = self.context.namespaces
        ops = self.context.model['operations']
        constraints = self.context.model['constraints']
        # generate domain model
        # NOTE: We should probably avoid this sort of mutable state for WSGI
        if 'GetDomain' not in ops:
            ops['GetDomain'] = self.context.gen_domains()

        # generate distributed search model, if specified in config
        if self.config.has_option('server', 'federatedcatalogues'):
            LOGGER.info('Configuring distributed search')

            constraints['FederatedCatalogues'] = {'values': []}

            for fedcat in self.config.get('server',
                                          'federatedcatalogues').split(','):
                LOGGER.debug('federated catalogue: %s', fedcat)
                constraints['FederatedCatalogues']['values'].append(fedcat)

        for key, value in self.outputschemas.items():
            get_records_params = ops['GetRecords']['parameters']
            get_records_params['outputSchema']['values'].append(
                value.NAMESPACE)
            get_records_by_id_params = ops['GetRecordById']['parameters']
            get_records_by_id_params['outputSchema']['values'].append(
                value.NAMESPACE)
            if 'Harvest' in ops:
                harvest_params = ops['Harvest']['parameters']
                harvest_params['ResourceType']['values'].append(
                    value.NAMESPACE)

        LOGGER.info('Setting MaxRecordDefault')
        if self.config.has_option('server', 'maxrecords'):
            constraints['MaxRecordDefault']['values'] = [
                self.config.get('server', 'maxrecords')]

        # load profiles
        if self.config.has_option('server', 'profiles'):
            self.profiles = pprofile.load_profiles(
                os.path.join('pycsw', 'plugins', 'profiles'),
                pprofile.Profile,
                self.config.get('server', 'profiles')
            )

            for prof in self.profiles['plugins'].keys():
                tmp = self.profiles['plugins'][prof](self.context.model,
                                                     namespaces,
                                                     self.context)

                key = tmp.outputschema  # to ref by outputschema
                self.profiles['loaded'][key] = tmp
                self.profiles['loaded'][key].extend_core(self.context.model,
                                                         namespaces,
                                                         self.config)

            LOGGER.debug('Profiles loaded: %s' % list(self.profiles['loaded'].keys()))

        # init repository
        # look for tablename, set 'records' as default
        if not self.config.has_option('repository', 'table'):
            self.config.set('repository', 'table', 'records')

        repo_filter = None
        if self.config.has_option('repository', 'filter'):
            repo_filter = self.config.get('repository', 'filter')

        if self.config.has_option('repository', 'source'):  # load custom repository
            rs = self.config.get('repository', 'source')
            rs_modname, rs_clsname = rs.rsplit('.', 1)

            rs_mod = __import__(rs_modname, globals(), locals(), [rs_clsname])
            rs_cls = getattr(rs_mod, rs_clsname)

            try:
                self.repository = rs_cls(self.context, repo_filter)
                LOGGER.debug('Custom repository %s loaded (%s)', rs, self.repository.dbtype)
            except Exception as err:
                msg = 'Could not load custom repository %s: %s' % (rs, err)
                LOGGER.exception(msg)
                error = 1
                code = 'NoApplicableCode'
                locator = 'service'
                text = 'Could not initialize repository. Check server logs'

        else:  # load default repository
            self.orm = 'sqlalchemy'
            from pycsw.core import repository
            try:
                LOGGER.info('Loading default repository')
                self.repository = repository.Repository(
                    self.config.get('repository', 'database'),
                    self.context,
                    self.environ.get('local.app_root', None),
                    self.config.get('repository', 'table'),
                    repo_filter
                )
                LOGGER.debug(
                    'Repository loaded (local): %s.' % self.repository.dbtype)
            except Exception as err:
                msg = 'Could not load repository (local): %s' % err
                LOGGER.exception(msg)
                error = 1
                code = 'NoApplicableCode'
                locator = 'service'
                text = 'Could not initialize repository. Check server logs'

        if self.requesttype == 'POST':
            LOGGER.debug('HTTP POST request')
            LOGGER.debug('CSW version: %s', self.iface.version)
            self.kvp = self.iface.parse_postdata(self.request)

        if isinstance(self.kvp, str):  # it's an exception
            error = 1
            locator = 'service'
            text = self.kvp
            if (self.kvp.find('the document is not valid') != -1 or
                    self.kvp.find('document not well-formed') != -1):
                code = 'NoApplicableCode'
            else:
                code = 'InvalidParameterValue'

        LOGGER.debug('HTTP Headers:\n%s.', self.environ)
        LOGGER.debug('Parsed request parameters: %s', self.kvp)

        if (not isinstance(self.kvp, str) and 'mode' in self.kvp and
                self.kvp['mode'] == 'opensearch'):
            self.mode = 'opensearch'
            LOGGER.info('OpenSearch mode detected; processing request.')
            self.kvp['outputschema'] = 'http://www.w3.org/2005/Atom'

        if ((len(self.kvp) == 0 and self.request_version == '3.0.0') or
                (len(self.kvp) == 1 and 'config' in self.kvp)):
            LOGGER.info('Turning on default csw30:Capabilities for base URL')
            self.kvp = {
                'service': 'CSW',
                'acceptversions': '3.0.0',
                'request': 'GetCapabilities'
            }
            http_accept = self.environ.get('HTTP_ACCEPT', '')
            if 'application/opensearchdescription+xml' in http_accept:
                self.mode = 'opensearch'
                self.kvp['outputschema'] = 'http://www.w3.org/2005/Atom'

        if error == 0:
            # test for the basic keyword values (service, version, request)
            basic_options = ['service', 'request']
            request = self.kvp.get('request', '')
            own_version_integer = util.get_version_integer(
                self.request_version)
            if self.request_version == '2.0.2':
                basic_options.append('version')
            if self.request_version == '3.0.0' and 'version' not in self.kvp and self.requesttype == 'POST':
                if 'service' not in self.kvp:
                    self.kvp['service'] = 'CSW'
                    basic_options.append('service')
                self.kvp['version'] = self.request_version
                basic_options.append('version')

            for k in basic_options:
                if k not in self.kvp:
                    if (k in ['version', 'acceptversions'] and
                            request == 'GetCapabilities'):
                        pass
                    else:
                        error = 1
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
                kvp_version = self.kvp.get('version', '')
                try:
                    kvp_version_integer = util.get_version_integer(kvp_version)
                except Exception as err:
                    kvp_version_integer = 'invalid_value'
                if (request != 'GetCapabilities' and
                        kvp_version_integer != own_version_integer):
                    error = 1
                    locator = 'version'
                    code = 'InvalidParameterValue'
                    text = ('Invalid value for version: %s. Value MUST be '
                            '2.0.2 or 3.0.0' % kvp_version)

                # check for GetCapabilities acceptversions
                if 'acceptversions' in self.kvp:
                    for vers in self.kvp['acceptversions'].split(','):
                        vers_integer = util.get_version_integer(vers)
                        if vers_integer == own_version_integer:
                            break
                        else:
                            error = 1
                            locator = 'acceptversions'
                            code = 'VersionNegotiationFailed'
                            text = ('Invalid parameter value in '
                                    'acceptversions: %s. Value MUST be '
                                    '2.0.2 or 3.0.0' %
                                    self.kvp['acceptversions'])

                # test request
                if self.kvp['request'] not in \
                    self.context.model['operations']:
                    error = 1
                    locator = 'request'
                    if request in ['Transaction', 'Harvest']:
                        code = 'OperationNotSupported'
                        text = '%s operations are not supported' % request
                    else:
                        code = 'InvalidParameterValue'
                        text = 'Invalid value for request: %s' % request

        if error == 1:  # return an ExceptionReport
            LOGGER.error('basic service options error: %s, %s, %s', code, locator, text)
            self.response = self.iface.exceptionreport(code, locator, text)

        else:  # process per the request value

            if 'responsehandler' in self.kvp:
                # set flag to process asynchronously
                import threading
                self.async = True
                request_id = self.kvp.get('requestid', None)
                if request_id is None:
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
                    self.response = self.iface._write_acknowledgement()
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
                    self.response = self.iface._write_acknowledgement()
                else:
                    self.response = self.iface.harvest()
            else:
                self.response = self.iface.exceptionreport(
                    'InvalidParameterValue', 'request',
                    'Invalid request parameter: %s' % self.kvp['request']
                )

        LOGGER.info('Request processed')
        if self.mode == 'sru':
            LOGGER.info('SRU mode detected; processing response.')
            self.response = self.sru().response_csw2sru(self.response,
                                                        self.environ)
        elif self.mode == 'opensearch':
            LOGGER.info('OpenSearch mode detected; processing response.')
            self.response = self.opensearch().response_csw2opensearch(
                self.response, self.config)

        elif self.mode == 'oaipmh':
            LOGGER.info('OAI-PMH mode detected; processing response.')
            self.response = self.oaipmh().response(
                self.response, self.oaiargs, self.repository,
                self.config.get('server', 'url')
            )

        return self._write_response()

    def getcapabilities(self):
        """ Handle GetCapabilities request """
        return self.iface.getcapabilities()

    def describerecord(self):
        """ Handle DescribeRecord request """
        return self.iface.describerecord()

    def getdomain(self):
        """ Handle GetDomain request """
        return self.iface.getdomain()

    def getrecords(self):
        """ Handle GetRecords request """
        return self.iface.getrecords()

    def getrecordbyid(self, raw=False):
        """ Handle GetRecordById request """
        return self.iface.getrecordbyid(raw)

    def getrepositoryitem(self):
        """ Handle GetRepositoryItem request """
        return self.iface.getrepositoryitem()

    def transaction(self):
        """ Handle Transaction request """
        return self.iface.transaction()

    def harvest(self):
        """ Handle Harvest request """
        return self.iface.harvest()

    def _write_response(self):
        """ Generate response """
        # set HTTP response headers and XML declaration

        xmldecl = ''
        appinfo = ''

        LOGGER.info('Writing response.')

        if hasattr(self, 'soap') and self.soap:
            self._gen_soap_wrapper()

        if etree.__version__ >= '3.5.0':  # remove superfluous namespaces
            etree.cleanup_namespaces(self.response,
                                     keep_ns_prefixes=self.context.keep_ns_prefixes)

        response = etree.tostring(self.response,
                                  pretty_print=self.pretty_print,
                                  encoding='unicode')

        if (isinstance(self.kvp, dict) and 'outputformat' in self.kvp and
                self.kvp['outputformat'] == 'application/json'):
            self.contenttype = self.kvp['outputformat']
            from pycsw.core.formats import fmt_json
            response = fmt_json.xml2json(response,
                                         self.context.namespaces,
                                         self.pretty_print)
        else:  # it's XML
            if 'outputformat' in self.kvp:
                self.contenttype = self.kvp['outputformat']
            else:
                self.contenttype = self.mimetype

            xmldecl = ('<?xml version="1.0" encoding="%s" standalone="no"?>'
                       '\n' % self.encoding)
            appinfo = '<!-- pycsw %s -->\n' % self.context.version

        if isinstance(self.contenttype, bytes):
            self.contenttype = self.contenttype.decode()

        s = (u'%s%s%s' % (xmldecl, appinfo, response)).encode(self.encoding)
        LOGGER.debug('Response code: %s',
                     self.context.response_codes[self.status])
        LOGGER.debug('Response:\n%s', s)
        return [self.context.response_codes[self.status], s]

    def _gen_soap_wrapper(self):
        """ Generate SOAP wrapper """
        LOGGER.info('Writing SOAP wrapper.')
        node = etree.Element(
            util.nspath_eval('soapenv:Envelope', self.context.namespaces),
            nsmap=self.context.namespaces
        )

        schema_location_ns = util.nspath_eval('xsi:schemaLocation',
                                              self.context.namespaces)
        node.attrib[schema_location_ns] = '%s %s' % (
            self.context.namespaces['soapenv'],
            self.context.namespaces['soapenv']
        )

        node2 = etree.SubElement(
            node, util.nspath_eval('soapenv:Body', self.context.namespaces))

        if self.exception:
            node3 = etree.SubElement(
                node2,
                util.nspath_eval('soapenv:Fault', self.context.namespaces)
            )
            node4 = etree.SubElement(
                node3,
                util.nspath_eval('soapenv:Code', self.context.namespaces)
            )

            etree.SubElement(
                node4,
                util.nspath_eval('soapenv:Value', self.context.namespaces)
            ).text = 'soap:Server'

            node4 = etree.SubElement(
                node3,
                util.nspath_eval('soapenv:Reason', self.context.namespaces)
            )

            etree.SubElement(
                node4,
                util.nspath_eval('soapenv:Text', self.context.namespaces)
            ).text = 'A server exception was encountered.'

            node4 = etree.SubElement(
                node3,
                util.nspath_eval('soapenv:Detail', self.context.namespaces)
            )
            node4.append(self.response)
        else:
            node2.append(self.response)

        self.response = node

    def _gen_manager(self):
        """ Update self.context.model with CSW-T advertising """
        if (self.config.has_option('manager', 'transactions') and
                self.config.get('manager', 'transactions') == 'true'):

            self.manager = True

            self.context.model['operations_order'].append('Transaction')

            self.context.model['operations']['Transaction'] = {
                'methods': {'get': False, 'post': True},
                'parameters': {}
            }

            schema_values = [
                'http://www.opengis.net/cat/csw/2.0.2',
                'http://www.opengis.net/cat/csw/3.0',
                'http://www.opengis.net/wms',
                'http://www.opengis.net/wmts/1.0',
                'http://www.opengis.net/wfs',
                'http://www.opengis.net/wfs/2.0',
                'http://www.opengis.net/wcs',
                'http://www.opengis.net/wps/1.0.0',
                'http://www.opengis.net/sos/1.0',
                'http://www.opengis.net/sos/2.0',
                'http://www.isotc211.org/2005/gmi',
                'urn:geoss:waf',
            ]

            self.context.model['operations_order'].append('Harvest')

            self.context.model['operations']['Harvest'] = {
                'methods': {'get': False, 'post': True},
                'parameters': {
                    'ResourceType': {'values': schema_values}
                }
            }

            self.context.model['operations']['Transaction'] = {
                'methods': {'get': False, 'post': True},
                'parameters': {
                    'TransactionSchemas': {'values': sorted(schema_values)}
                }
            }

            self.csw_harvest_pagesize = 10
            if self.config.has_option('manager', 'csw_harvest_pagesize'):
                self.csw_harvest_pagesize = int(
                    self.config.get('manager', 'csw_harvest_pagesize'))

    def _test_manager(self):
        """ Verify that transactions are allowed """

        if self.config.get('manager', 'transactions') != 'true':
            raise RuntimeError('CSW-T interface is disabled')

        """ get the client first forwarded ip """
        if 'HTTP_X_FORWARDED_FOR' in self.environ:
            ipaddress = self.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
        else:
            ipaddress = self.environ['REMOTE_ADDR']

        if not self.config.has_option('manager', 'allowed_ips') or \
        (self.config.has_option('manager', 'allowed_ips') and not
         util.ipaddress_in_whitelist(ipaddress,
                        self.config.get('manager', 'allowed_ips').split(','))):
            raise RuntimeError(
            'CSW-T operations not allowed for this IP address: %s' % ipaddress)

    def _cql_update_queryables_mappings(self, cql, mappings):
        """ Transform CQL query's properties to underlying DB columns """
        LOGGER.debug('Raw CQL text = %s', cql)
        LOGGER.debug(str(list(mappings.keys())))
        if cql is not None:
            for key in mappings.keys():
                try:
                    cql = cql.replace(key, mappings[key]['dbcol'])
                except:
                    cql = cql.replace(key, mappings[key])
            LOGGER.debug('Interpolated CQL text = %s.', cql)
            return cql

    def _process_responsehandler(self, xml):
        """ Process response handler """

        if self.kvp['responsehandler'] is not None:
            LOGGER.info('Processing responsehandler %s' %
                         self.kvp['responsehandler'])

            uprh = urlparse(self.kvp['responsehandler'])

            if uprh.scheme == 'mailto':  # email
                import smtplib

                LOGGER.debug('Email detected')

                smtp_host = 'localhost'
                if self.config.has_option('server', 'smtp_host'):
                    smtp_host = self.config.get('server', 'smtp_host')

                body = ('Subject: pycsw %s results\n\n%s' %
                        (self.kvp['request'], xml))

                try:
                    LOGGER.info('Sending email')
                    msg = smtplib.SMTP(smtp_host)
                    msg.sendmail(
                        self.config.get('metadata:main', 'contact_email'),
                        uprh.path, body
                    )
                    msg.quit()
                    LOGGER.debug('Email sent successfully.')
                except Exception as err:
                    LOGGER.exception('Error processing email')

            elif uprh.scheme == 'ftp':
                import ftplib

                LOGGER.debug('FTP detected.')

                try:
                    LOGGER.info('Sending to FTP server.')
                    ftp = ftplib.FTP(uprh.hostname)
                    if uprh.username is not None:
                        ftp.login(uprh.username, uprh.password)
                    ftp.storbinary('STOR %s' % uprh.path[1:], StringIO(xml))
                    ftp.quit()
                    LOGGER.debug('FTP sent successfully.')
                except Exception as err:
                    LOGGER.exception('Error processing FTP')

    @staticmethod
    def normalize_kvp(kvp):
        """Normalize Key Value Pairs.

        This method will transform all keys to lowercase and leave values
        unchanged, as specified in the CSW standard (see for example note
        C on Table 62 - KVP Encoding for DescribeRecord operation request
        of the CSW standard version 2.0.2)

        :arg kvp: a mapping with Key Value Pairs
        :type kvp: dict
        :returns: A new dictionary with normalized parameters
        """

        result = dict()
        for name, value in kvp.items():
            result[name.lower()] = value
        return result
