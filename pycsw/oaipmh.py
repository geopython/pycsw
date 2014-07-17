# -*- coding: iso-8859-15 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2013 Tom Kralidis
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
from lxml import etree
from pycsw import fes, util

LOGGER = logging.getLogger(__name__)

class OAIPMH(object):
    """OAI-PMH wrapper class"""
    def __init__(self, context, config):
        self.oaipmh_version = '2.0'

        self.namespaces = {
            'oai': 'http://www.openarchives.org/OAI/2.0/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        self.request_model = {
            'Identify': [],
            'ListSets': ['resumptiontoken'],
            'ListMetadataFormats': ['identifier'],
            'GetRecord': ['identifier', 'metadataprefix'],
            'ListRecords': ['from', 'until', 'set', 'resumptiontoken', 'metadataprefix'],
            'ListIdentifiers': ['from', 'until', 'set', 'resumptiontoken', 'metadataprefix'],
        }
        self.metadata_formats = {
            'iso19139': {
                'namespace': 'http://www.isotc211.org/2005/gmd',
                'schema': 'http://www.isotc211.org/2005/gmd/gmd.xsd',
                'identifier': '//gmd:fileIdentifier/gco:CharacterString',
                'dateStamp': '//gmd:dateStamp/gco:DateTime'
            },
            'csw-record': {
                'namespace': 'http://www.opengis.net/cat/csw/2.0.2',
                'schema': 'http://schemas.opengis.net/csw/2.0.2/record.xsd',
                'identifier': '//dc:identifier',
                'dateStamp': '//dct:modified'
            },
            'fgdc-std': {
                'namespace': 'http://www.opengis.net/cat/csw/csdgm',
                'schema': 'http://www.fgdc.gov/metadata/fgdc-std-001-1998.xsd',
                'identifier': '//idinfo/datasetid',
                'dateStamp': '//metainfo/metd'
            },
            'oai_dc': {
                'namespace': self.namespaces['oai'],
                'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
                'identifier': '//dc:identifier',
                'dateStamp': '//dct:modified'
            },
            'dif': {
                'namespace': 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/',
                'schema': 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/dif.xsd',
                'identifier': '//dif:Entry_ID',
                'dateStamp': '//dif:Last_DIF_Revision_Date'
            }
        }
        self.metadata_sets = {
            'datasets': ('Datasets', 'dataset'),
            'interactiveResources': ('Interactive Resources', 'service')
        }
        self.error_codes = {
            'badArgument': 'InvalidParameterValue',
            'badVerb': 'OperationNotSupported',
            'idDoesNotExist': None,
            'noRecordsMatch': None,
        }

        self.context = context
        self.context.namespaces.update(self.namespaces)
        self.config = config

    def request(self, kvp):
        """process OAI-PMH request"""
        kvpout = {'service': 'CSW', 'version': '2.0.2', 'mode': 'oaipmh'}
        if 'verb' in kvp:
            if 'metadataprefix' in kvp:
                self.metadata_prefix = kvp['metadataprefix']
                kvpout['outputschema'] = self._get_metadata_prefix(kvp['metadataprefix'])
            else:
                self.metadata_prefix = 'csw-record'
            if kvp['verb'] in ['ListRecords', 'ListIdentifiers', 'GetRecord']:
                kvpout['request'] = 'GetRecords'
                kvpout['resulttype'] = 'results'
                kvpout['typenames'] = 'csw:Record'
                kvpout['elementsetname'] = 'full'
            if kvp['verb'] in ['Identify', 'ListMetadataFormats', 'ListSets']:
                kvpout['request'] = 'GetCapabilities'
            elif kvp['verb'] == 'GetRecord':
                kvpout['request'] = 'GetRecordById'
                if 'identifier' in kvp:
                    kvpout['id'] = kvp['identifier']
            elif kvp['verb'] in ['ListRecords', 'ListIdentifiers']:
                if 'resumptiontoken' in kvp:
                    kvpout['startposition'] = kvp['resumptiontoken']
                if 'outputschema' in kvpout and kvp['verb'] == 'ListIdentifiers':  # simple output only
                    del kvpout['outputschema'] 

                start = end = None
                if 'from' in kvp:
                    start = 'dc:date >= %s' % kvp['from']
                if 'until' in kvp:
                    end = 'dc:date <= %s' % kvp['until']
                if any([start is not None, end is not None]):
                    if all([start is not None, end is not None]):
                        time_query = '%s and %s' % (start, end)
                    elif end is None:
                        time_query = start
                    elif start is None:
                        time_query = end
                    kvpout['constraintlanguage'] = 'CQL_TEXT'
                    kvpout['constraint'] = time_query
        return kvpout

    def response(self, response, kvp, repository, server_url):
        """process OAI-PMH request"""

        mode = kvp.pop('mode', None)
        url = '%smode=oaipmh' % util.bind_url(server_url)

        node = etree.Element(util.nspath_eval('oai:OAI-PMH', self.namespaces), nsmap=self.namespaces)
        node.set(util.nspath_eval('xsi:schemaLocation', self.namespaces), 'http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd')
        LOGGER.info(etree.tostring(node))

        etree.SubElement(node, util.nspath_eval('oai:responseDate', self.namespaces)).text = util.get_today_and_now()
        etree.SubElement(node, util.nspath_eval('oai:request', self.namespaces), attrib=kvp).text = url


        if 'verb' not in kvp:
            etree.SubElement(node, util.nspath_eval('oai:error', self.namespaces), code='badArgument').text = 'Missing \'verb\' parameter'
            return node

        if kvp['verb'] not in self.request_model.keys():
            etree.SubElement(node, util.nspath_eval('oai:error', self.namespaces), code='badArgument').text = 'Unknown verb \'%s\'' % kvp['verb']
            return node

        if util.xmltag_split(response.tag) == 'ExceptionReport':
            etree.SubElement(node, util.nspath_eval('oai:error', self.namespaces), code='badArgument').text = response.xpath('//ows:ExceptionText', namespaces=self.context.namespaces)[0].text
            return node

        verb = kvp.pop('verb')

        for key, value in kvp.iteritems():
            if key != 'mode' and key not in self.request_model[verb]:
                etree.SubElement(node, util.nspath_eval('oai:error', self.namespaces), code='badArgument').text = 'Illegal parameter \'%s\'' % key
                return node

        verbnode = etree.SubElement(node, util.nspath_eval('oai:%s' % verb, self.namespaces))

        if verb == 'Identify':
                etree.SubElement(verbnode, util.nspath_eval('oai:repositoryName', self.namespaces)).text = self.config.get('metadata:main', 'identification_title')
                etree.SubElement(verbnode, util.nspath_eval('oai:baseURL', self.namespaces)).text = url
                etree.SubElement(verbnode, util.nspath_eval('oai:protocolVersion', self.namespaces)).text = '2.0'
                etree.SubElement(verbnode, util.nspath_eval('oai:adminEmail', self.namespaces)).text = self.config.get('metadata:main', 'contact_email')
                etree.SubElement(verbnode, util.nspath_eval('oai:earliestDatestamp', self.namespaces)).text = repository.query_insert('min')
                etree.SubElement(verbnode, util.nspath_eval('oai:deletedRecord', self.namespaces)).text = 'no'
                etree.SubElement(verbnode, util.nspath_eval('oai:granularity', self.namespaces)).text = 'YYYY-MM-DDThh:mm:ssZ'

        elif verb == 'ListSets':
            for key, value in self.metadata_sets.iteritems():
                setnode = etree.SubElement(verbnode, util.nspath_eval('oai:set', self.namespaces))
                etree.SubElement(setnode, util.nspath_eval('oai:setSpec', self.namespaces)).text = key
                etree.SubElement(setnode, util.nspath_eval('oai:setName', self.namespaces)).text = value[0]

        elif verb == 'ListMetadataFormats':
            for key, value in self.metadata_formats.iteritems():
                mdfnode = etree.SubElement(verbnode, util.nspath_eval('oai:metadataFormat', self.namespaces))
                etree.SubElement(mdfnode, util.nspath_eval('oai:metadataPrefix', self.namespaces)).text = key
                etree.SubElement(mdfnode, util.nspath_eval('oai:schema', self.namespaces)).text = value['schema']
                etree.SubElement(mdfnode, util.nspath_eval('oai:metadataNamespace', self.namespaces)).text = value['namespace']

        elif verb in ['GetRecord', 'ListIdentifiers', 'ListRecords']:
                if verb == 'GetRecord':  # GetRecordById
                    records = response.getchildren()
                else:  # GetRecords
                    records = response.getchildren()[1].getchildren()
                for child in records:
                    recnode = etree.SubElement(verbnode, util.nspath_eval('oai:record', self.namespaces))
                    header = etree.SubElement(recnode, util.nspath_eval('oai:header', self.namespaces))
                    self._transform_element(header, response, 'oai:identifier')
                    self._transform_element(header, response, 'oai:dateStamp')
                    if verb in ['GetRecord', 'ListRecords']:
                        metadata = etree.SubElement(recnode, util.nspath_eval('oai:metadata', self.namespaces))
                        metadata.append(child)
                complete_list_size = response.xpath('//@numberOfRecordsMatched')[0]
                next_record = response.xpath('//@nextRecord')[0]
                cursor = str(int(complete_list_size) - int(next_record) - 1)
                
                resumption_token = etree.SubElement(verbnode, util.nspath_eval('oai:resumptionToken', self.namespaces),
                                                    completeListSize=complete_list_size, cursor=cursor).text = next_record
        return node

    def _get_metadata_prefix(self, prefix):
        """Convenience function to return metadataPrefix as CSW outputschema"""
        try:
            outputschema = self.metadata_formats[prefix]['namespace']
        except KeyError:
            outputschema = prefix
        return outputschema

    def _transform_element(self, parent, element, elname):
        """tests for existence of a given xpath, writes out text if exists"""

        xpath = self.metadata_formats[self.metadata_prefix][elname.split(':')[1]]
        value = element.xpath(xpath, namespaces=self.context.namespaces)
        el = etree.SubElement(parent, util.nspath_eval(elname, self.namespaces))
        if value:
            el.text = value[0].text
