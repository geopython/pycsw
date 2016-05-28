# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2016 Tom Kralidis
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
from time import time
from six.moves.urllib.parse import quote, unquote
from six import StringIO
from six.moves.configparser import SafeConfigParser
from pycsw.core.etree import etree
from pycsw import oaipmh, opensearch, sru
from pycsw.plugins.profiles import profile as pprofile
import pycsw.plugins.outputschemas
from pycsw.core import config, log, metadata, util
from pycsw.ogc.fes import fes2
import logging

LOGGER = logging.getLogger(__name__)


class Csw3(object):
    ''' CSW 3.x server '''
    def __init__(self, server_csw):
        ''' Initialize CSW3 '''

        self.parent = server_csw
        self.version = '3.0.0'

    def getcapabilities(self):
        ''' Handle GetCapabilities request '''
        serviceidentification = True
        serviceprovider = True
        operationsmetadata = True
        filtercaps = False
        languages = False

        # validate acceptformats
        LOGGER.debug('Validating ows20:AcceptFormats')
        LOGGER.debug(self.parent.context.model['operations']['GetCapabilities']['parameters']['acceptFormats']['values'])
        if 'acceptformats' in self.parent.kvp:
            bfound = False
            for fmt in self.parent.kvp['acceptformats'].split(','):
                if fmt in self.parent.context.model['operations']['GetCapabilities']['parameters']['acceptFormats']['values']:
                    self.parent.mimetype = fmt
                    bfound = True
                    break
            if not bfound:
                return self.exceptionreport('InvalidParameterValue',
                'acceptformats', 'Invalid acceptFormats parameter value: %s' %
                self.parent.kvp['acceptformats'])

        if 'sections' in self.parent.kvp and self.parent.kvp['sections'] != '':
            serviceidentification = False
            serviceprovider = False
            operationsmetadata = False
            for section in self.parent.kvp['sections'].split(','):
                if section == 'ServiceIdentification':
                    serviceidentification = True
                if section == 'ServiceProvider':
                    serviceprovider = True
                if section == 'OperationsMetadata':
                    operationsmetadata = True
                if section == 'All':
                    serviceidentification = True
                    serviceprovider = True
                    operationsmetadata = True
                    filtercaps = True
                    languages = True
        else:
            filtercaps = True
            languages = True

        # check extra parameters that may be def'd by profiles
        if self.parent.profiles is not None:
            for prof in self.parent.profiles['loaded'].keys():
                result = \
                self.parent.profiles['loaded'][prof].check_parameters(self.parent.kvp)
                if result is not None:
                    return self.exceptionreport(result['code'],
                    result['locator'], result['text'])

        # @updateSequence: get latest update to repository
        try:
            updatesequence = \
            util.get_time_iso2unix(self.parent.repository.query_insert())
        except:
            updatesequence = None

        node = etree.Element(util.nspath_eval('csw30:Capabilities',
        self.parent.context.namespaces),
        nsmap=self.parent.context.namespaces, version='3.0.0',
        updateSequence=str(updatesequence))

        if 'updatesequence' in self.parent.kvp:
            if int(self.parent.kvp['updatesequence']) == updatesequence:
                return node
            elif int(self.parent.kvp['updatesequence']) > updatesequence:
                return self.exceptionreport('InvalidUpdateSequence',
                'updatesequence',
                'outputsequence specified (%s) is higher than server\'s \
                updatesequence (%s)' % (self.parent.kvp['updatesequence'],
                updatesequence))

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.parent.context.namespaces)] = '%s %s/csw/3.0/cswGetCapabilities.xsd' % \
        (self.parent.context.namespaces['csw30'],
         self.parent.config.get('server', 'ogc_schemas_base'))

        metadata_main = dict(self.parent.config.items('metadata:main'))

        if serviceidentification:
            LOGGER.debug('Writing section ServiceIdentification.')

            serviceidentification = etree.SubElement(node, \
            util.nspath_eval('ows20:ServiceIdentification',
            self.parent.context.namespaces))

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows20:Title', self.parent.context.namespaces)).text = \
            metadata_main.get('identification_title', 'missing')

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows20:Abstract', self.parent.context.namespaces)).text = \
            metadata_main.get('identification_abstract', 'missing')

            keywords = etree.SubElement(serviceidentification,
            util.nspath_eval('ows20:Keywords', self.parent.context.namespaces))

            for k in \
            metadata_main.get('identification_keywords').split(','):
                etree.SubElement(
                keywords, util.nspath_eval('ows20:Keyword',
                self.parent.context.namespaces)).text = k

            etree.SubElement(keywords,
            util.nspath_eval('ows20:Type', self.parent.context.namespaces),
            codeSpace='ISOTC211/19115').text = \
            metadata_main.get('identification_keywords_type', 'missing')

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows20:ServiceType', self.parent.context.namespaces),
            codeSpace='OGC').text = 'CSW'

            for stv in self.parent.context.model['parameters']['version']['values']:
                etree.SubElement(serviceidentification,
                util.nspath_eval('ows20:ServiceTypeVersion',
                self.parent.context.namespaces)).text = stv

            if self.parent.profiles is not None:
                for prof in self.parent.profiles['loaded'].keys():
                    prof_name = self.parent.profiles['loaded'][prof].name
                    prof_val = self.parent.profiles['loaded'][prof].namespaces[prof_name]

                    etree.SubElement(serviceidentification,
                    util.nspath_eval('ows20:Profile',
                    self.parent.context.namespaces)).text = prof_val

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows20:Fees', self.parent.context.namespaces)).text = \
            metadata_main.get('identification_fees', 'missing')

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows20:AccessConstraints',
            self.parent.context.namespaces)).text = \
            metadata_main.get('identification_accessconstraints', 'missing')

        if serviceprovider:
            LOGGER.debug('Writing section ServiceProvider.')
            serviceprovider = etree.SubElement(node,
            util.nspath_eval('ows20:ServiceProvider', self.parent.context.namespaces))

            etree.SubElement(serviceprovider,
            util.nspath_eval('ows20:ProviderName', self.parent.context.namespaces)).text = \
            metadata_main.get('provider_name', 'missing')

            providersite = etree.SubElement(serviceprovider,
            util.nspath_eval('ows20:ProviderSite', self.parent.context.namespaces))

            providersite.attrib[util.nspath_eval('xlink:type',
            self.parent.context.namespaces)] = 'simple'

            providersite.attrib[util.nspath_eval('xlink:href',
            self.parent.context.namespaces)] = \
            metadata_main.get('provider_url', 'missing')

            servicecontact = etree.SubElement(serviceprovider,
            util.nspath_eval('ows20:ServiceContact', self.parent.context.namespaces))

            etree.SubElement(servicecontact,
            util.nspath_eval('ows20:IndividualName',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_name', 'missing')

            etree.SubElement(servicecontact,
            util.nspath_eval('ows20:PositionName',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_position', 'missing')

            contactinfo = etree.SubElement(servicecontact,
            util.nspath_eval('ows20:ContactInfo', self.parent.context.namespaces))

            phone = etree.SubElement(contactinfo, util.nspath_eval('ows20:Phone',
            self.parent.context.namespaces))

            etree.SubElement(phone, util.nspath_eval('ows20:Voice',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_phone', 'missing')

            etree.SubElement(phone, util.nspath_eval('ows20:Facsimile',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_fax', 'missing')

            address = etree.SubElement(contactinfo,
            util.nspath_eval('ows20:Address', self.parent.context.namespaces))

            etree.SubElement(address,
            util.nspath_eval('ows20:DeliveryPoint',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_address', 'missing')

            etree.SubElement(address, util.nspath_eval('ows20:City',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_city', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows20:AdministrativeArea',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_stateorprovince', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows20:PostalCode',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_postalcode', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows20:Country', self.parent.context.namespaces)).text = \
            metadata_main.get('contact_country', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows20:ElectronicMailAddress',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_email', 'missing')

            url = etree.SubElement(contactinfo,
            util.nspath_eval('ows20:OnlineResource', self.parent.context.namespaces))

            url.attrib[util.nspath_eval('xlink:type',
            self.parent.context.namespaces)] = 'simple'

            url.attrib[util.nspath_eval('xlink:href',
            self.parent.context.namespaces)] = \
            metadata_main.get('contact_url', 'missing')

            etree.SubElement(contactinfo,
            util.nspath_eval('ows20:HoursOfService',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_hours', 'missing')

            etree.SubElement(contactinfo,
            util.nspath_eval('ows20:ContactInstructions',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_instructions', 'missing')

            etree.SubElement(servicecontact,
            util.nspath_eval('ows20:Role', self.parent.context.namespaces),
            codeSpace='ISOTC211/19115').text = \
            metadata_main.get('contact_role', 'missing')

        if operationsmetadata:
            LOGGER.debug('Writing section OperationsMetadata.')
            operationsmetadata = etree.SubElement(node,
            util.nspath_eval('ows20:OperationsMetadata',
            self.parent.context.namespaces))

            for operation in self.parent.context.model['operations_order']:
                oper = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows20:Operation', self.parent.context.namespaces),
                name=operation)

                dcp = etree.SubElement(oper, util.nspath_eval('ows20:DCP',
                self.parent.context.namespaces))

                http = etree.SubElement(dcp, util.nspath_eval('ows20:HTTP',
                self.parent.context.namespaces))

                if self.parent.context.model['operations'][operation]['methods']['get']:
                    get = etree.SubElement(http, util.nspath_eval('ows20:Get',
                    self.parent.context.namespaces))

                    get.attrib[util.nspath_eval('xlink:type',\
                    self.parent.context.namespaces)] = 'simple'

                    get.attrib[util.nspath_eval('xlink:href',\
                    self.parent.context.namespaces)] = self.parent.config.get('server', 'url')

                if self.parent.context.model['operations'][operation]['methods']['post']:
                    post = etree.SubElement(http, util.nspath_eval('ows20:Post',
                    self.parent.context.namespaces))
                    post.attrib[util.nspath_eval('xlink:type',
                    self.parent.context.namespaces)] = 'simple'
                    post.attrib[util.nspath_eval('xlink:href',
                    self.parent.context.namespaces)] = \
                    self.parent.config.get('server', 'url')

                for parameter in \
                sorted(self.parent.context.model['operations'][operation]['parameters']):
                    param = etree.SubElement(oper,
                    util.nspath_eval('ows20:Parameter',
                    self.parent.context.namespaces), name=parameter)

                    param.append(self._write_allowed_values(self.parent.context.model['operations'][operation]['parameters'][parameter]['values']))

                if operation == 'GetRecords':  # advertise queryables, MaxRecordDefault
                    for qbl in sorted(self.parent.repository.queryables.keys()):
                        if qbl not in ['_all', 'SupportedDublinCoreQueryables']:
                            param = etree.SubElement(oper,
                            util.nspath_eval('ows20:Constraint',
                            self.parent.context.namespaces), name=qbl)

                            param.append(self._write_allowed_values(self.parent.repository.queryables[qbl]))

                    if self.parent.profiles is not None:
                        for con in sorted(self.parent.context.model[\
                        'operations']['GetRecords']['constraints'].keys()):
                            param = etree.SubElement(oper,
                            util.nspath_eval('ows20:Constraint',
                            self.parent.context.namespaces), name=con)

                            param.append(self._write_allowed_values(self.parent.context.model['operations']['GetRecords']['constraints'][con]['values']))

                    extra_constraints = {
                        'OpenSearchDescriptionDocument': ['%s?mode=opensearch&service=CSW&version=3.0.0&request=GetCapabilities' % self.parent.config.get('server', 'url')],
                        'MaxRecordDefault': self.parent.context.model['constraints']['MaxRecordDefault']['values'],
                    }

                    for key in sorted(extra_constraints.keys()):
                        param = etree.SubElement(oper,
                        util.nspath_eval('ows20:Constraint',
                        self.parent.context.namespaces), name=key)
                        param.append(self._write_allowed_values(extra_constraints[key]))

                    if 'FederatedCatalogues' in self.parent.context.model['constraints']:
                        param = etree.SubElement(oper,
                        util.nspath_eval('ows20:Constraint',
                        self.parent.context.namespaces), name='FederatedCatalogues')
                        param.append(self._write_allowed_values(self.parent.context.model['constraints']['FederatedCatalogues']['values']))

            for parameter in sorted(self.parent.context.model['parameters'].keys()):
                param = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows20:Parameter', self.parent.context.namespaces),
                name=parameter)

                param.append(self._write_allowed_values(self.parent.context.model['parameters'][parameter]['values']))

            for qbl in sorted(self.parent.repository.queryables.keys()):
                if qbl == 'SupportedDublinCoreQueryables':
                    param = etree.SubElement(operationsmetadata,
                    util.nspath_eval('ows20:Constraint',
                    self.parent.context.namespaces), name='CoreQueryables')
                    param.append(self._write_allowed_values(self.parent.repository.queryables[qbl]))

            for constraint in sorted(self.parent.context.model['constraints'].keys()):
                param = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows20:Constraint', self.parent.context.namespaces),
                name=constraint)

                param.append(self._write_allowed_values(self.parent.context.model['constraints'][constraint]['values']))

            if self.parent.profiles is not None:
                for prof in self.parent.profiles['loaded'].keys():
                    ecnode = \
                    self.parent.profiles['loaded'][prof].get_extendedcapabilities()
                    if ecnode is not None:
                        operationsmetadata.append(ecnode)

        if languages:
            LOGGER.debug('Writing section ows:Languages')
            langs = etree.SubElement(node,
            util.nspath_eval('ows20:Languages', self.parent.context.namespaces))
            etree.SubElement(langs,
            util.nspath_eval('ows20:Language', self.parent.context.namespaces)).text = self.parent.language['639_code']

        if not filtercaps:
            return node

        # always write out Filter_Capabilities
        LOGGER.debug('Writing section Filter_Capabilities.')
        fltcaps = etree.SubElement(node,
        util.nspath_eval('fes20:Filter_Capabilities', self.parent.context.namespaces))

        conformance = etree.SubElement(fltcaps,
        util.nspath_eval('fes20:Conformance', self.parent.context.namespaces))

        for value in fes2.MODEL['Conformance']['values']:
            constraint = etree.SubElement(conformance,
                                          util.nspath_eval('fes20:Constraint', self.parent.context.namespaces),
                                          name=value)
            etree.SubElement(constraint,
                             util.nspath_eval('ows11:NoValues', self.parent.context.namespaces))
            etree.SubElement(constraint,
                             util.nspath_eval('ows11:DefaultValue', self.parent.context.namespaces)).text = 'TRUE'

        idcaps = etree.SubElement(fltcaps,
        util.nspath_eval('fes20:Id_Capabilities', self.parent.context.namespaces))

        for idcap in fes2.MODEL['Ids']['values']:
            etree.SubElement(idcaps, util.nspath_eval('fes20:ResourceIdentifier',
            self.parent.context.namespaces), name=idcap)

        scalarcaps = etree.SubElement(fltcaps,
        util.nspath_eval('fes20:Scalar_Capabilities', self.parent.context.namespaces))

        etree.SubElement(scalarcaps, util.nspath_eval('fes20:LogicalOperators',
        self.parent.context.namespaces))

        cmpops = etree.SubElement(scalarcaps,
        util.nspath_eval('fes20:ComparisonOperators', self.parent.context.namespaces))

        for cmpop in sorted(fes2.MODEL['ComparisonOperators'].keys()):
            etree.SubElement(cmpops,
            util.nspath_eval('fes20:ComparisonOperator',
            self.parent.context.namespaces), name=fes2.MODEL['ComparisonOperators'][cmpop]['opname'])

        spatialcaps = etree.SubElement(fltcaps,
        util.nspath_eval('fes20:Spatial_Capabilities', self.parent.context.namespaces))

        geomops = etree.SubElement(spatialcaps,
        util.nspath_eval('fes20:GeometryOperands', self.parent.context.namespaces))

        for geomtype in \
        fes2.MODEL['GeometryOperands']['values']:
            etree.SubElement(geomops,
            util.nspath_eval('fes20:GeometryOperand',
            self.parent.context.namespaces), name=geomtype)

        spatialops = etree.SubElement(spatialcaps,
        util.nspath_eval('fes20:SpatialOperators', self.parent.context.namespaces))

        for spatial_comparison in \
        fes2.MODEL['SpatialOperators']['values']:
            etree.SubElement(spatialops,
            util.nspath_eval('fes20:SpatialOperator', self.parent.context.namespaces),
            name=spatial_comparison)

        functions = etree.SubElement(fltcaps,
        util.nspath_eval('fes20:Functions', self.parent.context.namespaces))

        for fnop in sorted(fes2.MODEL['Functions'].keys()):
            fn = etree.SubElement(functions,
            util.nspath_eval('fes20:Function', self.parent.context.namespaces),
            name=fnop)

            etree.SubElement(fn, util.nspath_eval('fes20:Returns',
                             self.parent.context.namespaces)).text = \
                             fes2.MODEL['Functions'][fnop]['returns']

        return node

    def getdomain(self):
        ''' Handle GetDomain request '''
        if ('parametername' not in self.parent.kvp and
            'valuereference' not in self.parent.kvp):
            return self.exceptionreport('MissingParameterValue',
            'parametername', 'Missing value. \
            One of valuereference or parametername must be specified')

        node = etree.Element(util.nspath_eval('csw30:GetDomainResponse',
        self.parent.context.namespaces), nsmap=self.parent.context.namespaces)

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.parent.context.namespaces)] = '%s %s/csw/3.0/cswGetDomain.xsd' % \
        (self.parent.context.namespaces['csw30'],
        self.parent.config.get('server', 'ogc_schemas_base'))

        if 'parametername' in self.parent.kvp:
            for pname in self.parent.kvp['parametername'].split(','):
                LOGGER.debug('Parsing parametername %s.' % pname)
                domainvalue = etree.SubElement(node,
                util.nspath_eval('csw30:DomainValues', self.parent.context.namespaces),
                type='csw30:Record', resultType='available')
                etree.SubElement(domainvalue,
                util.nspath_eval('csw30:ParameterName',
                self.parent.context.namespaces)).text = pname
                try:
                    operation, parameter = pname.split('.')
                except:
                    return node
                if (operation in self.parent.context.model['operations'] and
                    parameter in self.parent.context.model['operations'][operation]['parameters']):
                    listofvalues = etree.SubElement(domainvalue,
                    util.nspath_eval('csw30:ListOfValues', self.parent.context.namespaces))
                    for val in \
                    sorted(self.parent.context.model['operations'][operation]\
                    ['parameters'][parameter]['values']):
                        etree.SubElement(listofvalues,
                        util.nspath_eval('csw30:Value',
                        self.parent.context.namespaces)).text = val

        if 'valuereference' in self.parent.kvp:
            for pname in self.parent.kvp['valuereference'].split(','):
                LOGGER.debug('Parsing valuereference %s.' % pname)

                if pname.find('/') == 0:  # it's an XPath
                    pname2 = pname
                else:  # it's a core queryable, map to internal typename model
                    try:
                        pname2 = self.parent.repository.queryables['_all'][pname]['dbcol']
                    except:
                        pname2 = pname

                # decipher typename
                dvtype = None
                if self.parent.profiles is not None:
                    for prof in self.parent.profiles['loaded'].keys():
                        for prefix in self.parent.profiles['loaded'][prof].prefixes:
                            if pname2.find(prefix) != -1:
                                dvtype = self.parent.profiles['loaded'][prof].typename
                                break
                if not dvtype:
                    dvtype = 'csw30:Record'

                domainvalue = etree.SubElement(node,
                util.nspath_eval('csw30:DomainValues', self.parent.context.namespaces),
                type=dvtype, resultType='available')
                etree.SubElement(domainvalue,
                util.nspath_eval('csw30:ValueReference',
                self.parent.context.namespaces)).text = pname

                try:
                    LOGGER.debug(
                    'Querying repository property %s, typename %s, \
                    domainquerytype %s.' % \
                    (pname2, dvtype, self.parent.domainquerytype))

                    results = self.parent.repository.query_domain(
                    pname2, dvtype, self.parent.domainquerytype, True)

                    LOGGER.debug('Results: %s' % str(len(results)))

                    if self.parent.domainquerytype == 'range':
                        rangeofvalues = etree.SubElement(domainvalue,
                        util.nspath_eval('csw30:RangeOfValues',
                        self.parent.context.namespaces))

                        etree.SubElement(rangeofvalues,
                        util.nspath_eval('csw30:MinValue',
                        self.parent.context.namespaces)).text = results[0][0]

                        etree.SubElement(rangeofvalues,
                        util.nspath_eval('csw30:MaxValue',
                        self.parent.context.namespaces)).text = results[0][1]
                    else:
                        listofvalues = etree.SubElement(domainvalue,
                        util.nspath_eval('csw30:ListOfValues',
                        self.parent.context.namespaces))
                        for result in results:
                            LOGGER.debug(str(result))
                            if (result is not None and
                                result[0] is not None):  # drop null values
                                etree.SubElement(listofvalues,
                                util.nspath_eval('csw30:Value',
                                self.parent.context.namespaces),
                                count=str(result[1])).text = result[0]
                except Exception as err:
                    LOGGER.debug('No results for propertyname %s: %s.' %
                    (pname2, str(err)))
        return node

    def getrecords(self):
        ''' Handle GetRecords request '''

        timestamp = util.get_today_and_now()

        if ('elementsetname' not in self.parent.kvp and
            'elementname' not in self.parent.kvp):
            if self.parent.requesttype == 'GET':
                LOGGER.debug(self.parent.requesttype)
                self.parent.kvp['elementsetname'] = 'summary'
            else:
                # mutually exclusive required
                return self.exceptionreport('MissingParameterValue',
                'elementsetname',
                'Missing one of ElementSetName or ElementName parameter(s)')

        if 'elementsetname' in self.parent.kvp and 'elementname' in self.parent.kvp:
            # mutually exclusive required
            return self.exceptionreport('NoApplicableCode',
            'elementsetname',
            'Only ONE of ElementSetName or ElementName parameter(s) is permitted')

        if 'elementsetname' not in self.parent.kvp:
                self.parent.kvp['elementsetname'] = 'summary'

        if 'outputschema' not in self.parent.kvp:
            self.parent.kvp['outputschema'] = self.parent.context.namespaces['csw30']

        LOGGER.debug(self.parent.context.model['operations']['GetRecords']['parameters']['outputSchema']['values'])
        if (self.parent.kvp['outputschema'] not in self.parent.context.model['operations']
            ['GetRecords']['parameters']['outputSchema']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputschema', 'Invalid outputSchema parameter value: %s' %
            self.parent.kvp['outputschema'])

        if 'outputformat' not in self.parent.kvp:
            self.parent.kvp['outputformat'] = 'application/xml'

        if 'HTTP_ACCEPT' in self.parent.environ:
            LOGGER.debug('Detected HTTP Accept header: %s', self.parent.environ['HTTP_ACCEPT'])
            formats_match = False
            if 'outputformat' in self.parent.kvp:
                LOGGER.debug(self.parent.kvp['outputformat'])
                for ofmt in self.parent.environ['HTTP_ACCEPT'].split(','):
                    LOGGER.debug('Comparing %s and %s', ofmt, self.parent.kvp['outputformat'])
                    if ofmt.split('/')[0] in self.parent.kvp['outputformat']:
                        LOGGER.debug('FOUND OUTPUT MATCH')
                        formats_match = True
                if not formats_match:
                    return self.exceptionreport('InvalidParameterValue',
                    'outputformat', 'HTTP Accept header (%s) and outputformat (%s) must agree' %
                    (self.parent.environ['HTTP_ACCEPT'], self.parent.kvp['outputformat']))
            else:
                for ofmt in self.parent.environ['HTTP_ACCEPT'].split(','):
                    if ofmt in self.parent.context.model['operations']['GetRecords']['parameters']['outputFormat']['values']:
                        self.parent.kvp['outputformat'] = ofmt
                        break


        if (self.parent.kvp['outputformat'] not in self.parent.context.model['operations']
            ['GetRecords']['parameters']['outputFormat']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputformat', 'Invalid outputFormat parameter value: %s' %
            self.parent.kvp['outputformat'])

        if 'outputformat' in self.parent.kvp:
            LOGGER.debug('Setting content type')
            self.parent.contenttype = self.parent.kvp['outputformat']
            if self.parent.kvp['outputformat'] == 'application/atom+xml':
                self.parent.kvp['outputschema'] = self.parent.context.namespaces['atom']
                self.parent.mode = 'opensearch'

        if (('elementname' not in self.parent.kvp or
             len(self.parent.kvp['elementname']) == 0) and
             self.parent.kvp['elementsetname'] not in
             self.parent.context.model['operations']['GetRecords']['parameters']
             ['ElementSetName']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'elementsetname', 'Invalid ElementSetName parameter value: %s' %
            self.parent.kvp['elementsetname'])

        if 'typenames' not in self.parent.kvp:
            return self.exceptionreport('MissingParameterValue',
            'typenames', 'Missing typenames parameter')

        if ('typenames' in self.parent.kvp and
            self.parent.requesttype == 'GET'):  # passed via GET
            #self.parent.kvp['typenames'] = self.parent.kvp['typenames'].split(',')
            self.parent.kvp['typenames'] = ['csw:Record' if x=='Record' else x for x in self.parent.kvp['typenames'].split(',')]

        if 'namespace' in self.parent.kvp:
            LOGGER.debug('resolving KVP namespace bindings')
            LOGGER.debug(self.parent.kvp['typenames'])
            self.parent.kvp['typenames'] = self.resolve_nsmap(self.parent.kvp['typenames'])
            if 'elementname' in self.parent.kvp:
                LOGGER.debug(self.parent.kvp['elementname'])
                self.parent.kvp['elementname'] = self.resolve_nsmap(self.parent.kvp['elementname'].split(','))

        if 'typenames' in self.parent.kvp:
            for tname in self.parent.kvp['typenames']:
                #if tname == 'Record':
                #    tname = 'csw:Record'
                if (tname not in self.parent.context.model['operations']['GetRecords']
                    ['parameters']['typeNames']['values']):
                    return self.exceptionreport('InvalidParameterValue',
                    'typenames', 'Invalid typeNames parameter value: %s' %
                    tname)

        # check elementname's
        if 'elementname' in self.parent.kvp:
            for ename in self.parent.kvp['elementname']:
                if ename not in self.parent.repository.queryables['_all']:
                    return self.exceptionreport('InvalidParameterValue',
                    'elementname', 'Invalid ElementName parameter value: %s' %
                    ename)

        maxrecords_cfg = -1  # not set in config server.maxrecords

        if self.parent.config.has_option('server', 'maxrecords'):
            maxrecords_cfg = int(self.parent.config.get('server', 'maxrecords'))

        if 'maxrecords' in self.parent.kvp and self.parent.kvp['maxrecords'] == 'unlimited':
            LOGGER.debug('Detected maxrecords=unlimited')
            self.parent.kvp.pop('maxrecords')

        if 'maxrecords' not in self.parent.kvp:  # not specified by client
            if maxrecords_cfg > -1:  # specified in config
                self.parent.kvp['maxrecords'] = maxrecords_cfg
            else:  # spec default
                self.parent.kvp['maxrecords'] = 10
        else:  # specified by client
            if self.parent.kvp['maxrecords'] == '':
                self.parent.kvp['maxrecords'] = 10
            if maxrecords_cfg > -1:  # set in config
                if int(self.parent.kvp['maxrecords']) > maxrecords_cfg:
                    self.parent.kvp['maxrecords'] = maxrecords_cfg

        if any(x in ['bbox', 'q', 'time'] for x in self.parent.kvp):
            LOGGER.debug('OpenSearch Geo/Time parameters detected.')
            self.parent.kvp['constraintlanguage'] = 'FILTER'
            try:
                tmp_filter = opensearch.kvp2filterxml(self.parent.kvp, self.parent.context)
            except Exception as err:
                return self.exceptionreport('InvalidParameterValue', 'bbox', str(err))

            if tmp_filter is not "":
                self.parent.kvp['constraint'] = tmp_filter
                LOGGER.debug('OpenSearch Geo/Time parameters to Filter: %s.' % self.parent.kvp['constraint'])

        if self.parent.requesttype == 'GET':
            if 'constraint' in self.parent.kvp:
                # GET request
                LOGGER.debug('csw:Constraint passed over HTTP GET.')
                if 'constraintlanguage' not in self.parent.kvp:
                    return self.exceptionreport('MissingParameterValue',
                    'constraintlanguage',
                    'constraintlanguage required when constraint specified')
                if (self.parent.kvp['constraintlanguage'] not in
                self.parent.context.model['operations']['GetRecords']['parameters']
                ['CONSTRAINTLANGUAGE']['values']):
                    return self.exceptionreport('InvalidParameterValue',
                    'constraintlanguage', 'Invalid constraintlanguage: %s'
                    % self.parent.kvp['constraintlanguage'])
                if self.parent.kvp['constraintlanguage'] == 'CQL_TEXT':
                    tmp = self.parent.kvp['constraint']
                    self.parent.kvp['constraint'] = {}
                    self.parent.kvp['constraint']['type'] = 'cql'
                    self.parent.kvp['constraint']['where'] = \
                    self.parent._cql_update_queryables_mappings(tmp,
                    self.parent.repository.queryables['_all'])
                    self.parent.kvp['constraint']['values'] = {}
                elif self.parent.kvp['constraintlanguage'] == 'FILTER':
                    # validate filter XML
                    try:
                        schema = os.path.join(self.parent.config.get('server', 'home'),
                        'core', 'schemas', 'ogc', 'filter', '1.1.0', 'filter.xsd')
                        LOGGER.debug('Validating Filter %s.' %
                        self.parent.kvp['constraint'])
                        schema = etree.XMLSchema(file=schema)
                        parser = etree.XMLParser(schema=schema, resolve_entities=False)
                        doc = etree.fromstring(self.parent.kvp['constraint'], parser)
                        LOGGER.debug('Filter is valid XML.')
                        self.parent.kvp['constraint'] = {}
                        self.parent.kvp['constraint']['type'] = 'filter'
                        self.parent.kvp['constraint']['where'], self.parent.kvp['constraint']['values'] = \
                        fes2.parse(doc,
                        self.parent.repository.queryables['_all'],
                        self.parent.repository.dbtype,
                        self.parent.context.namespaces, self.parent.orm, self.parent.language['text'], self.parent.repository.fts)
                    except Exception as err:
                        errortext = \
                        'Exception: document not valid.\nError: %s.' % str(err)

                        LOGGER.debug(errortext)
                        return self.exceptionreport('InvalidParameterValue',
                        'bbox', 'Invalid Filter query: %s' % errortext)
            else:
                self.parent.kvp['constraint'] = {}

        if 'sortby' not in self.parent.kvp:
            self.parent.kvp['sortby'] = None
        elif 'sortby' in self.parent.kvp and self.parent.requesttype == 'GET':
            LOGGER.debug('Sorted query specified.')
            tmp = self.parent.kvp['sortby']
            self.parent.kvp['sortby'] = {}

            try:
                name, order = tmp.rsplit(':', 1)
            except:
                return self.exceptionreport('InvalidParameterValue',
                'sortby', 'Invalid SortBy value: must be in the format\
                propertyname:A or propertyname:D')

            try:
                self.parent.kvp['sortby']['propertyname'] = \
                self.parent.repository.queryables['_all'][name]['dbcol']
                if name.find('BoundingBox') != -1 or name.find('Envelope') != -1:
                    # it's a spatial sort
                    self.parent.kvp['sortby']['spatial'] = True
            except Exception as err:
                return self.exceptionreport('InvalidParameterValue',
                'sortby', 'Invalid SortBy propertyname: %s' % name)

            if order not in ['A', 'D']:
                return self.exceptionreport('InvalidParameterValue',
                'sortby', 'Invalid SortBy value: sort order must be "A" or "D"')

            if order == 'D':
                self.parent.kvp['sortby']['order'] = 'DESC'
            else:
                self.parent.kvp['sortby']['order'] = 'ASC'

        if 'startposition' not in self.parent.kvp:
            self.parent.kvp['startposition'] = 1

        if 'recordids' in self.parent.kvp and self.parent.kvp['recordids'] != '':
            # query repository
            LOGGER.debug('Querying repository with RECORD ids: %s.' % self.parent.kvp['recordids'])
            results = self.parent.repository.query_ids(self.parent.kvp['recordids'].split(','))
            matched = str(len(results))
            if len(results) == 0:
                return self.exceptionreport('NotFound', 'recordids',
                'No records found for \'%s\'' % self.parent.kvp['recordids'])
        else:
            # query repository
            LOGGER.debug('Querying repository with constraint: %s,\
            sortby: %s, typenames: %s, maxrecords: %s, startposition: %s.' %
            (self.parent.kvp['constraint'], self.parent.kvp['sortby'], self.parent.kvp['typenames'],
            self.parent.kvp['maxrecords'], self.parent.kvp['startposition']))

            try:
                matched, results = self.parent.repository.query(
                constraint=self.parent.kvp['constraint'],
                sortby=self.parent.kvp['sortby'], typenames=self.parent.kvp['typenames'],
                maxrecords=self.parent.kvp['maxrecords'],
                startposition=int(self.parent.kvp['startposition'])-1)
            except Exception as err:
                return self.exceptionreport('InvalidParameterValue', 'constraint',
                'Invalid query: %s' % err)

        if int(matched) == 0:
            returned = nextrecord = '0'
        else:
            if int(matched) < int(self.parent.kvp['maxrecords']):
                returned = matched
                nextrecord = '0'
            else:
                returned = str(self.parent.kvp['maxrecords'])
                if int(self.parent.kvp['startposition']) + int(self.parent.kvp['maxrecords']) >= int(matched):
                    nextrecord = '0'
                else:
                    nextrecord = str(int(self.parent.kvp['startposition']) + \
                    int(self.parent.kvp['maxrecords']))

        LOGGER.debug('Results: matched: %s, returned: %s, next: %s.' % \
        (matched, returned, nextrecord))

        node = etree.Element(util.nspath_eval('csw30:GetRecordsResponse',
        self.parent.context.namespaces),
        nsmap=self.parent.context.namespaces, version='3.0.0')

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.parent.context.namespaces)] = \
        '%s %s/csw/3.0/cswGetRecordsResponse.xsd' % \
        (self.parent.context.namespaces['csw30'], self.parent.config.get('server', 'ogc_schemas_base'))

        if 'requestid' in self.parent.kvp and self.parent.kvp['requestid'] is not None:
            etree.SubElement(node, util.nspath_eval('csw:RequestId',
            self.parent.context.namespaces)).text = self.parent.kvp['requestid']

        etree.SubElement(node, util.nspath_eval('csw30:SearchStatus',
        self.parent.context.namespaces), timestamp=timestamp)

        #if 'where' not in self.parent.kvp['constraint'] and \
        #self.parent.kvp['resulttype'] is None:
        #    returned = '0'

        searchresults = etree.SubElement(node,
        util.nspath_eval('csw30:SearchResults', self.parent.context.namespaces),
        numberOfRecordsMatched=matched, numberOfRecordsReturned=returned,
        nextRecord=nextrecord, recordSchema=self.parent.kvp['outputschema'],
        expires=timestamp, status=get_resultset_status(matched, nextrecord))

        if self.parent.kvp['elementsetname'] is not None:
            searchresults.attrib['elementSet'] = self.parent.kvp['elementsetname']

        #if 'where' not in self.parent.kvp['constraint'] \
        #and self.parent.kvp['resulttype'] is None:
        #    LOGGER.debug('Empty result set returned.')
        #    return node

        if results is not None:
            if len(results) < int(self.parent.kvp['maxrecords']):
                max1 = len(results)
            else:
                max1 = int(self.parent.kvp['startposition']) + (int(self.parent.kvp['maxrecords'])-1)
            LOGGER.debug('Presenting records %s - %s.' %
            (self.parent.kvp['startposition'], max1))

            for res in results:
                try:
                    if (self.parent.kvp['outputschema'] ==
                        'http://www.opengis.net/cat/csw/3.0' and
                        'csw:Record' in self.parent.kvp['typenames']):
                        # serialize csw:Record inline
                        searchresults.append(self._write_record(
                        res, self.parent.repository.queryables['_all']))
                    elif (self.parent.kvp['outputschema'] ==
                        'http://www.opengis.net/cat/csw/3.0' and
                        'csw:Record' not in self.parent.kvp['typenames']):
                        # serialize into csw:Record model

                        for prof in self.parent.profiles['loaded']:
                            # find source typename
                            if self.parent.profiles['loaded'][prof].typename in \
                            self.parent.kvp['typenames']:
                                typename = self.parent.profiles['loaded'][prof].typename
                                break

                        util.transform_mappings(self.parent.repository.queryables['_all'],
                        self.parent.context.model['typenames'][typename]\
                        ['mappings']['csw:Record'], reverse=True)

                        searchresults.append(self._write_record(
                        res, self.parent.repository.queryables['_all']))
                    elif self.parent.kvp['outputschema'] in self.parent.outputschemas:  # use outputschema serializer
                        searchresults.append(self.parent.outputschemas[self.parent.kvp['outputschema']].write_record(res, self.parent.kvp['elementsetname'], self.parent.context, self.parent.config.get('server', 'url')))
                    else:  # use profile serializer
                        searchresults.append(
                        self.parent.profiles['loaded'][self.parent.kvp['outputschema']].\
                        write_record(res, self.parent.kvp['elementsetname'],
                        self.parent.kvp['outputschema'],
                        self.parent.repository.queryables['_all']))
                except Exception as err:
                    self.parent.response = self.exceptionreport(
                    'NoApplicableCode', 'service',
                    'Record serialization failed: %s' % str(err))
                    return self.parent.response

        if (self.parent.config.has_option('server', 'federatedcatalogues') and
            'distributedsearch' in self.parent.kvp and
            self.parent.kvp['distributedsearch'] and self.parent.kvp['hopcount'] > 0):
            # do distributed search

            LOGGER.debug('DistributedSearch specified (hopCount: %s).' %
            self.parent.kvp['hopcount'])

            from owslib.csw import CatalogueServiceWeb
            from owslib.ows import ExceptionReport
            for fedcat in \
            self.parent.config.get('server', 'federatedcatalogues').split(','):
                LOGGER.debug('Performing distributed search on federated \
                catalogue: %s.' % fedcat)
                try:
                    start_time = time()
                    remotecsw = CatalogueServiceWeb(fedcat, skip_caps=True)
                    remotecsw.getrecords2(xml=self.parent.request,
                                          esn=self.parent.kvp['elementsetname'],
                                          outputschema=self.parent.kvp['outputschema'])

                    fsr = etree.SubElement(searchresults, util.nspath_eval(
                        'csw30:FederatedSearchResult',
                         self.parent.context.namespaces),
                         catalogueURL=fedcat.request)

                    msg = 'Distributed search results from catalogue %s: %s.' % (fedcat, remotecsw.results)
                    LOGGER.debug(msg)
                    fsr.append(etree.Comment(msg))

                    search_result = etree.SubElement(fsr, util.nspath_eval(
                        'csw30:searchResult', self.parent.context.namespaces),
                        recordSchema=self.parent.kvp['outputschema'],
                        elementSetName=self.parent.kvp['elementsetname'],
                        numberOfRecordsMatched=fedcat.results['matches'],
                        numberOfRecordsReturned=fedcat.results['returned'],
                        nextRecord=fedcat.results['nextrecord'],
                        elapsedTime=str(util.get_elapsed_time(start_time, time())),
                        status=get_resultset_status(
                            fedcat.results['matches'],
                            fedcat.results['nextrecord']))

                    search_result.append(remotecsw.records)
                except ExceptionReport as err:
                    error_string = 'remote CSW %s returned exception: ' % fedcat
                    searchresults.append(etree.Comment(
                    ' %s\n\n%s ' % (error_string, err)))
                    LOGGER.debug(str(err))
                except Exception as err:
                    error_string = 'remote CSW %s returned error: ' % fedcat
                    searchresults.append(etree.Comment(
                    ' %s\n\n%s ' % (error_string, err)))
                    LOGGER.debug(str(err))

#        if len(dsresults) > 0:  # return DistributedSearch results
#            for resultset in dsresults:
#                if isinstance(resultset, etree._Comment):
#                    searchresults.append(resultset)
#                for rec in resultset:
#                    searchresults.append(etree.fromstring(resultset[rec].xml, self.parent.context.parser))

        searchresults.attrib['elapsedTime'] = str(util.get_elapsed_time(self.parent.process_time_start, time()))

        if 'responsehandler' in self.parent.kvp:  # process the handler
            self.parent._process_responsehandler(etree.tostring(node,
            pretty_print=self.parent.pretty_print))
        else:
            return node

    def getrecordbyid(self, raw=False):
        ''' Handle GetRecordById request '''

        if 'id' not in self.parent.kvp:
            return self.exceptionreport('MissingParameterValue', 'id',
            'Missing id parameter')
        if len(self.parent.kvp['id']) < 1:
            return self.exceptionreport('InvalidParameterValue', 'id',
            'Invalid id parameter')
        if 'outputschema' not in self.parent.kvp:
            self.parent.kvp['outputschema'] = self.parent.context.namespaces['csw30']

        if 'HTTP_ACCEPT' in self.parent.environ:
            LOGGER.debug('Detected HTTP Accept header: %s', self.parent.environ['HTTP_ACCEPT'])
            formats_match = False
            if 'outputformat' in self.parent.kvp:
                LOGGER.debug(self.parent.kvp['outputformat'])
                for ofmt in self.parent.environ['HTTP_ACCEPT'].split(','):
                    LOGGER.debug('Comparing %s and %s', ofmt, self.parent.kvp['outputformat'])
                    if ofmt.split('/')[0] in self.parent.kvp['outputformat']:
                        LOGGER.debug('FOUND OUTPUT MATCH')
                        formats_match = True
                if not formats_match:
                    return self.exceptionreport('InvalidParameterValue',
                    'outputformat', 'HTTP Accept header (%s) and outputformat (%s) must agree' %
                    (self.parent.environ['HTTP_ACCEPT'], self.parent.kvp['outputformat']))
            else:
                for ofmt in self.parent.environ['HTTP_ACCEPT'].split(','):
                    if ofmt in self.parent.context.model['operations']['GetRecords']['parameters']['outputFormat']['values']:
                        self.parent.kvp['outputformat'] = ofmt
                        break

        if ('outputformat' in self.parent.kvp and
            self.parent.kvp['outputformat'] not in
            self.parent.context.model['operations']['GetRecordById']['parameters']
            ['outputFormat']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputformat', 'Invalid outputformat parameter %s' %
            self.parent.kvp['outputformat'])

        if ('outputschema' in self.parent.kvp and self.parent.kvp['outputschema'] not in
            self.parent.context.model['operations']['GetRecordById']['parameters']
            ['outputSchema']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputschema', 'Invalid outputschema parameter %s' %
            self.parent.kvp['outputschema'])

        if 'outputformat' in self.parent.kvp:
            self.parent.contenttype = self.parent.kvp['outputformat']
            if self.parent.kvp['outputformat'] == 'application/atom+xml':
                self.parent.kvp['outputschema'] = self.parent.context.namespaces['atom']
                self.parent.mode = 'opensearch'

        if 'elementsetname' not in self.parent.kvp:
            self.parent.kvp['elementsetname'] = 'summary'
        else:
            if (self.parent.kvp['elementsetname'] not in
                self.parent.context.model['operations']['GetRecordById']['parameters']
                ['ElementSetName']['values']):
                return self.exceptionreport('InvalidParameterValue',
                'elementsetname', 'Invalid elementsetname parameter %s' %
                self.parent.kvp['elementsetname'])

        # query repository
        LOGGER.debug('Querying repository with ids: %s.' % self.parent.kvp['id'])
        results = self.parent.repository.query_ids([self.parent.kvp['id']])

        if raw:  # GetRepositoryItem request
            LOGGER.debug('GetRepositoryItem request.')
            if len(results) > 0:
                return etree.fromstring(util.getqattr(results[0],
                self.parent.context.md_core_model['mappings']['pycsw:XML']), self.parent.context.parser)

        for result in results:
            if (util.getqattr(result,
            self.parent.context.md_core_model['mappings']['pycsw:Typename']) == 'csw:Record'
            and self.parent.kvp['outputschema'] ==
            'http://www.opengis.net/cat/csw/3.0'):
                # serialize record inline
                node = self._write_record(
                result, self.parent.repository.queryables['_all'])
            elif (self.parent.kvp['outputschema'] ==
                'http://www.opengis.net/cat/csw/3.0'):
                # serialize into csw:Record model
                typename = None

                for prof in self.parent.profiles['loaded']:  # find source typename
                    if self.parent.profiles['loaded'][prof].typename in \
                    [util.getqattr(result, self.parent.context.md_core_model['mappings']['pycsw:Typename'])]:
                        typename = self.parent.profiles['loaded'][prof].typename
                        break

                if typename is not None:
                    util.transform_mappings(self.parent.repository.queryables['_all'],
                    self.parent.context.model['typenames'][typename]\
                    ['mappings']['csw:Record'], reverse=True)

                node = self._write_record( result, self.parent.repository.queryables['_all'])
            elif self.parent.kvp['outputschema'] in self.parent.outputschemas:  # use outputschema serializer
                node = self.parent.outputschemas[self.parent.kvp['outputschema']].write_record(result, self.parent.kvp['elementsetname'], self.parent.context, self.parent.config.get('server', 'url'))
            else:  # it's a profile output
                node = self.parent.profiles['loaded'][self.parent.kvp['outputschema']].write_record(
                result, self.parent.kvp['elementsetname'],
                self.parent.kvp['outputschema'], self.parent.repository.queryables['_all'])

        if raw and len(results) == 0:
            return None

        if len(results) == 0:
            return self.exceptionreport('NotFound', 'id',
            'No repository item found for \'%s\'' % self.parent.kvp['id'])

        return node

    def getrepositoryitem(self):
        ''' Handle GetRepositoryItem request '''

        # similar to GetRecordById without csw:* wrapping
        node = self.parent.getrecordbyid(raw=True)
        if node is None:
            return self.exceptionreport('NotFound', 'id',
            'No repository item found for \'%s\'' % self.parent.kvp['id'])
        else:
            return node

    def transaction(self):
        ''' Handle Transaction request '''

        try:
            self.parent._test_manager()
        except Exception as err:
            return self.exceptionreport('NoApplicableCode', 'transaction',
            str(err))

        inserted = 0
        updated = 0
        deleted = 0

        insertresults = []

        LOGGER.debug('Transaction list: %s' % self.parent.kvp['transactions'])

        for ttype in self.parent.kvp['transactions']:
            if ttype['type'] == 'insert':
                try:
                    record = metadata.parse_record(self.parent.context,
                    ttype['xml'], self.parent.repository)[0]
                except Exception as err:
                    return self.exceptionreport('NoApplicableCode', 'insert',
                    'Transaction (insert) failed: record parsing failed: %s' \
                    % str(err))

                LOGGER.debug('Transaction operation: %s' % record)

                if not hasattr(record,
                self.parent.context.md_core_model['mappings']['pycsw:Identifier']):
                    return self.exceptionreport('NoApplicableCode',
                    'insert', 'Record requires an identifier')

                # insert new record
                try:
                    self.parent.repository.insert(record, 'local',
                    util.get_today_and_now())

                    inserted += 1
                    insertresults.append(
                    {'identifier': getattr(record,
                    self.parent.context.md_core_model['mappings']['pycsw:Identifier']),
                    'title': getattr(record,
                    self.parent.context.md_core_model['mappings']['pycsw:Title'])})
                except Exception as err:
                    return self.exceptionreport('NoApplicableCode',
                    'insert', 'Transaction (insert) failed: %s.' % str(err))

            elif ttype['type'] == 'update':
                if 'constraint' not in ttype:
                    # update full existing resource in repository
                    try:
                        record = metadata.parse_record(self.parent.context,
                        ttype['xml'], self.parent.repository)[0]
                        identifier = getattr(record,
                        self.parent.context.md_core_model['mappings']['pycsw:Identifier'])
                    except Exception as err:
                        return self.exceptionreport('NoApplicableCode', 'insert',
                        'Transaction (update) failed: record parsing failed: %s' \
                        % str(err))

                    # query repository to see if record already exists
                    LOGGER.debug('checking if record exists (%s)' % \
                    identifier)

                    results = self.parent.repository.query_ids(ids=[identifier])

                    if len(results) == 0:
                        LOGGER.debug('id %s does not exist in repository' % \
                        identifier)
                    else:  # existing record, it's an update
                        try:
                            self.parent.repository.update(record)
                            updated += 1
                        except Exception as err:
                            return self.exceptionreport('NoApplicableCode',
                            'update',
                            'Transaction (update) failed: %s.' % str(err))
                else:  # update by record property and constraint
                    # get / set XPath for property names
                    for rp in ttype['recordproperty']:
                        if rp['name'] not in self.parent.repository.queryables['_all']:
                            # is it an XPath?
                            if rp['name'].find('/') != -1:
                                # scan outputschemas; if match, bind
                                for osch in self.parent.outputschemas.values():
                                    for key, value in osch.XPATH_MAPPINGS.items():
                                        if value == rp['name']:  # match
                                            rp['rp'] = {'xpath': value, 'name': key}
                                            rp['rp']['dbcol'] = self.parent.repository.queryables['_all'][key]
                                            break
                            else:
                                return self.exceptionreport('NoApplicableCode',
                                       'update', 'Transaction (update) failed: invalid property2: %s.' % str(rp['name']))
                        else:
                            rp['rp']= \
                            self.parent.repository.queryables['_all'][rp['name']]

                    LOGGER.debug('Record Properties: %s.' %
                    ttype['recordproperty'])
                    try:
                        updated += self.parent.repository.update(record=None,
                        recprops=ttype['recordproperty'],
                        constraint=ttype['constraint'])
                    except Exception as err:
                        return self.exceptionreport('NoApplicableCode',
                        'update',
                        'Transaction (update) failed: %s.' % str(err))

            elif ttype['type'] == 'delete':
                deleted += self.parent.repository.delete(ttype['constraint'])

        node = etree.Element(util.nspath_eval('csw30:TransactionResponse',
        self.parent.context.namespaces), nsmap=self.parent.context.namespaces, version='3.0.0')

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.parent.context.namespaces)] = '%s %s/csw/3.0/cswTransaction.xsd' % \
        (self.parent.context.namespaces['csw30'], self.parent.config.get('server', 'ogc_schemas_base'))

        node.append(
        self._write_transactionsummary(
        inserted=inserted, updated=updated, deleted=deleted))

        if (len(insertresults) > 0 and self.parent.kvp['verboseresponse']):
            # show insert result identifiers
            node.append(self._write_verboseresponse(insertresults))

        return node

    def harvest(self):
        ''' Handle Harvest request '''

        service_identifier = None
        old_identifier = None
        deleted = []

        try:
            self.parent._test_manager()
        except Exception as err:
            return self.exceptionreport('NoApplicableCode', 'harvest', str(err))

        if self.parent.requesttype == 'GET':
            if 'resourcetype' not in self.parent.kvp:
                return self.exceptionreport('MissingParameterValue',
                'resourcetype', 'Missing resourcetype parameter')
            if 'source' not in self.parent.kvp:
                return self.exceptionreport('MissingParameterValue',
                'source', 'Missing source parameter')

        # validate resourcetype
        if (self.parent.kvp['resourcetype'] not in
            self.parent.context.model['operations']['Harvest']['parameters']['ResourceType']
            ['values']):
            return self.exceptionreport('InvalidParameterValue',
            'resourcetype', 'Invalid resource type parameter: %s.\
            Allowable resourcetype values: %s' % (self.parent.kvp['resourcetype'],
            ','.join(self.parent.context.model['operations']['Harvest']['parameters']
            ['ResourceType']['values'])))

        if (self.parent.kvp['resourcetype'].find('opengis.net') == -1 and
            self.parent.kvp['resourcetype'].find('urn:geoss:waf') == -1):
            # fetch content-based resource
            LOGGER.debug('Fetching resource %s' % self.parent.kvp['source'])
            try:
                content = util.http_request('GET', self.parent.kvp['source'])
            except Exception as err:
                errortext = 'Error fetching resource %s.\nError: %s.' % \
                (self.parent.kvp['source'], str(err))
                LOGGER.debug(errortext)
                return self.exceptionreport('InvalidParameterValue', 'source',
                errortext)
        else:  # it's a service URL
            content = self.parent.kvp['source']
            # query repository to see if service already exists
            LOGGER.debug('checking if service exists (%s)' % content)
            results = self.parent.repository.query_source(content)

            if len(results) > 0:  # exists, keep identifier for update
                LOGGER.debug('Service already exists, keeping identifier and results')
                service_identifier = getattr(results[0], self.parent.context.md_core_model['mappings']['pycsw:Identifier'])
                service_results = results
                LOGGER.debug('Identifier is %s' % service_identifier)
            #    return self.exceptionreport('NoApplicableCode', 'source',
            #    'Insert failed: service %s already in repository' % content)


        if hasattr(self.parent.repository, 'local_ingest') and self.parent.repository.local_ingest:
            updated = 0
            deleted = []
            try:
                ir = self.parent.repository.insert(self.parent.kvp['resourcetype'], self.parent.kvp['source'])
                inserted = len(ir)
            except Exception as err:
                return self.exceptionreport('NoApplicableCode',
                'source', 'Harvest (insert) failed: %s.' % str(err))
        else:
            # parse resource into record
            try:
                records_parsed = metadata.parse_record(self.parent.context,
                content, self.parent.repository, self.parent.kvp['resourcetype'],
                pagesize=self.parent.csw_harvest_pagesize)
            except Exception as err:
                LOGGER.exception(err)
                return self.exceptionreport('NoApplicableCode', 'source',
                'Harvest failed: record parsing failed: %s' % str(err))

            inserted = 0
            updated = 0
            ir = []

            LOGGER.debug('Total Records parsed: %d' % len(records_parsed))
            for record in records_parsed:
                if self.parent.kvp['resourcetype'] == 'urn:geoss:waf':
                    src = record.source
                else:
                    src = self.parent.kvp['source']

                setattr(record, self.parent.context.md_core_model['mappings']['pycsw:Source'],
                        src)

                setattr(record, self.parent.context.md_core_model['mappings']['pycsw:InsertDate'],
                util.get_today_and_now())

                identifier = getattr(record,
                self.parent.context.md_core_model['mappings']['pycsw:Identifier'])
                source = getattr(record,
                self.parent.context.md_core_model['mappings']['pycsw:Source'])
                insert_date = getattr(record,
                self.parent.context.md_core_model['mappings']['pycsw:InsertDate'])
                title = getattr(record,
                self.parent.context.md_core_model['mappings']['pycsw:Title'])

                record_type = getattr(record, self.parent.context.md_core_model['mappings']['pycsw:Type'])

                record_identifier = getattr(record, self.parent.context.md_core_model['mappings']['pycsw:Identifier'])

                if record_type == 'service' and service_identifier is not None:  # service endpoint
                    LOGGER.debug('Replacing service identifier from %s to %s' % (record_identifier, service_identifier))
                    old_identifier = record_identifier
                    identifier = record_identifier = service_identifier
                if (record_type != 'service' and service_identifier is not None
                    and old_identifier is not None):  # service resource
                    if record_identifier.find(old_identifier) != -1:
                        new_identifier = record_identifier.replace(old_identifier, service_identifier)
                        LOGGER.debug('Replacing service resource identifier from %s to %s' % (record_identifier, new_identifier))
                        identifier = record_identifier = new_identifier

                ir.append({'identifier': identifier, 'title': title})

                results = []
                if not self.parent.config.has_option('repository', 'source'):
                    # query repository to see if record already exists
                    LOGGER.debug('checking if record exists (%s)' % identifier)
                    results = self.parent.repository.query_ids(ids=[identifier])

                    if len(results) == 0:  # check for service identifier
                        LOGGER.debug('checking if service id exists (%s)' % service_identifier)
                        results = self.parent.repository.query_ids(ids=[service_identifier])

                LOGGER.debug(str(results))

                if len(results) == 0:  # new record, it's a new insert
                    inserted += 1
                    try:
                        tmp = self.parent.repository.insert(record, source, insert_date)
                        if tmp is not None: ir = tmp
                    except Exception as err:
                        return self.exceptionreport('NoApplicableCode',
                        'source', 'Harvest (insert) failed: %s.' % str(err))
                else:  # existing record, it's an update
                    if source != results[0].source:
                        # same identifier, but different source
                        return self.exceptionreport('NoApplicableCode',
                        'source', 'Insert failed: identifier %s in repository\
                        has source %s.' % (identifier, source))

                    try:
                        self.parent.repository.update(record)
                    except Exception as err:
                        return self.exceptionreport('NoApplicableCode',
                        'source', 'Harvest (update) failed: %s.' % str(err))
                    updated += 1

            if service_identifier is not None:
                fresh_records = [str(i['identifier']) for i in ir]
                existing_records = [str(i.identifier) for i in service_results]

                deleted = set(existing_records) - set(fresh_records)
                LOGGER.debug('Records to delete: %s' % str(deleted))

                for to_delete in deleted:
                    delete_constraint = {
                        'type': 'filter',
                        'values': [to_delete],
                        'where': 'identifier = :pvalue0'
                    }
                    self.parent.repository.delete(delete_constraint)

        node = etree.Element(util.nspath_eval('csw:HarvestResponse',
        self.parent.context.namespaces), nsmap=self.parent.context.namespaces)

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.parent.context.namespaces)] = \
        '%s %s/csw/2.0.2/CSW-publication.xsd' % (self.parent.context.namespaces['csw'],
        self.parent.config.get('server', 'ogc_schemas_base'))

        node2 = etree.SubElement(node,
        util.nspath_eval('csw:TransactionResponse',
        self.parent.context.namespaces), version='2.0.2')

        node2.append(
        self._write_transactionsummary(inserted=len(ir), updated=updated,
                                       deleted=len(deleted)))

        if inserted > 0:
            # show insert result identifiers
            node2.append(self._write_verboseresponse(ir))

        if 'responsehandler' in self.parent.kvp:  # process the handler
            self.parent._process_responsehandler(etree.tostring(node,
            pretty_print=self.parent.pretty_print))
        else:
            return node

    def _write_record(self, recobj, queryables):
        ''' Generate csw30:Record '''
        if self.parent.kvp['elementsetname'] == 'brief':
            elname = 'BriefRecord'
        elif self.parent.kvp['elementsetname'] == 'summary':
            elname = 'SummaryRecord'
        else:
            elname = 'Record'

        record = etree.Element(util.nspath_eval('csw30:%s' % elname,
                 self.parent.context.namespaces), nsmap=self.parent.context.namespaces)

        if ('elementname' in self.parent.kvp and
            len(self.parent.kvp['elementname']) > 0):
            for req_term in ['dc:identifier', 'dc:title']:
                if req_term not in self.parent.kvp['elementname']:
                    value = util.getqattr(recobj, queryables[req_term]['dbcol'])
                    etree.SubElement(record,
                    util.nspath_eval(req_term,
                    self.parent.context.namespaces)).text = value
            for elemname in self.parent.kvp['elementname']:
                if (elemname.find('BoundingBox') != -1 or
                    elemname.find('Envelope') != -1):
                    bboxel = write_boundingbox(util.getqattr(recobj,
                    self.parent.context.md_core_model['mappings']['pycsw:BoundingBox']),
                    self.parent.context.namespaces)
                    if bboxel is not None:
                        record.append(bboxel)
                else:
                    value = util.getqattr(recobj, queryables[elemname]['dbcol'])
                    elem = etree.SubElement(record,
                           util.nspath_eval(elemname,
                           self.parent.context.namespaces))
                    if value:
                        elem.text = value
        elif 'elementsetname' in self.parent.kvp:
            if (self.parent.kvp['elementsetname'] == 'full' and
            util.getqattr(recobj, self.parent.context.md_core_model['mappings']\
            ['pycsw:Typename']) == 'csw:Record' and
            util.getqattr(recobj, self.parent.context.md_core_model['mappings']\
            ['pycsw:Schema']) == 'http://www.opengis.net/cat/csw/3.0' and
            util.getqattr(recobj, self.parent.context.md_core_model['mappings']\
            ['pycsw:Type']) != 'service'):
                # dump record as is and exit
                return etree.fromstring(util.getqattr(recobj,
                self.parent.context.md_core_model['mappings']['pycsw:XML']), self.parent.context.parser)

            etree.SubElement(record,
            util.nspath_eval('dc:identifier', self.parent.context.namespaces)).text = \
            util.getqattr(recobj,
            self.parent.context.md_core_model['mappings']['pycsw:Identifier'])

            for i in ['dc:title', 'dc:type']:
                val = util.getqattr(recobj, queryables[i]['dbcol'])
                if not val:
                    val = ''
                etree.SubElement(record, util.nspath_eval(i,
                self.parent.context.namespaces)).text = val

            if self.parent.kvp['elementsetname'] in ['summary', 'full']:
                # add summary elements
                keywords = util.getqattr(recobj, queryables['dc:subject']['dbcol'])
                if keywords is not None:
                    for keyword in keywords.split(','):
                        etree.SubElement(record,
                        util.nspath_eval('dc:subject',
                        self.parent.context.namespaces)).text = keyword

                val = util.getqattr(recobj, self.parent.context.md_core_model['mappings']['pycsw:TopicCategory'])
                if val:
                    etree.SubElement(record,
                    util.nspath_eval('dc:subject',
                    self.parent.context.namespaces), scheme='http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_TopicCategoryCode').text = val

                val = util.getqattr(recobj, queryables['dc:format']['dbcol'])
                if val:
                    etree.SubElement(record,
                    util.nspath_eval('dc:format',
                    self.parent.context.namespaces)).text = val

                # links
                rlinks = util.getqattr(recobj,
                self.parent.context.md_core_model['mappings']['pycsw:Links'])

                if rlinks:
                    links = rlinks.split('^')
                    for link in links:
                        linkset = link.split(',')
                        etree.SubElement(record,
                        util.nspath_eval('dct:references',
                        self.parent.context.namespaces),
                        scheme=linkset[2]).text = linkset[-1]

                for i in ['dc:relation', 'dct:modified', 'dct:abstract']:
                    val = util.getqattr(recobj, queryables[i]['dbcol'])
                    if val is not None:
                        etree.SubElement(record,
                        util.nspath_eval(i, self.parent.context.namespaces)).text = val

            if self.parent.kvp['elementsetname'] == 'full':  # add full elements
                for i in ['dc:date', 'dc:creator', \
                'dc:publisher', 'dc:contributor', 'dc:source', \
                'dc:language', 'dc:rights']:
                    val = util.getqattr(recobj, queryables[i]['dbcol'])
                    if val:
                        etree.SubElement(record,
                        util.nspath_eval(i, self.parent.context.namespaces)).text = val

            # always write out ows:BoundingBox
            bboxel = write_boundingbox(getattr(recobj,
            self.parent.context.md_core_model['mappings']['pycsw:BoundingBox']),
            self.parent.context.namespaces)

            if bboxel is not None:
                record.append(bboxel)

            if self.parent.kvp['elementsetname'] != 'brief':  # add temporal extent
                begin = util.getqattr(record, self.parent.context.md_core_model['mappings']['pycsw:TempExtent_begin'])
                end = util.getqattr(record, self.parent.context.md_core_model['mappings']['pycsw:TempExtent_end'])

                if begin or end:
                    tempext = etree.SubElement(record, util.nspath_eval('csw30:TemporalExtent', self.parent.context.namespaces))
                    if begin:
                        etree.SubElement(record, util.nspath_eval('csw30:begin', self.parent.context.namespaces)).text = begin
                    if end:
                        etree.SubElement(record, util.nspath_eval('csw30:end', self.parent.context.namespaces)).text = end

        return record

    def _parse_constraint(self, element):
        ''' Parse csw:Constraint '''

        query = {}

        tmp = element.find(util.nspath_eval('fes20:Filter', self.parent.context.namespaces))
        if tmp is not None:
            LOGGER.debug('Filter constraint specified.')
            try:
                query['type'] = 'filter'
                query['where'], query['values'] = fes2.parse(tmp,
                self.parent.repository.queryables['_all'], self.parent.repository.dbtype,
                self.parent.context.namespaces, self.parent.orm, self.parent.language['text'], self.parent.repository.fts)
            except Exception as err:
                return 'Invalid Filter request: %s' % err
        tmp = element.find(util.nspath_eval('csw30:CqlText', self.parent.context.namespaces))
        if tmp is not None:
            LOGGER.debug('CQL specified: %s.' % tmp.text)
            query['type'] = 'cql'
            query['where'] = self.parent._cql_update_queryables_mappings(tmp.text,
            self.parent.repository.queryables['_all'])
            query['values'] = {}
        return query

    def parse_postdata(self, postdata):
        ''' Parse POST XML '''

        request = {}
        try:
            LOGGER.debug('Parsing %s.' % postdata)
            doc = etree.fromstring(postdata, self.parent.context.parser)
        except Exception as err:
            errortext = \
            'Exception: document not well-formed.\nError: %s.' % str(err)

            LOGGER.debug(errortext)
            return errortext

        # if this is a SOAP request, get to SOAP-ENV:Body/csw:*
        if (doc.tag == util.nspath_eval('soapenv:Envelope',
            self.parent.context.namespaces)):

            LOGGER.debug('SOAP request specified.')
            self.parent.soap = True

            doc = doc.find(
            util.nspath_eval('soapenv:Body',
            self.parent.context.namespaces)).xpath('child::*')[0]

        xsd_filename = 'csw%s.xsd' % util.xmltag_split(doc.tag)
        schema = os.path.join(self.parent.config.get('server', 'home'),
        'core', 'schemas', 'ogc', 'csw', '3.0', xsd_filename)

        try:
            # it is virtually impossible to validate a csw:Transaction
            # csw:Insert|csw:Update (with single child) XML document.
            # Only validate non csw:Transaction XML

            if doc.find('.//%s' % util.nspath_eval('csw30:Insert',
            self.parent.context.namespaces)) is None and \
            len(doc.xpath('//csw30:Update/child::*',
            namespaces=self.parent.context.namespaces)) == 0:

                LOGGER.debug('Validating %s.' % postdata)
                schema = etree.XMLSchema(file=schema)
                parser = etree.XMLParser(schema=schema, resolve_entities=False)
                if hasattr(self.parent, 'soap') and self.parent.soap:
                # validate the body of the SOAP request
                    doc = etree.fromstring(etree.tostring(doc), parser)
                else:  # validate the request normally
                    doc = etree.fromstring(postdata, parser)
                LOGGER.debug('Request is valid XML.')
            else:  # parse Transaction without validation
                doc = etree.fromstring(postdata, self.parent.context.parser)
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

        tmp = doc.find('.//%s' % util.nspath_eval('ows20:Version',
        self.parent.context.namespaces))

        if tmp is not None:
            request['version'] = tmp.text

        tmp = doc.find('.').attrib.get('updateSequence')
        if tmp is not None:
            request['updatesequence'] = tmp

        # GetCapabilities
        if request['request'] == 'GetCapabilities':
            tmp = doc.find(util.nspath_eval('ows20:Sections',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['sections'] = ','.join([section.text for section in \
                doc.findall(util.nspath_eval('ows20:Sections/ows20:Section',
                self.parent.context.namespaces))])

            tmp = doc.find(util.nspath_eval('ows20:AcceptFormats',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['acceptformats'] = ','.join([aformat.text for aformat in \
                doc.findall(util.nspath_eval('ows20:AcceptFormats/ows20:OutputFormat',
                self.parent.context.namespaces))])

            tmp = doc.find(util.nspath_eval('ows20:AcceptVersions',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['acceptversions'] = ','.join([version.text for version in \
                doc.findall(util.nspath_eval('ows20:AcceptVersions/ows20:Version',
                self.parent.context.namespaces))])

        # GetDomain
        if request['request'] == 'GetDomain':
            tmp = doc.find(util.nspath_eval('csw30:ParameterName',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['parametername'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw30:ValueReference',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['valuereference'] = tmp.text

        # GetRecords
        if request['request'] == 'GetRecords':
            tmp = doc.find('.').attrib.get('outputSchema')
            request['outputschema'] = tmp if tmp is not None \
            else self.parent.context.namespaces['csw30']

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

            tmp = doc.find(util.nspath_eval('csw30:DistributedSearch',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['distributedsearch'] = True
                hopcount = tmp.attrib.get('hopCount')
                request['hopcount'] = int(hopcount)-1 if hopcount is not None \
                else 1
            else:
                request['distributedsearch'] = False

            tmp = doc.find(util.nspath_eval('csw30:ResponseHandler',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['responsehandler'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw30:Query/csw30:ElementSetName',
                  self.parent.context.namespaces))
            request['elementsetname'] = tmp.text if tmp is not None else None

            tmp = doc.find(util.nspath_eval(
            'csw30:Query', self.parent.context.namespaces)).attrib.get('typeNames')
            request['typenames'] = tmp.split() if tmp is not None \
            else 'csw:Record'

            request['elementname'] = [elname.text for elname in \
            doc.findall(util.nspath_eval('csw30:Query/csw30:ElementName',
            self.parent.context.namespaces))]

            request['constraint'] = {}
            tmp = doc.find(util.nspath_eval('csw30:Query/csw30:Constraint',
            self.parent.context.namespaces))

            if tmp is not None:
                request['constraint'] = self._parse_constraint(tmp)
                if isinstance(request['constraint'], str):  # parse error
                    return 'Invalid Constraint: %s' % request['constraint']
            else:
                LOGGER.debug('No csw30:Constraint (fes20:Filter or csw30:CqlText) \
                specified.')

            tmp = doc.find(util.nspath_eval('csw30:Query/fes20:SortBy',
                  self.parent.context.namespaces))
            if tmp is not None:
                LOGGER.debug('Sorted query specified.')
                request['sortby'] = {}


                try:
                    elname = tmp.find(util.nspath_eval(
                    'fes20:SortProperty/fes20:ValueReference',
                    self.parent.context.namespaces)).text

                    request['sortby']['propertyname'] = \
                    self.parent.repository.queryables['_all'][elname]['dbcol']

                    if (elname.find('BoundingBox') != -1 or
                        elname.find('Envelope') != -1):
                        # it's a spatial sort
                        request['sortby']['spatial'] = True
                except Exception as err:
                    errortext = \
                    'Invalid fes20:SortProperty/fes20:ValueReference: %s' % str(err)
                    LOGGER.debug(errortext)
                    return errortext

                tmp2 =  tmp.find(util.nspath_eval(
                'fes20:SortProperty/fes20:SortOrder', self.parent.context.namespaces))
                request['sortby']['order'] = tmp2.text if tmp2 is not None \
                else 'ASC'
            else:
                request['sortby'] = None

        # GetRecordById
        if request['request'] == 'GetRecordById':
            request['id'] = None
            tmp = doc.find(util.nspath_eval('csw30:Id', self.parent.context.namespaces))
            if tmp is not None:
                request['id'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw30:ElementSetName',
                  self.parent.context.namespaces))
            request['elementsetname'] = tmp.text if tmp is not None \
            else 'summary'

            tmp = doc.find('.').attrib.get('outputSchema')
            request['outputschema'] = tmp if tmp is not None \
            else self.parent.context.namespaces['csw30']

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
            doc.xpath('//csw30:Insert', namespaces=self.parent.context.namespaces):
                tname = ttype.attrib.get('typeName')

                for mdrec in ttype.xpath('child::*'):
                    xml = mdrec
                    request['transactions'].append(
                    {'type': 'insert', 'typename': tname, 'xml': xml})

            for ttype in \
            doc.xpath('//csw30:Update', namespaces=self.parent.context.namespaces):
                child = ttype.xpath('child::*')
                update = {'type': 'update'}

                if len(child) == 1:  # it's a wholesale update
                    update['xml'] = child[0]
                else:  # it's a RecordProperty with Constraint Update
                    update['recordproperty'] = []

                    for recprop in ttype.findall(
                    util.nspath_eval('csw:RecordProperty',
                        self.parent.context.namespaces)):
                        rpname = recprop.find(util.nspath_eval('csw30:Name',
                        self.parent.context.namespaces)).text
                        rpvalue = recprop.find(
                        util.nspath_eval('csw30:Value',
                        self.parent.context.namespaces)).text

                        update['recordproperty'].append(
                        {'name': rpname, 'value': rpvalue})

                    update['constraint'] = self._parse_constraint(
                    ttype.find(util.nspath_eval('csw30:Constraint',
                    self.parent.context.namespaces)))

                request['transactions'].append(update)

            for ttype in \
            doc.xpath('//csw30:Delete', namespaces=self.parent.context.namespaces):
                tname = ttype.attrib.get('typeName')
                constraint = self._parse_constraint(
                ttype.find(util.nspath_eval('csw30:Constraint',
                self.parent.context.namespaces)))

                if isinstance(constraint, str):  # parse error
                    return 'Invalid Constraint: %s' % constraint

                request['transactions'].append(
                {'type': 'delete', 'typename': tname, 'constraint': constraint})

        # Harvest
        if request['request'] == 'Harvest':
            request['source'] = doc.find(util.nspath_eval('csw30:Source',
            self.parent.context.namespaces)).text

            request['resourcetype'] = \
            doc.find(util.nspath_eval('csw30:ResourceType',
            self.parent.context.namespaces)).text

            tmp = doc.find(util.nspath_eval('csw30:ResourceFormat',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['resourceformat'] = tmp.text
            else:
                request['resourceformat'] = 'application/xml'

            tmp = doc.find(util.nspath_eval('csw30:HarvestInterval',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['harvestinterval'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw30:ResponseHandler',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['responsehandler'] = tmp.text
        return request

    def _write_transactionsummary(self, inserted=0, updated=0, deleted=0):
        ''' Write csw:TransactionSummary construct '''
        node = etree.Element(util.nspath_eval('csw30:TransactionSummary',
               self.parent.context.namespaces))

        if 'requestid' in self.parent.kvp and self.parent.kvp['requestid'] is not None:
            node.attrib['requestId'] = self.parent.kvp['requestid']

        etree.SubElement(node, util.nspath_eval('csw30:totalInserted',
        self.parent.context.namespaces)).text = str(inserted)

        etree.SubElement(node, util.nspath_eval('csw30:totalUpdated',
        self.parent.context.namespaces)).text = str(updated)

        etree.SubElement(node, util.nspath_eval('csw30:totalDeleted',
        self.parent.context.namespaces)).text = str(deleted)

        return node

    def _write_acknowledgement(self, root=True):
        ''' Generate csw:Acknowledgement '''
        node = etree.Element(util.nspath_eval('csw30:Acknowledgement',
               self.parent.context.namespaces),
        nsmap = self.parent.context.namespaces, timeStamp=util.get_today_and_now())

        if root:
            node.attrib[util.nspath_eval('xsi:schemaLocation',
            self.parent.context.namespaces)] = \
            '%s %s/csw/3.0/cswAll.xsd' % (self.parent.context.namespaces['csw30'], \
            self.parent.config.get('server', 'ogc_schemas_base'))

        node1 = etree.SubElement(node, util.nspath_eval('csw30:EchoedRequest',
                self.parent.context.namespaces))
        if self.parent.requesttype == 'POST':
            node1.append(etree.fromstring(self.parent.request, self.parent.context.parser))
        else:  # GET
            node2 = etree.SubElement(node1, util.nspath_eval('ows:Get',
                    self.parent.context.namespaces))

            node2.text = self.parent.request

        if self.parent.async:
            etree.SubElement(node, util.nspath_eval('csw30:RequestId',
            self.parent.context.namespaces)).text = self.parent.kvp['requestid']

        return node

    def _write_verboseresponse(self, insertresults):
        ''' show insert result identifiers '''
        insertresult = etree.Element(util.nspath_eval('csw30:InsertResult',
        self.parent.context.namespaces))
        for ir in insertresults:
            briefrec = etree.SubElement(insertresult,
                       util.nspath_eval('csw30:BriefRecord',
                       self.parent.context.namespaces))

            etree.SubElement(briefrec,
            util.nspath_eval('dc:identifier',
            self.parent.context.namespaces)).text = ir['identifier']

            etree.SubElement(briefrec,
            util.nspath_eval('dc:title',
            self.parent.context.namespaces)).text = ir['title']

        return insertresult

    def _write_allowed_values(self, values):
        ''' design pattern to write ows20:AllowedValues '''

        allowed_values = etree.Element(util.nspath_eval('ows20:AllowedValues',
                                       self.parent.context.namespaces))

        for value in sorted(values):
            etree.SubElement(allowed_values,
                             util.nspath_eval('ows20:Value',
                             self.parent.context.namespaces)).text = value
        return allowed_values

    def exceptionreport(self, code, locator, text):
        ''' Generate ExceptionReport '''
        self.parent.exception = True
        self.parent.status = code

        try:
            language = self.parent.config.get('server', 'language')
            ogc_schemas_base = self.parent.config.get('server', 'ogc_schemas_base')
        except:
            language = 'en-US'
            ogc_schemas_base = self.parent.context.ogc_schemas_base

        node = etree.Element(util.nspath_eval('ows20:ExceptionReport',
        self.parent.context.namespaces), nsmap=self.parent.context.namespaces,
        version='3.0.0')

        node.attrib['{http://www.w3.org/XML/1998/namespace}lang'] = language

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.parent.context.namespaces)] = \
        '%s %s/ows/2.0/owsExceptionReport.xsd' % \
        (self.parent.context.namespaces['ows20'], ogc_schemas_base)

        exception = etree.SubElement(node, util.nspath_eval('ows20:Exception',
        self.parent.context.namespaces),
        exceptionCode=code, locator=locator)

        etree.SubElement(exception,
        util.nspath_eval('ows20:ExceptionText',
        self.parent.context.namespaces)).text = text

        return node

    def resolve_nsmap(self, list_):
        '''' Resolve typename bindings based on default and KVP namespaces '''

        nsmap = {}

        tns = []

        LOGGER.debug('Namespace list pairs: %s', list_)

        # bind KVP namespaces into typenames
        for ns in self.parent.kvp['namespace'].split(','):
            nspair = ns.split('(')[1].split(')')[0].split('=')
            if len(nspair) == 1:  # default namespace
                nsmap['csw'] = nspair[1]
            else:
                nsmap[nspair[0]] = nspair[1]

        LOGGER.debug('Namespace pairs: %s', nsmap)

        for tn in list_:
            LOGGER.debug(tn)
            if tn.find(':') != -1:  # resolve prefix
                prefix = tn.split(':')[0]
                if prefix in nsmap.keys():  # get uri
                    uri = nsmap[prefix]
                    newprefix = next(k for k, v in self.parent.context.namespaces.items() if v == uri)
                    LOGGER.debug(uri)
                    LOGGER.debug(prefix)
                    LOGGER.debug(newprefix)
                    #if prefix == 'csw30': newprefix = 'csw'
                    newvalue = tn.replace(prefix, newprefix).replace('csw30', 'csw')
                else:
                    newvalue = tn
            else:  # default namespace
                newvalue = tn

            tns.append(newvalue)


        LOGGER.debug(tns)
        return tns

def write_boundingbox(bbox, nsmap):
    ''' Generate ows20:BoundingBox '''

    if bbox is not None:
        try:
            bbox2 = util.wkt2geom(bbox)
        except:
            return None

        if len(bbox2) == 4:
            boundingbox = etree.Element(util.nspath_eval('ows20:BoundingBox',
            nsmap), crs='http://www.opengis.net/def/crs/EPSG/0/4326',
            dimensions='2')

            etree.SubElement(boundingbox, util.nspath_eval('ows20:LowerCorner',
            nsmap)).text = '%s %s' % (bbox2[1], bbox2[0])

            etree.SubElement(boundingbox, util.nspath_eval('ows20:UpperCorner',
            nsmap)).text = '%s %s' % (bbox2[3], bbox2[2])

            return boundingbox
        else:
            return None
    else:
        return None
        if nextrecord == 0:
            searchresult_status = 'complete'
        elif nextrecord > 0:
            searchresult_status = 'subset'
        elif matched == 0:
            searchresult_status = 'none'

def get_resultset_status(matched, nextrecord):
    ''' Helper function to assess status of a result set '''

    status = 'subset'  # default

    if nextrecord == 0:
        status = 'complete'
    elif matched == 0:
       status = 'none'

    return status
