# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2016 Tom Kralidis
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
from six.moves.urllib.parse import quote, unquote
from six import StringIO
from six.moves.configparser import SafeConfigParser
from pycsw.core.etree import etree
from pycsw import oaipmh, opensearch, sru
from pycsw.ogc.csw.cql import cql2fes1
from pycsw.plugins.profiles import profile as pprofile
import pycsw.plugins.outputschemas
from pycsw.core import config, log, metadata, util
from pycsw.core.formats.fmt_json import xml2dict
from pycsw.ogc.fes import fes1
import logging

LOGGER = logging.getLogger(__name__)


class Csw2(object):
    ''' CSW 2.x server '''
    def __init__(self, server_csw):
        ''' Initialize CSW2 '''

        self.parent = server_csw
        self.version = '2.0.2'

    def getcapabilities(self):
        ''' Handle GetCapabilities request '''
        serviceidentification = True
        serviceprovider = True
        operationsmetadata = True
        if 'sections' in self.parent.kvp:
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

        node = etree.Element(util.nspath_eval('csw:Capabilities',
        self.parent.context.namespaces),
        nsmap=self.parent.context.namespaces, version='2.0.2',
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
        self.parent.context.namespaces)] = '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (self.parent.context.namespaces['csw'],
         self.parent.config.get('server', 'ogc_schemas_base'))

        metadata_main = dict(self.parent.config.items('metadata:main'))

        if serviceidentification:
            LOGGER.info('Writing section ServiceIdentification')

            serviceidentification = etree.SubElement(node, \
            util.nspath_eval('ows:ServiceIdentification',
            self.parent.context.namespaces))

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Title', self.parent.context.namespaces)).text = \
            metadata_main.get('identification_title', 'missing')

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Abstract', self.parent.context.namespaces)).text = \
            metadata_main.get('identification_abstract', 'missing')

            keywords = etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Keywords', self.parent.context.namespaces))

            for k in \
            metadata_main.get('identification_keywords').split(','):
                etree.SubElement(
                keywords, util.nspath_eval('ows:Keyword',
                self.parent.context.namespaces)).text = k

            etree.SubElement(keywords,
            util.nspath_eval('ows:Type', self.parent.context.namespaces),
            codeSpace='ISOTC211/19115').text = \
            metadata_main.get('identification_keywords_type', 'missing')

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:ServiceType', self.parent.context.namespaces),
            codeSpace='OGC').text = 'CSW'

            for stv in self.parent.context.model['parameters']['version']['values']:
                etree.SubElement(serviceidentification,
                util.nspath_eval('ows:ServiceTypeVersion',
                self.parent.context.namespaces)).text = stv

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:Fees', self.parent.context.namespaces)).text = \
            metadata_main.get('identification_fees', 'missing')

            etree.SubElement(serviceidentification,
            util.nspath_eval('ows:AccessConstraints',
            self.parent.context.namespaces)).text = \
            metadata_main.get('identification_accessconstraints', 'missing')

        if serviceprovider:
            LOGGER.info('Writing section ServiceProvider')
            serviceprovider = etree.SubElement(node,
            util.nspath_eval('ows:ServiceProvider', self.parent.context.namespaces))

            etree.SubElement(serviceprovider,
            util.nspath_eval('ows:ProviderName', self.parent.context.namespaces)).text = \
            metadata_main.get('provider_name', 'missing')

            providersite = etree.SubElement(serviceprovider,
            util.nspath_eval('ows:ProviderSite', self.parent.context.namespaces))

            providersite.attrib[util.nspath_eval('xlink:type',
            self.parent.context.namespaces)] = 'simple'

            providersite.attrib[util.nspath_eval('xlink:href',
            self.parent.context.namespaces)] = \
            metadata_main.get('provider_url', 'missing')

            servicecontact = etree.SubElement(serviceprovider,
            util.nspath_eval('ows:ServiceContact', self.parent.context.namespaces))

            etree.SubElement(servicecontact,
            util.nspath_eval('ows:IndividualName',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_name', 'missing')

            etree.SubElement(servicecontact,
            util.nspath_eval('ows:PositionName',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_position', 'missing')

            contactinfo = etree.SubElement(servicecontact,
            util.nspath_eval('ows:ContactInfo', self.parent.context.namespaces))

            phone = etree.SubElement(contactinfo, util.nspath_eval('ows:Phone',
            self.parent.context.namespaces))

            etree.SubElement(phone, util.nspath_eval('ows:Voice',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_phone', 'missing')

            etree.SubElement(phone, util.nspath_eval('ows:Facsimile',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_fax', 'missing')

            address = etree.SubElement(contactinfo,
            util.nspath_eval('ows:Address', self.parent.context.namespaces))

            etree.SubElement(address,
            util.nspath_eval('ows:DeliveryPoint',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_address', 'missing')

            etree.SubElement(address, util.nspath_eval('ows:City',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_city', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows:AdministrativeArea',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_stateorprovince', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows:PostalCode',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_postalcode', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows:Country', self.parent.context.namespaces)).text = \
            metadata_main.get('contact_country', 'missing')

            etree.SubElement(address,
            util.nspath_eval('ows:ElectronicMailAddress',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_email', 'missing')

            url = etree.SubElement(contactinfo,
            util.nspath_eval('ows:OnlineResource', self.parent.context.namespaces))

            url.attrib[util.nspath_eval('xlink:type',
            self.parent.context.namespaces)] = 'simple'

            url.attrib[util.nspath_eval('xlink:href',
            self.parent.context.namespaces)] = \
            metadata_main.get('contact_url', 'missing')

            etree.SubElement(contactinfo,
            util.nspath_eval('ows:HoursOfService',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_hours', 'missing')

            etree.SubElement(contactinfo,
            util.nspath_eval('ows:ContactInstructions',
            self.parent.context.namespaces)).text = \
            metadata_main.get('contact_instructions', 'missing')

            etree.SubElement(servicecontact,
            util.nspath_eval('ows:Role', self.parent.context.namespaces),
            codeSpace='ISOTC211/19115').text = \
            metadata_main.get('contact_role', 'missing')

        if operationsmetadata:
            LOGGER.info('Writing section OperationsMetadata')
            operationsmetadata = etree.SubElement(node,
            util.nspath_eval('ows:OperationsMetadata',
            self.parent.context.namespaces))

            for operation in self.parent.context.model['operations_order']:
                oper = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows:Operation', self.parent.context.namespaces),
                name=operation)

                dcp = etree.SubElement(oper, util.nspath_eval('ows:DCP',
                self.parent.context.namespaces))

                http = etree.SubElement(dcp, util.nspath_eval('ows:HTTP',
                self.parent.context.namespaces))

                if self.parent.context.model['operations'][operation]['methods']['get']:
                    get = etree.SubElement(http, util.nspath_eval('ows:Get',
                    self.parent.context.namespaces))

                    get.attrib[util.nspath_eval('xlink:type',\
                    self.parent.context.namespaces)] = 'simple'

                    get.attrib[util.nspath_eval('xlink:href',\
                    self.parent.context.namespaces)] = self.parent.config.get('server', 'url')

                if self.parent.context.model['operations'][operation]['methods']['post']:
                    post = etree.SubElement(http, util.nspath_eval('ows:Post',
                    self.parent.context.namespaces))
                    post.attrib[util.nspath_eval('xlink:type',
                    self.parent.context.namespaces)] = 'simple'
                    post.attrib[util.nspath_eval('xlink:href',
                    self.parent.context.namespaces)] = \
                    self.parent.config.get('server', 'url')

                for parameter in \
                sorted(self.parent.context.model['operations'][operation]['parameters']):
                    param = etree.SubElement(oper,
                    util.nspath_eval('ows:Parameter',
                    self.parent.context.namespaces), name=parameter)

                    for val in \
                    sorted(self.parent.context.model['operations'][operation]\
                    ['parameters'][parameter]['values']):
                        etree.SubElement(param,
                        util.nspath_eval('ows:Value',
                        self.parent.context.namespaces)).text = val

                if operation == 'GetRecords':  # advertise queryables
                    for qbl in sorted(self.parent.repository.queryables.keys()):
                        if qbl != '_all':
                            param = etree.SubElement(oper,
                            util.nspath_eval('ows:Constraint',
                            self.parent.context.namespaces), name=qbl)

                            for qbl2 in sorted(self.parent.repository.queryables[qbl]):
                                etree.SubElement(param,
                                util.nspath_eval('ows:Value',
                                self.parent.context.namespaces)).text = qbl2

                    if self.parent.profiles is not None:
                        for con in sorted(self.parent.context.model[\
                        'operations']['GetRecords']['constraints'].keys()):
                            param = etree.SubElement(oper,
                            util.nspath_eval('ows:Constraint',
                            self.parent.context.namespaces), name = con)
                            for val in self.parent.context.model['operations']\
                            ['GetRecords']['constraints'][con]['values']:
                                etree.SubElement(param,
                                util.nspath_eval('ows:Value',
                                self.parent.context.namespaces)).text = val

            for parameter in sorted(self.parent.context.model['parameters'].keys()):
                param = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows:Parameter', self.parent.context.namespaces),
                name=parameter)

                for val in self.parent.context.model['parameters'][parameter]['values']:
                    etree.SubElement(param, util.nspath_eval('ows:Value',
                    self.parent.context.namespaces)).text = val

            for constraint in sorted(self.parent.context.model['constraints'].keys()):
                param = etree.SubElement(operationsmetadata,
                util.nspath_eval('ows:Constraint', self.parent.context.namespaces),
                name=constraint)

                for val in self.parent.context.model['constraints'][constraint]['values']:
                    etree.SubElement(param, util.nspath_eval('ows:Value',
                    self.parent.context.namespaces)).text = val

            if self.parent.profiles is not None:
                for prof in self.parent.profiles['loaded'].keys():
                    ecnode = \
                    self.parent.profiles['loaded'][prof].get_extendedcapabilities()
                    if ecnode is not None:
                        operationsmetadata.append(ecnode)

        # always write out Filter_Capabilities
        LOGGER.info('Writing section Filter_Capabilities')
        fltcaps = etree.SubElement(node,
        util.nspath_eval('ogc:Filter_Capabilities', self.parent.context.namespaces))

        spatialcaps = etree.SubElement(fltcaps,
        util.nspath_eval('ogc:Spatial_Capabilities', self.parent.context.namespaces))

        geomops = etree.SubElement(spatialcaps,
        util.nspath_eval('ogc:GeometryOperands', self.parent.context.namespaces))

        for geomtype in \
        fes1.MODEL['GeometryOperands']['values']:
            etree.SubElement(geomops,
            util.nspath_eval('ogc:GeometryOperand',
            self.parent.context.namespaces)).text = geomtype

        spatialops = etree.SubElement(spatialcaps,
        util.nspath_eval('ogc:SpatialOperators', self.parent.context.namespaces))

        for spatial_comparison in \
        fes1.MODEL['SpatialOperators']['values']:
            etree.SubElement(spatialops,
            util.nspath_eval('ogc:SpatialOperator', self.parent.context.namespaces),
            name=spatial_comparison)

        scalarcaps = etree.SubElement(fltcaps,
        util.nspath_eval('ogc:Scalar_Capabilities', self.parent.context.namespaces))

        etree.SubElement(scalarcaps, util.nspath_eval('ogc:LogicalOperators',
        self.parent.context.namespaces))

        cmpops = etree.SubElement(scalarcaps,
        util.nspath_eval('ogc:ComparisonOperators', self.parent.context.namespaces))

        for cmpop in sorted(fes1.MODEL['ComparisonOperators'].keys()):
            etree.SubElement(cmpops,
            util.nspath_eval('ogc:ComparisonOperator',
            self.parent.context.namespaces)).text = \
            fes1.MODEL['ComparisonOperators'][cmpop]['opname']

        arithops = etree.SubElement(scalarcaps,
        util.nspath_eval('ogc:ArithmeticOperators', self.parent.context.namespaces))

        functions = etree.SubElement(arithops,
        util.nspath_eval('ogc:Functions', self.parent.context.namespaces))

        functionames = etree.SubElement(functions,
        util.nspath_eval('ogc:FunctionNames', self.parent.context.namespaces))

        for fnop in sorted(fes1.MODEL['Functions'].keys()):
            etree.SubElement(functionames,
            util.nspath_eval('ogc:FunctionName', self.parent.context.namespaces),
            nArgs=fes1.MODEL['Functions'][fnop]['args']).text = fnop

        idcaps = etree.SubElement(fltcaps,
        util.nspath_eval('ogc:Id_Capabilities', self.parent.context.namespaces))

        for idcap in fes1.MODEL['Ids']['values']:
            etree.SubElement(idcaps, util.nspath_eval('ogc:%s' % idcap,
            self.parent.context.namespaces))

        return node

    def describerecord(self):
        ''' Handle DescribeRecord request '''

        if 'typename' not in self.parent.kvp or \
        len(self.parent.kvp['typename']) == 0:  # missing typename
        # set to return all typenames
            self.parent.kvp['typename'] = ['csw:Record']

            if self.parent.profiles is not None:
                for prof in self.parent.profiles['loaded'].keys():
                    self.parent.kvp['typename'].append(
                    self.parent.profiles['loaded'][prof].typename)

        elif self.parent.requesttype == 'GET':  # pass via GET
            self.parent.kvp['typename'] = self.parent.kvp['typename'].split(',')

        if ('outputformat' in self.parent.kvp and
            self.parent.kvp['outputformat'] not in
            self.parent.context.model['operations']['DescribeRecord']
            ['parameters']['outputFormat']['values']):  # bad outputformat
            return self.exceptionreport('InvalidParameterValue',
            'outputformat', 'Invalid value for outputformat: %s' %
            self.parent.kvp['outputformat'])

        if ('schemalanguage' in self.parent.kvp and
            self.parent.kvp['schemalanguage'] not in
            self.parent.context.model['operations']['DescribeRecord']['parameters']
            ['schemaLanguage']['values']):  # bad schemalanguage
            return self.exceptionreport('InvalidParameterValue',
            'schemalanguage', 'Invalid value for schemalanguage: %s' %
            self.parent.kvp['schemalanguage'])

        node = etree.Element(util.nspath_eval('csw:DescribeRecordResponse',
        self.parent.context.namespaces), nsmap=self.parent.context.namespaces)

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.parent.context.namespaces)] = \
        '%s %s/csw/2.0.2/CSW-discovery.xsd' % (self.parent.context.namespaces['csw'],
        self.parent.config.get('server', 'ogc_schemas_base'))

        for typename in self.parent.kvp['typename']:
            if typename.find(':') == -1:  # unqualified typename
                return self.exceptionreport('InvalidParameterValue',
                'typename', 'Typename not qualified: %s' % typename)
            if typename == 'csw:Record':   # load core schema
                LOGGER.info('Writing csw:Record schema')
                schemacomponent = etree.SubElement(node,
                util.nspath_eval('csw:SchemaComponent', self.parent.context.namespaces),
                schemaLanguage='XMLSCHEMA',
                targetNamespace=self.parent.context.namespaces['csw'])

                path = os.path.join(self.parent.config.get('server', 'home'),
                'core', 'schemas', 'ogc', 'csw', '2.0.2', 'record.xsd')

                dublincore = etree.parse(path, self.parent.context.parser).getroot()

                schemacomponent.append(dublincore)

            if self.parent.profiles is not None:
                for prof in self.parent.profiles['loaded'].keys():
                    if self.parent.profiles['loaded'][prof].typename == typename:
                        scnodes = \
                        self.parent.profiles['loaded'][prof].get_schemacomponents()
                        if scnodes:
                            for scn in scnodes:
                                node.append(scn)
        return node

    def getdomain(self):
        ''' Handle GetDomain request '''
        if ('parametername' not in self.parent.kvp and
            'propertyname' not in self.parent.kvp):
            return self.exceptionreport('MissingParameterValue',
            'parametername', 'Missing value. \
            One of propertyname or parametername must be specified')

        node = etree.Element(util.nspath_eval('csw:GetDomainResponse',
        self.parent.context.namespaces), nsmap=self.parent.context.namespaces)

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.parent.context.namespaces)] = '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (self.parent.context.namespaces['csw'],
        self.parent.config.get('server', 'ogc_schemas_base'))

        if 'parametername' in self.parent.kvp:
            for pname in self.parent.kvp['parametername'].split(','):
                LOGGER.info('Parsing parametername %s', pname)
                domainvalue = etree.SubElement(node,
                util.nspath_eval('csw:DomainValues', self.parent.context.namespaces),
                type='csw:Record')
                etree.SubElement(domainvalue,
                util.nspath_eval('csw:ParameterName',
                self.parent.context.namespaces)).text = pname
                try:
                    operation, parameter = pname.split('.')
                except:
                    return node
                if (operation in self.parent.context.model['operations'].keys() and
                    parameter in
                    self.parent.context.model['operations'][operation]['parameters'].keys()):
                    listofvalues = etree.SubElement(domainvalue,
                    util.nspath_eval('csw:ListOfValues', self.parent.context.namespaces))
                    for val in \
                    sorted(self.parent.context.model['operations'][operation]\
                    ['parameters'][parameter]['values']):
                        etree.SubElement(listofvalues,
                        util.nspath_eval('csw:Value',
                        self.parent.context.namespaces)).text = val

        if 'propertyname' in self.parent.kvp:
            for pname in self.parent.kvp['propertyname'].split(','):
                LOGGER.info('Parsing propertyname %s', pname)

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
                    dvtype = 'csw:Record'

                domainvalue = etree.SubElement(node,
                util.nspath_eval('csw:DomainValues', self.parent.context.namespaces),
                type=dvtype)
                etree.SubElement(domainvalue,
                util.nspath_eval('csw:PropertyName',
                self.parent.context.namespaces)).text = pname

                try:
                    LOGGER.info(
                    'Querying repository property %s, typename %s, \
                    domainquerytype %s',  pname2, dvtype, self.parent.domainquerytype)

                    count = False

                    if (self.parent.config.has_option('server', 'domaincounts') and
                        self.parent.config.get('server', 'domaincounts') == 'true'):
                        count = True

                    results = self.parent.repository.query_domain(
                    pname2, dvtype, self.parent.domainquerytype, count)

                    LOGGER.debug('Results: %d', len(results))

                    if self.parent.domainquerytype == 'range':
                        rangeofvalues = etree.SubElement(domainvalue,
                        util.nspath_eval('csw:RangeOfValues',
                        self.parent.context.namespaces))

                        etree.SubElement(rangeofvalues,
                        util.nspath_eval('csw:MinValue',
                        self.parent.context.namespaces)).text = results[0][0]

                        etree.SubElement(rangeofvalues,
                        util.nspath_eval('csw:MaxValue',
                        self.parent.context.namespaces)).text = results[0][1]
                    else:
                        listofvalues = etree.SubElement(domainvalue,
                        util.nspath_eval('csw:ListOfValues',
                        self.parent.context.namespaces))
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
                                self.parent.context.namespaces)).text = val
                except Exception as err:
                    # here we fail silently back to the client because
                    # CSW tells us to
                    LOGGER.exception('No results for propertynames')
        return node

    def getrecords(self):
        ''' Handle GetRecords request '''

        timestamp = util.get_today_and_now()

        if ('elementsetname' not in self.parent.kvp and
            'elementname' not in self.parent.kvp):
            # mutually exclusive required
            return self.exceptionreport('MissingParameterValue',
            'elementsetname',
            'Missing one of ElementSetName or ElementName parameter(s)')

        if 'outputschema' not in self.parent.kvp:
            self.parent.kvp['outputschema'] = self.parent.context.namespaces['csw']

        if (self.parent.kvp['outputschema'] not in self.parent.context.model['operations']
            ['GetRecords']['parameters']['outputSchema']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputschema', 'Invalid outputSchema parameter value: %s' %
            self.parent.kvp['outputschema'])

        if 'outputformat' not in self.parent.kvp:
            self.parent.kvp['outputformat'] = 'application/xml'

        if (self.parent.kvp['outputformat'] not in self.parent.context.model['operations']
            ['GetRecords']['parameters']['outputFormat']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'outputformat', 'Invalid outputFormat parameter value: %s' %
            self.parent.kvp['outputformat'])

        if 'resulttype' not in self.parent.kvp:
            self.parent.kvp['resulttype'] = 'hits'

        if self.parent.kvp['resulttype'] is not None:
            if (self.parent.kvp['resulttype'] not in self.parent.context.model['operations']
            ['GetRecords']['parameters']['resultType']['values']):
                return self.exceptionreport('InvalidParameterValue',
                'resulttype', 'Invalid resultType parameter value: %s' %
                self.parent.kvp['resulttype'])

        if (('elementname' not in self.parent.kvp or
             len(self.parent.kvp['elementname']) == 0) and
             self.parent.kvp['elementsetname'] not in
             self.parent.context.model['operations']['GetRecords']['parameters']
             ['ElementSetName']['values']):
            return self.exceptionreport('InvalidParameterValue',
            'elementsetname', 'Invalid ElementSetName parameter value: %s' %
            self.parent.kvp['elementsetname'])

        if ('elementname' in self.parent.kvp and
            self.parent.requesttype == 'GET'):  # passed via GET
            self.parent.kvp['elementname'] = self.parent.kvp['elementname'].split(',')
            self.parent.kvp['elementsetname'] = 'summary'

        if 'typenames' not in self.parent.kvp:
            return self.exceptionreport('MissingParameterValue',
            'typenames', 'Missing typenames parameter')

        if ('typenames' in self.parent.kvp and
            self.parent.requesttype == 'GET'):  # passed via GET
            self.parent.kvp['typenames'] = self.parent.kvp['typenames'].split(',')

        if 'typenames' in self.parent.kvp:
            for tname in self.parent.kvp['typenames']:
                if (tname not in self.parent.context.model['operations']['GetRecords']
                    ['parameters']['typeNames']['values']):
                    return self.exceptionreport('InvalidParameterValue',
                    'typenames', 'Invalid typeNames parameter value: %s' %
                    tname)

        # check elementname's
        if 'elementname' in self.parent.kvp:
            for ename in self.parent.kvp['elementname']:
                enamelist = self.parent.repository.queryables['_all'].keys()
                if ename not in enamelist:
                    return self.exceptionreport('InvalidParameterValue',
                    'elementname', 'Invalid ElementName parameter value: %s' %
                    ename)

        if self.parent.kvp['resulttype'] == 'validate':
            return self._write_acknowledgement()

        maxrecords_cfg = -1  # not set in config server.maxrecords

        if self.parent.config.has_option('server', 'maxrecords'):
            maxrecords_cfg = int(self.parent.config.get('server', 'maxrecords'))

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
            tmp_filter = opensearch.kvp2filterxml(self.parent.kvp, self.parent.context)
            if tmp_filter is not "":
                self.parent.kvp['constraint'] = tmp_filter
                LOGGER.debug('OpenSearch Geo/Time parameters to Filter: %s.', self.parent.kvp['constraint'])

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
                    try:
                        LOGGER.info('Transforming CQL into fes1')
                        LOGGER.debug('CQL: %s', tmp)
                        self.parent.kvp['constraint'] = {}
                        self.parent.kvp['constraint']['type'] = 'filter'
                        cql = cql2fes1(tmp, self.parent.context.namespaces)
                        self.parent.kvp['constraint']['where'], self.parent.kvp['constraint']['values'] = fes1.parse(cql,
                        self.parent.repository.queryables['_all'], self.parent.repository.dbtype,
                        self.parent.context.namespaces, self.parent.orm, self.parent.language['text'], self.parent.repository.fts)
                        self.parent.kvp['constraint']['_dict'] = xml2dict(etree.tostring(cql), self.parent.context.namespaces)
                    except Exception as err:
                        LOGGER.exception('Invalid CQL query %s', tmp)
                        return self.exceptionreport('InvalidParameterValue',
                        'constraint', 'Invalid Filter syntax')
                elif self.parent.kvp['constraintlanguage'] == 'FILTER':
                    # validate filter XML
                    try:
                        schema = os.path.join(self.parent.config.get('server', 'home'),
                        'core', 'schemas', 'ogc', 'filter', '1.1.0', 'filter.xsd')
                        LOGGER.info('Validating Filter %s', self.parent.kvp['constraint'])
                        schema = etree.XMLSchema(file=schema)
                        parser = etree.XMLParser(schema=schema, resolve_entities=False)
                        doc = etree.fromstring(self.parent.kvp['constraint'], parser)
                        LOGGER.debug('Filter is valid XML')
                        self.parent.kvp['constraint'] = {}
                        self.parent.kvp['constraint']['type'] = 'filter'
                        self.parent.kvp['constraint']['where'], self.parent.kvp['constraint']['values'] = \
                        fes1.parse(doc,
                        self.parent.repository.queryables['_all'],
                        self.parent.repository.dbtype,
                        self.parent.context.namespaces, self.parent.orm, self.parent.language['text'], self.parent.repository.fts)
                        self.parent.kvp['constraint']['_dict'] = xml2dict(etree.tostring(doc), self.parent.context.namespaces)
                    except Exception as err:
                        errortext = \
                        'Exception: document not valid.\nError: %s.' % str(err)
                        LOGGER.exception(errortext)
                        return self.exceptionreport('InvalidParameterValue',
                        'constraint', 'Invalid Filter query: %s' % errortext)
            else:
                self.parent.kvp['constraint'] = {}

        if 'sortby' not in self.parent.kvp:
            self.parent.kvp['sortby'] = None
        elif 'sortby' in self.parent.kvp and self.parent.requesttype == 'GET':
            LOGGER.debug('Sorted query specified')
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

        # query repository
        LOGGER.debug('Querying repository with constraint: %s,\
        sortby: %s, typenames: %s, maxrecords: %s, startposition: %s',
        self.parent.kvp['constraint'], self.parent.kvp['sortby'], self.parent.kvp['typenames'],
        self.parent.kvp['maxrecords'], self.parent.kvp['startposition'])

        try:
            matched, results = self.parent.repository.query(
            constraint=self.parent.kvp['constraint'],
            sortby=self.parent.kvp['sortby'], typenames=self.parent.kvp['typenames'],
            maxrecords=self.parent.kvp['maxrecords'],
            startposition=int(self.parent.kvp['startposition'])-1)
        except Exception as err:
            LOGGER.exception('Invalid query syntax.  Query: %s', self.parent.kvp['constraint'])
            LOGGER.exception('Invalid query syntax.  Result: %s', err)
            return self.exceptionreport('InvalidParameterValue', 'constraint',
            'Invalid query syntax')

        dsresults = []

        if (self.parent.config.has_option('server', 'federatedcatalogues') and
            'distributedsearch' in self.parent.kvp and
            self.parent.kvp['distributedsearch'] and self.parent.kvp['hopcount'] > 0):
            # do distributed search

            LOGGER.debug('DistributedSearch specified (hopCount: %s).',
            self.parent.kvp['hopcount'])

            from owslib.csw import CatalogueServiceWeb
            from owslib.ows import ExceptionReport
            for fedcat in \
            self.parent.config.get('server', 'federatedcatalogues').split(','):
                LOGGER.debug('Performing distributed search on federated \
                catalogue: %s.', fedcat)
                remotecsw = CatalogueServiceWeb(fedcat, skip_caps=True)
                try:
                    remotecsw.getrecords2(xml=self.parent.request,
                                          esn=self.parent.kvp['elementsetname'],
                                          outputschema=self.parent.kvp['outputschema'])
                    if hasattr(remotecsw, 'results'):
                        LOGGER.debug(
                        'Distributed search results from catalogue \
                        %s: %s.', fedcat, remotecsw.results)

                        remotecsw_matches = int(remotecsw.results['matches'])
                        plural = 's' if remotecsw_matches != 1 else ''
                        if remotecsw_matches > 0:
                            matched = str(int(matched) + remotecsw_matches)
                            dsresults.append(etree.Comment(
                            ' %d result%s from %s ' %
                            (remotecsw_matches, plural, fedcat)))

                            dsresults.append(remotecsw.records)
                except ExceptionReport as err:
                    error_string = 'remote CSW %s returned exception: ' % fedcat
                    dsresults.append(etree.Comment(
                    ' %s\n\n%s ' % (error_string, err)))
                    LOGGER.exception(error_string)
                except Exception as err:
                    error_string = 'remote CSW %s returned error: ' % fedcat
                    dsresults.append(etree.Comment(
                    ' %s\n\n%s ' % (error_string, err)))
                    LOGGER.exception(error_string)

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

        LOGGER.debug('Results: matched: %s, returned: %s, next: %s',
        matched, returned, nextrecord)

        node = etree.Element(util.nspath_eval('csw:GetRecordsResponse',
        self.parent.context.namespaces),
        nsmap=self.parent.context.namespaces, version='2.0.2')

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.parent.context.namespaces)] = \
        '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (self.parent.context.namespaces['csw'], self.parent.config.get('server', 'ogc_schemas_base'))

        if 'requestid' in self.parent.kvp and self.parent.kvp['requestid'] is not None:
            etree.SubElement(node, util.nspath_eval('csw:RequestId',
            self.parent.context.namespaces)).text = self.parent.kvp['requestid']

        etree.SubElement(node, util.nspath_eval('csw:SearchStatus',
        self.parent.context.namespaces), timestamp=timestamp)

        if 'where' not in self.parent.kvp['constraint'] and \
        self.parent.kvp['resulttype'] is None:
            returned = '0'

        searchresults = etree.SubElement(node,
        util.nspath_eval('csw:SearchResults', self.parent.context.namespaces),
        numberOfRecordsMatched=matched, numberOfRecordsReturned=returned,
        nextRecord=nextrecord, recordSchema=self.parent.kvp['outputschema'])

        if self.parent.kvp['elementsetname'] is not None:
            searchresults.attrib['elementSet'] = self.parent.kvp['elementsetname']

        if 'where' not in self.parent.kvp['constraint'] \
        and self.parent.kvp['resulttype'] is None:
            LOGGER.debug('Empty result set returned')
            return node

        if self.parent.kvp['resulttype'] == 'hits':
            return node


        if results is not None:
            if len(results) < int(self.parent.kvp['maxrecords']):
                max1 = len(results)
            else:
                max1 = int(self.parent.kvp['startposition']) + (int(self.parent.kvp['maxrecords'])-1)
            LOGGER.info('Presenting records %s - %s',
            self.parent.kvp['startposition'], max1)

            for res in results:
                try:
                    if (self.parent.kvp['outputschema'] ==
                        'http://www.opengis.net/cat/csw/2.0.2' and
                        'csw:Record' in self.parent.kvp['typenames']):
                        # serialize csw:Record inline
                        searchresults.append(self._write_record(
                        res, self.parent.repository.queryables['_all']))
                    elif (self.parent.kvp['outputschema'] ==
                        'http://www.opengis.net/cat/csw/2.0.2' and
                        'csw:Record' not in self.parent.kvp['typenames']):
                        # serialize into csw:Record model

                        for prof in self.parent.profiles['loaded']:
                            # find source typename
                            if self.parent.profiles['loaded'][prof].typename in \
                            self.parent.kvp['typenames']:
                                typename = self.parent.profiles['loaded'][prof].typename
                                break

                        util.transform_mappings(
                            self.parent.repository.queryables['_all'],
                            self.parent.context.model['typenames'][typename][
                                'mappings']['csw:Record']
                        )

                        searchresults.append(self._write_record(
                        res, self.parent.repository.queryables['_all']))
                    elif self.parent.kvp['outputschema'] in self.parent.outputschemas.keys():  # use outputschema serializer
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

        if len(dsresults) > 0:  # return DistributedSearch results
            for resultset in dsresults:
                if isinstance(resultset, etree._Comment):
                    searchresults.append(resultset)
                for rec in resultset:
                    searchresults.append(etree.fromstring(resultset[rec].xml, self.parent.context.parser))

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
            self.parent.kvp['outputschema'] = self.parent.context.namespaces['csw']

        if self.parent.requesttype == 'GET':
            self.parent.kvp['id'] = self.parent.kvp['id'].split(',')

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

        if 'elementsetname' not in self.parent.kvp:
            self.parent.kvp['elementsetname'] = 'summary'
        else:
            if (self.parent.kvp['elementsetname'] not in
                self.parent.context.model['operations']['GetRecordById']['parameters']
                ['ElementSetName']['values']):
                return self.exceptionreport('InvalidParameterValue',
                'elementsetname', 'Invalid elementsetname parameter %s' %
                self.parent.kvp['elementsetname'])

        node = etree.Element(util.nspath_eval('csw:GetRecordByIdResponse',
        self.parent.context.namespaces), nsmap=self.parent.context.namespaces)

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.parent.context.namespaces)] = '%s %s/csw/2.0.2/CSW-discovery.xsd' % \
        (self.parent.context.namespaces['csw'], self.parent.config.get('server', 'ogc_schemas_base'))

        # query repository
        LOGGER.info('Querying repository with ids: %s', self.parent.kvp['id'][0])
        results = self.parent.repository.query_ids(self.parent.kvp['id'])

        if raw:  # GetRepositoryItem request
            LOGGER.debug('GetRepositoryItem request')
            if len(results) > 0:
                return etree.fromstring(util.getqattr(results[0],
                self.parent.context.md_core_model['mappings']['pycsw:XML']), self.parent.context.parser)

        for result in results:
            if (util.getqattr(result,
            self.parent.context.md_core_model['mappings']['pycsw:Typename']) == 'csw:Record'
            and self.parent.kvp['outputschema'] ==
            'http://www.opengis.net/cat/csw/2.0.2'):
                # serialize record inline
                node.append(self._write_record(
                result, self.parent.repository.queryables['_all']))
            elif (self.parent.kvp['outputschema'] ==
                'http://www.opengis.net/cat/csw/2.0.2'):
                # serialize into csw:Record model
                typename = None

                for prof in self.parent.profiles['loaded']:  # find source typename
                    if self.parent.profiles['loaded'][prof].typename in \
                    [util.getqattr(result, self.parent.context.md_core_model['mappings']['pycsw:Typename'])]:
                        typename = self.parent.profiles['loaded'][prof].typename
                        break

                if typename is not None:
                    util.transform_mappings(
                        self.parent.repository.queryables['_all'],
                        self.parent.context.model['typenames'][typename][
                            'mappings']['csw:Record']
                    )

                node.append(self._write_record(
                result, self.parent.repository.queryables['_all']))
            elif self.parent.kvp['outputschema'] in self.parent.outputschemas.keys():  # use outputschema serializer
                node.append(self.parent.outputschemas[self.parent.kvp['outputschema']].write_record(result, self.parent.kvp['elementsetname'], self.parent.context, self.parent.config.get('server', 'url')))
            else:  # it's a profile output
                node.append(
                self.parent.profiles['loaded'][self.parent.kvp['outputschema']].write_record(
                result, self.parent.kvp['elementsetname'],
                self.parent.kvp['outputschema'], self.parent.repository.queryables['_all']))

        if raw and len(results) == 0:
            return None

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

        LOGGER.debug('Transaction list: %s', self.parent.kvp['transactions'])

        for ttype in self.parent.kvp['transactions']:
            if ttype['type'] == 'insert':
                try:
                    record = metadata.parse_record(self.parent.context,
                    ttype['xml'], self.parent.repository)[0]
                except Exception as err:
                    LOGGER.exception('Transaction (insert) failed')
                    return self.exceptionreport('NoApplicableCode', 'insert',
                    'Transaction (insert) failed: record parsing failed: %s' \
                    % str(err))

                LOGGER.debug('Transaction operation: %s', record)

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
                    LOGGER.info('checking if record exists (%s)', identifier)

                    results = self.parent.repository.query_ids(ids=[identifier])

                    if len(results) == 0:
                        LOGGER.debug('id %s does not exist in repository', identifier)
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

                    LOGGER.debug('Record Properties: %s.', ttype['recordproperty'])
                    try:
                        updated += self.parent.repository.update(record=None,
                        recprops=ttype['recordproperty'],
                        constraint=ttype['constraint'])
                    except Exception as err:
                        LOGGER.exception('Transaction (updated) failed')
                        return self.exceptionreport('NoApplicableCode',
                        'update',
                        'Transaction (update) failed: %s.' % str(err))

            elif ttype['type'] == 'delete':
                deleted += self.parent.repository.delete(ttype['constraint'])

        node = etree.Element(util.nspath_eval('csw:TransactionResponse',
        self.parent.context.namespaces), nsmap=self.parent.context.namespaces, version='2.0.2')

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.parent.context.namespaces)] = '%s %s/csw/2.0.2/CSW-publication.xsd' % \
        (self.parent.context.namespaces['csw'], self.parent.config.get('server', 'ogc_schemas_base'))

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
            LOGGER.debug('Fetching resource %s', self.parent.kvp['source'])
            try:
                content = util.http_request('GET', self.parent.kvp['source'])
            except Exception as err:
                errortext = 'Error fetching resource %s.\nError: %s.' % \
                (self.parent.kvp['source'], str(err))
                LOGGER.exception(errortext)
                return self.exceptionreport('InvalidParameterValue', 'source',
                errortext)
        else:  # it's a service URL
            content = self.parent.kvp['source']
            # query repository to see if service already exists
            LOGGER.info('checking if service exists (%s)', content)
            results = self.parent.repository.query_source(content)

            if len(results) > 0:  # exists, keep identifier for update
                LOGGER.debug('Service already exists, keeping identifier and results')
                service_identifier = getattr(results[0], self.parent.context.md_core_model['mappings']['pycsw:Identifier'])
                service_results = results
                LOGGER.debug('Identifier is %s', service_identifier)
            #    return self.exceptionreport('NoApplicableCode', 'source',
            #    'Insert failed: service %s already in repository' % content)


        if hasattr(self.parent.repository, 'local_ingest') and self.parent.repository.local_ingest:
            updated = 0
            deleted = []
            try:
                ir = self.parent.repository.insert(self.parent.kvp['resourcetype'], self.parent.kvp['source'])
                inserted = len(ir)
            except Exception as err:
                LOGGER.exception('Harvest (insert) failed')
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

            LOGGER.debug('Total Records parsed: %d', len(records_parsed))
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
                    LOGGER.info('Replacing service identifier from %s to %s', record_identifier, service_identifier)
                    old_identifier = record_identifier
                    identifier = record_identifier = service_identifier
                if (record_type != 'service' and service_identifier is not None
                    and old_identifier is not None):  # service resource
                    if record_identifier.find(old_identifier) != -1:
                        new_identifier = record_identifier.replace(old_identifier, service_identifier)
                        LOGGER.debug('Replacing service resource identifier from %s to %s', record_identifier, new_identifier)
                        identifier = record_identifier = new_identifier

                ir.append({'identifier': identifier, 'title': title})

                results = []
                if not self.parent.config.has_option('repository', 'source'):
                    # query repository to see if record already exists
                    LOGGER.info('checking if record exists (%s)', identifier)
                    results = self.parent.repository.query_ids(ids=[identifier])

                    if len(results) == 0:  # check for service identifier
                        LOGGER.info('checking if service id exists (%s)', service_identifier)
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
                LOGGER.debug('Records to delete: %s', deleted)

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
        ''' Generate csw:Record '''
        if self.parent.kvp['elementsetname'] == 'brief':
            elname = 'BriefRecord'
        elif self.parent.kvp['elementsetname'] == 'summary':
            elname = 'SummaryRecord'
        else:
            elname = 'Record'

        record = etree.Element(util.nspath_eval('csw:%s' % elname,
                 self.parent.context.namespaces))

        if ('elementname' in self.parent.kvp and
            len(self.parent.kvp['elementname']) > 0):
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
                    if value:
                        etree.SubElement(record,
                        util.nspath_eval(elemname,
                        self.parent.context.namespaces)).text = value
        elif 'elementsetname' in self.parent.kvp:
            if (self.parent.kvp['elementsetname'] == 'full' and
            util.getqattr(recobj, self.parent.context.md_core_model['mappings']\
            ['pycsw:Typename']) == 'csw:Record' and
            util.getqattr(recobj, self.parent.context.md_core_model['mappings']\
            ['pycsw:Schema']) == 'http://www.opengis.net/cat/csw/2.0.2' and
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
                'dc:language', 'dc:rights', 'dct:alternative']:
                    val = util.getqattr(recobj, queryables[i]['dbcol'])
                    if val:
                        etree.SubElement(record,
                        util.nspath_eval(i, self.parent.context.namespaces)).text = val
                val = util.getqattr(recobj, queryables['dct:spatial']['dbcol'])
                if val:
                    etree.SubElement(record,
                    util.nspath_eval('dct:spatial', self.parent.context.namespaces), scheme='http://www.opengis.net/def/crs').text = val

            # always write out ows:BoundingBox
            bboxel = write_boundingbox(getattr(recobj,
            self.parent.context.md_core_model['mappings']['pycsw:BoundingBox']),
            self.parent.context.namespaces)

            if bboxel is not None:
                record.append(bboxel)
        return record

    def _parse_constraint(self, element):
        ''' Parse csw:Constraint '''

        query = {}

        tmp = element.find(util.nspath_eval('ogc:Filter', self.parent.context.namespaces))
        if tmp is not None:
            LOGGER.debug('Filter constraint specified')
            try:
                query['type'] = 'filter'
                query['where'], query['values'] = fes1.parse(tmp,
                self.parent.repository.queryables['_all'], self.parent.repository.dbtype,
                self.parent.context.namespaces, self.parent.orm, self.parent.language['text'], self.parent.repository.fts)
                query['_dict'] = xml2dict(etree.tostring(tmp), self.parent.context.namespaces)
            except Exception as err:
                return 'Invalid Filter request: %s' % err

        tmp = element.find(util.nspath_eval('csw:CqlText', self.parent.context.namespaces))
        if tmp is not None:
            LOGGER.debug('CQL specified: %s.', tmp.text)
            try:
                LOGGER.info('Transforming CQL into OGC Filter')
                query['type'] = 'filter'
                cql = cql2fes1(tmp.text, self.parent.context.namespaces)
                query['where'], query['values'] = fes1.parse(cql,
                self.parent.repository.queryables['_all'], self.parent.repository.dbtype,
                self.parent.context.namespaces, self.parent.orm, self.parent.language['text'], self.parent.repository.fts)
                query['_dict'] = xml2dict(etree.tostring(cql), self.parent.context.namespaces)
            except Exception as err:
                LOGGER.exception('Invalid CQL request: %s', tmp.text)
                LOGGER.exception('Error message: %s', err)
                return 'Invalid CQL request'
        return query

    def parse_postdata(self, postdata):
        ''' Parse POST XML '''

        request = {}
        try:
            LOGGER.info('Parsing %s', postdata)
            doc = etree.fromstring(postdata, self.parent.context.parser)
        except Exception as err:
            errortext = \
            'Exception: document not well-formed.\nError: %s.' % str(err)
            LOGGER.exception(errortext)
            return errortext

        # if this is a SOAP request, get to SOAP-ENV:Body/csw:*
        if (doc.tag == util.nspath_eval('soapenv:Envelope',
            self.parent.context.namespaces)):

            LOGGER.debug('SOAP request specified')
            self.parent.soap = True

            doc = doc.find(
            util.nspath_eval('soapenv:Body',
            self.parent.context.namespaces)).xpath('child::*')[0]

        if (doc.tag in [util.nspath_eval('csw:Transaction',
            self.parent.context.namespaces), util.nspath_eval('csw:Harvest',
            self.parent.context.namespaces)]):
            schema = os.path.join(self.parent.config.get('server', 'home'),
            'core', 'schemas', 'ogc', 'csw', '2.0.2', 'CSW-publication.xsd')
        else:
            schema = os.path.join(self.parent.config.get('server', 'home'),
            'core', 'schemas', 'ogc', 'csw', '2.0.2', 'CSW-discovery.xsd')

        try:
            # it is virtually impossible to validate a csw:Transaction
            # csw:Insert|csw:Update (with single child) XML document.
            # Only validate non csw:Transaction XML

            if doc.find('.//%s' % util.nspath_eval('csw:Insert',
            self.parent.context.namespaces)) is None and \
            len(doc.xpath('//csw:Update/child::*',
            namespaces=self.parent.context.namespaces)) == 0:

                LOGGER.info('Validating %s', postdata)
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
            LOGGER.exception(errortext)
            return errortext

        request['request'] = etree.QName(doc).localname
        LOGGER.debug('Request operation %s specified.', request['request'])
        tmp = doc.find('.').attrib.get('service')
        if tmp is not None:
            request['service'] = tmp

        tmp = doc.find('.').attrib.get('version')
        if tmp is not None:
            request['version'] = tmp

        tmp = doc.find('.//%s' % util.nspath_eval('ows:Version',
        self.parent.context.namespaces))

        if tmp is not None:
            request['version'] = tmp.text

        tmp = doc.find('.').attrib.get('updateSequence')
        if tmp is not None:
            request['updatesequence'] = tmp

        # GetCapabilities
        if request['request'] == 'GetCapabilities':
            tmp = doc.find(util.nspath_eval('ows:Sections',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['sections'] = ','.join([section.text for section in \
                doc.findall(util.nspath_eval('ows:Sections/ows:Section',
                self.parent.context.namespaces))])

        # DescribeRecord
        if request['request'] == 'DescribeRecord':
            request['typename'] = [typename.text for typename in \
            doc.findall(util.nspath_eval('csw:TypeName',
            self.parent.context.namespaces))]

            tmp = doc.find('.').attrib.get('schemaLanguage')
            if tmp is not None:
                request['schemalanguage'] = tmp

            tmp = doc.find('.').attrib.get('outputFormat')
            if tmp is not None:
                request['outputformat'] = tmp

        # GetDomain
        if request['request'] == 'GetDomain':
            tmp = doc.find(util.nspath_eval('csw:ParameterName',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['parametername'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw:PropertyName',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['propertyname'] = tmp.text

        # GetRecords
        if request['request'] == 'GetRecords':
            tmp = doc.find('.').attrib.get('outputSchema')
            request['outputschema'] = tmp if tmp is not None \
            else self.parent.context.namespaces['csw']

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
                  self.parent.context.namespaces))
            if tmp is not None:
                request['distributedsearch'] = True
                hopcount = tmp.attrib.get('hopCount')
                request['hopcount'] = int(hopcount)-1 if hopcount is not None \
                else 1
            else:
                request['distributedsearch'] = False

            tmp = doc.find(util.nspath_eval('csw:ResponseHandler',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['responsehandler'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw:Query/csw:ElementSetName',
                  self.parent.context.namespaces))
            request['elementsetname'] = tmp.text if tmp is not None else None

            tmp = doc.find(util.nspath_eval(
            'csw:Query', self.parent.context.namespaces)).attrib.get('typeNames')
            request['typenames'] = tmp.split() if tmp is not None \
            else 'csw:Record'

            request['elementname'] = [elname.text for elname in \
            doc.findall(util.nspath_eval('csw:Query/csw:ElementName',
            self.parent.context.namespaces))]

            request['constraint'] = {}
            tmp = doc.find(util.nspath_eval('csw:Query/csw:Constraint',
            self.parent.context.namespaces))

            if tmp is not None:
                request['constraint'] = self._parse_constraint(tmp)
                if isinstance(request['constraint'], str):  # parse error
                    return 'Invalid Constraint: %s' % request['constraint']
            else:
                LOGGER.debug('No csw:Constraint (ogc:Filter or csw:CqlText) \
                specified')

            tmp = doc.find(util.nspath_eval('csw:Query/ogc:SortBy',
                  self.parent.context.namespaces))
            if tmp is not None:
                LOGGER.debug('Sorted query specified')
                request['sortby'] = {}


                try:
                    elname = tmp.find(util.nspath_eval(
                    'ogc:SortProperty/ogc:PropertyName',
                    self.parent.context.namespaces)).text

                    request['sortby']['propertyname'] = \
                    self.parent.repository.queryables['_all'][elname]['dbcol']

                    if (elname.find('BoundingBox') != -1 or
                        elname.find('Envelope') != -1):
                        # it's a spatial sort
                        request['sortby']['spatial'] = True
                except Exception as err:
                    errortext = \
                    'Invalid ogc:SortProperty/ogc:PropertyName: %s' % str(err)
                    LOGGER.exception(errortext)
                    return errortext

                tmp2 =  tmp.find(util.nspath_eval(
                'ogc:SortProperty/ogc:SortOrder', self.parent.context.namespaces))
                request['sortby']['order'] = tmp2.text if tmp2 is not None \
                else 'ASC'
            else:
                request['sortby'] = None

        # GetRecordById
        if request['request'] == 'GetRecordById':
            request['id'] = [id1.text for id1 in \
            doc.findall(util.nspath_eval('csw:Id', self.parent.context.namespaces))]

            tmp = doc.find(util.nspath_eval('csw:ElementSetName',
                  self.parent.context.namespaces))
            request['elementsetname'] = tmp.text if tmp is not None \
            else 'summary'

            tmp = doc.find('.').attrib.get('outputSchema')
            request['outputschema'] = tmp if tmp is not None \
            else self.parent.context.namespaces['csw']

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
            doc.xpath('//csw:Insert', namespaces=self.parent.context.namespaces):
                tname = ttype.attrib.get('typeName')

                for mdrec in ttype.xpath('child::*'):
                    xml = mdrec
                    request['transactions'].append(
                    {'type': 'insert', 'typename': tname, 'xml': xml})

            for ttype in \
            doc.xpath('//csw:Update', namespaces=self.parent.context.namespaces):
                child = ttype.xpath('child::*')
                update = {'type': 'update'}

                if len(child) == 1:  # it's a wholesale update
                    update['xml'] = child[0]
                else:  # it's a RecordProperty with Constraint Update
                    update['recordproperty'] = []

                    for recprop in ttype.findall(
                    util.nspath_eval('csw:RecordProperty',
                        self.parent.context.namespaces)):
                        rpname = recprop.find(util.nspath_eval('csw:Name',
                        self.parent.context.namespaces)).text
                        rpvalue = recprop.find(
                        util.nspath_eval('csw:Value',
                        self.parent.context.namespaces)).text

                        update['recordproperty'].append(
                        {'name': rpname, 'value': rpvalue})

                    update['constraint'] = self._parse_constraint(
                    ttype.find(util.nspath_eval('csw:Constraint',
                    self.parent.context.namespaces)))

                request['transactions'].append(update)

            for ttype in \
            doc.xpath('//csw:Delete', namespaces=self.parent.context.namespaces):
                tname = ttype.attrib.get('typeName')
                constraint = self._parse_constraint(
                ttype.find(util.nspath_eval('csw:Constraint',
                self.parent.context.namespaces)))

                if isinstance(constraint, str):  # parse error
                    return 'Invalid Constraint: %s' % constraint

                request['transactions'].append(
                {'type': 'delete', 'typename': tname, 'constraint': constraint})

        # Harvest
        if request['request'] == 'Harvest':
            request['source'] = doc.find(util.nspath_eval('csw:Source',
            self.parent.context.namespaces)).text

            request['resourcetype'] = \
            doc.find(util.nspath_eval('csw:ResourceType',
            self.parent.context.namespaces)).text

            tmp = doc.find(util.nspath_eval('csw:ResourceFormat',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['resourceformat'] = tmp.text
            else:
                request['resourceformat'] = 'application/xml'

            tmp = doc.find(util.nspath_eval('csw:HarvestInterval',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['harvestinterval'] = tmp.text

            tmp = doc.find(util.nspath_eval('csw:ResponseHandler',
                  self.parent.context.namespaces))
            if tmp is not None:
                request['responsehandler'] = tmp.text
        return request

    def _write_transactionsummary(self, inserted=0, updated=0, deleted=0):
        ''' Write csw:TransactionSummary construct '''
        node = etree.Element(util.nspath_eval('csw:TransactionSummary',
               self.parent.context.namespaces))

        if 'requestid' in self.parent.kvp and self.parent.kvp['requestid'] is not None:
            node.attrib['requestId'] = self.parent.kvp['requestid']

        etree.SubElement(node, util.nspath_eval('csw:totalInserted',
        self.parent.context.namespaces)).text = str(inserted)

        etree.SubElement(node, util.nspath_eval('csw:totalUpdated',
        self.parent.context.namespaces)).text = str(updated)

        etree.SubElement(node, util.nspath_eval('csw:totalDeleted',
        self.parent.context.namespaces)).text = str(deleted)

        return node

    def _write_acknowledgement(self, root=True):
        ''' Generate csw:Acknowledgement '''
        node = etree.Element(util.nspath_eval('csw:Acknowledgement',
               self.parent.context.namespaces),
        nsmap = self.parent.context.namespaces, timeStamp=util.get_today_and_now())

        if root:
            node.attrib[util.nspath_eval('xsi:schemaLocation',
            self.parent.context.namespaces)] = \
            '%s %s/csw/2.0.2/CSW-discovery.xsd' % (self.parent.context.namespaces['csw'], \
            self.parent.config.get('server', 'ogc_schemas_base'))

        node1 = etree.SubElement(node, util.nspath_eval('csw:EchoedRequest',
                self.parent.context.namespaces))
        if self.parent.requesttype == 'POST':
            node1.append(etree.fromstring(self.parent.request, self.parent.context.parser))
        else:  # GET
            node2 = etree.SubElement(node1, util.nspath_eval('ows:Get',
                    self.parent.context.namespaces))

            node2.text = self.parent.request

        if self.parent.async:
            etree.SubElement(node, util.nspath_eval('csw:RequestId',
            self.parent.context.namespaces)).text = self.kvp['requestid']

        return node

    def _write_verboseresponse(self, insertresults):
        ''' show insert result identifiers '''
        insertresult = etree.Element(util.nspath_eval('csw:InsertResult',
        self.parent.context.namespaces))
        for ir in insertresults:
            briefrec = etree.SubElement(insertresult,
                       util.nspath_eval('csw:BriefRecord',
                       self.parent.context.namespaces))

            etree.SubElement(briefrec,
            util.nspath_eval('dc:identifier',
            self.parent.context.namespaces)).text = ir['identifier']

            etree.SubElement(briefrec,
            util.nspath_eval('dc:title',
            self.parent.context.namespaces)).text = ir['title']

        return insertresult

    def exceptionreport(self, code, locator, text):
        ''' Generate ExceptionReport '''
        self.parent.exception = True
        self.parent.status = 'OK'

        try:
            language = self.parent.config.get('server', 'language')
            ogc_schemas_base = self.parent.config.get('server', 'ogc_schemas_base')
        except:
            language = 'en-US'
            ogc_schemas_base = self.parent.context.ogc_schemas_base

        node = etree.Element(util.nspath_eval('ows:ExceptionReport',
        self.parent.context.namespaces), nsmap=self.parent.context.namespaces,
        version='1.2.0', language=language)

        node.attrib[util.nspath_eval('xsi:schemaLocation',
        self.parent.context.namespaces)] = \
        '%s %s/ows/1.0.0/owsExceptionReport.xsd' % \
        (self.parent.context.namespaces['ows'], ogc_schemas_base)

        exception = etree.SubElement(node, util.nspath_eval('ows:Exception',
        self.parent.context.namespaces),
        exceptionCode=code, locator=locator)

        exception_text = etree.SubElement(exception,
        util.nspath_eval('ows:ExceptionText',
        self.parent.context.namespaces))

        try:
            exception_text.text = text
        except ValueError as err:
            exception_text.text = repr(text)

        return node

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
