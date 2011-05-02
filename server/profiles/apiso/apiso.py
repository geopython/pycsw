# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#                Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2011 Tom Kralidis
# Copyright (c) 2011 Angelos Tzotsos
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
from server import profile, config, util

NAMESPACES = {
    'apiso': 'http://www.opengis.net/cat/csw/apiso/1.0',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'srv': 'http://www.isotc211.org/2005/srv'
}

CODELIST = 'http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml'
CODESPACE = 'ISOTC211/19115'

class APISO(profile.Profile):
    def __init__(self):
        profile.Profile.__init__(self, 'apiso', '1.0.0', 'ISO Metadata Application Profile', 'http://portal.opengeospatial.org/files/?artifact_id=21460', NAMESPACES['gmd'], 'gmd:MD_Metadata', NAMESPACES['gmd'])

    def extend_core(self, model, namespaces):
        ''' Extend core configuration '''

        # model
        model['operations']['DescribeRecord']['parameters']['typeName']['values'].append(self.typename)
        model['operations']['GetRecords']['parameters']['outputSchema']['values'].append(self.outputschema)
        model['operations']['GetRecords']['parameters']['typeNames']['values'].append(self.typename)
        model['operations']['GetRecordById']['parameters']['outputSchema']['values'].append(self.outputschema)
        model['constraints']['IsoProfiles'] = {}
        model['constraints']['IsoProfiles']['values'] = [self.namespace]

        # namespaces
        namespaces.update(NAMESPACES)

    def get_extendedcapabilities(self):
        ''' Add child to ows:OperationsMetadata Element '''
        return None

    def get_schemacomponents(self):
        ''' Return schema components as lxml.etree.Element list '''

        node1 = etree.Element(
        util.nspath_eval('csw:SchemaComponent'),
        schemaLanguage = 'XMLSCHEMA', targetNamespace = self.namespace,
        parentSchema = 'gmd.xsd')

        schema = etree.parse(os.path.join(
                'server', 'profiles', 'apiso',
                'etc', 'schemas', 'ogc', 'iso', '19139',
                '20060504', 'gmd', 'identification.xsd')).getroot()

        node1.append(schema)

        node2 = etree.Element(
        util.nspath_eval('csw:SchemaComponent'),
        schemaLanguage = 'XMLSCHEMA', targetNamespace = self.namespace,
        parentSchema = 'gmd.xsd')

        schema = etree.parse(os.path.join(
                'server', 'profiles', 'apiso',
                'etc', 'schemas', 'ogc', 'iso', '19139',
                '20060504', 'srv', 'serviceMetadata.xsd')).getroot()

        node2.append(schema)

        return [node1, node2]

    def check_getdomain(self, kvp):
        '''Perform extra profile specific checks in the GetDomain request'''
        return None

    def write_record(self, result, esn, outputschema, queryables):
        if outputschema == self.namespace:
            if esn == 'full':  # dump the full record
                xml = getattr(result, queryables['_anytext']['obj_attr'])

                node = etree.fromstring(xml)

            elif esn == 'brief':
                node = etree.Element(util.nspath_eval('gmd:MD_Metadata'))
                node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
                '%s http://schemas.opengis.net/csw/2.0.2/profiles/apiso/1.0.0/apiso.xsd' % self.namespace

                # identifier
                val = getattr(result, queryables['apiso:Identifier']['obj_attr'])

                identifier = etree.SubElement(node, util.nspath_eval('gmd:fileIdentifier'))
                tmp = etree.SubElement(identifier, util.nspath_eval('gco:ChracterString')).text = val

                # hierarchyLevel
                val = getattr(result, queryables['apiso:Type']['obj_attr'])

                hierarchy = etree.SubElement(node, util.nspath_eval('gmd:hierarchyLevel'),
                codeList = '%s#MD_ScopeCode' % CODELIST,
                codeListValue = val,
                codeSpace = CODESPACE).text = val

                # title
                val = getattr(result, queryables['apiso:Title']['obj_attr'])
                identification = etree.SubElement(node, util.nspath_eval('gmd:identificationInfo'))
                tmp = etree.SubElement(identification, util.nspath_eval('gmd:MD_IdentificationInfo'))
                tmp2 = etree.SubElement(tmp, util.nspath_eval('gmd:citation'))
                tmp3 = etree.SubElement(tmp2, util.nspath_eval('gmd:CI_Citation'))
                tmp4 = etree.SubElement(tmp3, util.nspath_eval('gmd:title'))
                etree.SubElement(tmp4, util.nspath_eval('gco:CharacterString')).text = val

                # bbox extent
                val = getattr(result, queryables['apiso:BoundingBox']['obj_attr'])
                bboxel = write_extent(val)
                if bboxel is not None:
                    identification.append(bboxel)

                # service identification
                val = getattr(result, queryables['apiso:ServiceType']['obj_attr'])
                if (val is not None):
                    srv_identification=etree.SubElement(identification, util.nspath_eval('srv:SV_ServiceIdentification'))
                    tmp = etree.SubElement(srv_identification, util.nspath_eval('srv:serviceType'))
                    etree.SubElement(tmp, util.nspath_eval('gco:LocalName')).text = val
                    val = getattr(result, queryables['apiso:ServiceTypeVersion']['obj_attr'])
                    tmp = etree.SubElement(srv_identification, util.nspath_eval('srv:serviceTypeVersion'))
                    etree.SubElement(tmp, util.nspath_eval('gco:CharacterString')).text = val

            else:  # summary
                node = etree.Element(util.nspath_eval('gmd:MD_Metadata'))
                node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
                '%s http://schemas.opengis.net/csw/2.0.2/profiles/apiso/1.0.0/apiso.xsd' % self.namespace

                # identifier
                val = getattr(result, queryables['apiso:Identifier']['obj_attr'])

                identifier = etree.SubElement(node, util.nspath_eval('gmd:fileIdentifier'))
                tmp = etree.SubElement(identifier, util.nspath_eval('gco:ChracterString')).text = val

                # language
                val = getattr(result, queryables['apiso:Language']['obj_attr'])
                lang = etree.SubElement(node, util.nspath_eval('gmd:language'))
                tmp = etree.SubElement(lang, util.nspath_eval('gco:ChracterString')).text = val

                # hierarchyLevel
                val = getattr(result, queryables['apiso:Type']['obj_attr'])
                hierarchy = etree.SubElement(node, util.nspath_eval('gmd:hierarchyLevel'),
                codeList = '%s#MD_ScopeCode' % CODELIST,
                codeListValue = val,
                codeSpace = CODESPACE).text = val

                # contact
                val = getattr(result, queryables['apiso:OrganisationName']['obj_attr'])
                contact = etree.SubElement(node, util.nspath_eval('gmd:contact'))
                CI_resp = etree.SubElement(contact, util.nspath_eval('gmd:CI_ResponsibleParty'))
                org_name = etree.SubElement(CI_resp, util.nspath_eval('gmd:organisationName'))
                tmp = etree.SubElement(org_name, util.nspath_eval('gco:ChracterString')).text = val

                # date
                val = getattr(result, queryables['apiso:Modified']['obj_attr'])
                date = etree.SubElement(node, util.nspath_eval('gmd:dateStamp'))
                etree.SubElement(date, util.nspath_eval('gco:Date')).text = val

                # metadata standard name
                standard = etree.SubElement(node, util.nspath_eval('gmd:metadataStandardName'))
                tmp = etree.SubElement(standard, util.nspath_eval('gco:ChracterString')).text = 'ISO19115'

                # metadata standard version
                standardver = etree.SubElement(node, util.nspath_eval('gmd:metadataStandardName'))
                tmp = etree.SubElement(standardver, util.nspath_eval('gco:ChracterString')).text = '2003/Cor.1:2006'

                # title
                val = getattr(result, queryables['apiso:Title']['obj_attr'])
                identification = etree.SubElement(node, util.nspath_eval('gmd:identificationInfo'))
                mdidentification = etree.SubElement(identification, util.nspath_eval('gmd:MD_IdentificationInfo'))
                tmp2 = etree.SubElement(mdidentification, util.nspath_eval('gmd:citation'))
                tmp3 = etree.SubElement(tmp2, util.nspath_eval('gmd:CI_Citation'))
                tmp4 = etree.SubElement(tmp3, util.nspath_eval('gmd:title'))
                etree.SubElement(tmp4, util.nspath_eval('gco:CharacterString')).text = val

                # abstract
                val = getattr(result, queryables['apiso:Abstract']['obj_attr'])
                tmp2 = etree.SubElement(mdidentification, util.nspath_eval('gmd:abstract'))
                tmp = etree.SubElement(tmp2, util.nspath_eval('gco:ChracterString')).text = val

                # spatial resolution
                val = getattr(result, queryables['apiso:Denominator']['obj_attr'])
                tmp = etree.SubElement(mdidentification, util.nspath_eval('gmd:spatialResolution'))
                tmp2 = etree.SubElement(tmp, util.nspath_eval('gmd:spatialResolution'))
                tmp3 = etree.SubElement(tmp2, util.nspath_eval('gmd:MD_Resolution'))
                tmp4 = etree.SubElement(tmp3, util.nspath_eval('gmd:equivalentScale'))
                tmp5 = etree.SubElement(tmp4, util.nspath_eval('gmd:MD_RepresentativeFraction'))
                tmp6 = etree.SubElement(tmp5, util.nspath_eval('gmd:denominator'))
                tmp7 = etree.SubElement(tmp6, util.nspath_eval('gco:ChracterString')).text = val

                # resource language
                val = getattr(result, queryables['apiso:ResourceLanguage']['obj_attr'])
                tmp = etree.SubElement(mdidentification, util.nspath_eval('gmd:language'))
                etree.SubElement(tmp, util.nspath_eval('gco:CharacterString')).text = val

                # topic category
                val = getattr(result, queryables['apiso:TopicCategory']['obj_attr'])
                for v in val.split(','):
                    tmp = etree.SubElement(mdidentification, util.nspath_eval('gmd:topicCategory'))
                    etree.SubElement(tmp, util.nspath_eval('gmd:MD_TopicCategoryCode')).text = val

                # bbox extent
                val = getattr(result, queryables['apiso:BoundingBox']['obj_attr'])
                bboxel = write_extent(val)
                if bboxel is not None:
                    mdidentification.append(bboxel)

                # service identification
                val = getattr(result, queryables['apiso:ServiceType']['obj_attr'])
                if (val is not None):
                    srv_identification=etree.SubElement(identification, util.nspath_eval('srv:SV_ServiceIdentification'))
                    tmp = etree.SubElement(srv_identification, util.nspath_eval('srv:serviceType'))
                    etree.SubElement(tmp, util.nspath_eval('gco:LocalName')).text = val
                    val = getattr(result, queryables['apiso:ServiceTypeVersion']['obj_attr'])
                    tmp = etree.SubElement(srv_identification, util.nspath_eval('srv:serviceTypeVersion'))
                    etree.SubElement(tmp, util.nspath_eval('gco:CharacterString')).text = val

                    # service operations
                    val = getattr(result, queryables['apiso:Operation']['obj_attr'])
                    temp_oper=val.split(',')
                    oper = etree.SubElement(srv_identification, util.nspath_eval('srv:containsOperations'))
                    for i in temp_oper:
                        tmp = etree.SubElement(oper, util.nspath_eval('srv:SV_OperationMetadata'))
                        tmp2 = etree.SubElement(tmp, util.nspath_eval('srv:operationName'))
                        etree.SubElement(tmp2, util.nspath_eval('gco:CharacterString')).text = i

        else:
            if esn == 'brief':
                node = etree.Element(util.nspath_eval('csw:BriefRecord'))
                val = getattr(result, queryables['apiso:Identifier']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:identifier')).text = val
                val = getattr(result, queryables['apiso:Title']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:title')).text = val
                val = getattr(result, queryables['apiso:Type']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:type')).text = val

            elif esn == 'full':
                node = etree.Element(util.nspath_eval('csw:Record'))
                val = getattr(result, queryables['apiso:OrganisationName']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:creator')).text = val
                etree.SubElement(node, util.nspath_eval('dc:publisher')).text = val
                val = getattr(result, queryables['apiso:Subject']['obj_attr'])
                for s in val.split(','):
                    etree.SubElement(node, util.nspath_eval('dc:subject')).text = val
                val = getattr(result, queryables['apiso:TopicCategory']['obj_attr'])
                for s in val.split(','):
                    etree.SubElement(node, util.nspath_eval('dc:subject')).text = val
                val = getattr(result, queryables['apiso:Abstract']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dct:abstract')).text = val
                val = getattr(result, queryables['apiso:Identifier']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:identifier')).text = val
                val = getattr(result, queryables['apiso:ParentIdentifier']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:relation')).text = val
                val = getattr(result, queryables['apiso:Format']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:format')).text = val
                val = getattr(result, queryables['apiso:Type']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:type')).text = val
                val = getattr(result, queryables['apiso:Title']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:title')).text = val
                val = getattr(result, queryables['apiso:Modified']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dct:modified')).text = val
                val = getattr(result, queryables['apiso:BoundingBox']['obj_attr'])
                s = val.split(',')
                if len(s) == 4:
                    tmp=etree.SubElement(node, util.nspath_eval('ows:BoundingBox'))
                    etree.SubElement(tmp,
                    util.nspath_eval('ows:LowerCorner')).text = \
                    '%s %s' % (s[1], s[0])
                    etree.SubElement(tmp,
                    util.nspath_eval('ows:UpperCorner')).text = \
                    '%s %s' % (s[3], s[2])

            else: # summary
                node = etree.Element(util.nspath_eval('csw:SummaryRecord'))
                val = getattr(result, queryables['apiso:Identifier']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:identifier')).text = val
                val = getattr(result, queryables['apiso:Title']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:title')).text = val
                val = getattr(result, queryables['apiso:Type']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:type')).text = val
                val = getattr(result, queryables['apiso:Subject']['obj_attr'])
                for s in val.split(','):
                    etree.SubElement(node, util.nspath_eval('dc:subject')).text = val
                val = getattr(result, queryables['apiso:TopicCategory']['obj_attr'])
                for s in val.split(','):
                    etree.SubElement(node, util.nspath_eval('dc:subject')).text = val
                val = getattr(result, queryables['apiso:Format']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dc:format')).text = val
                val = getattr(result, queryables['apiso:Modified']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dct:modified')).text = val
                val = getattr(result, queryables['apiso:Abstract']['obj_attr'])
                etree.SubElement(node, util.nspath_eval('dct:abstract')).text = val

        return node

def write_extent(bbox):

    from shapely.wkt import loads

    if bbox is not None:
        extent = etree.Element(util.nspath_eval('gmd:extent'))
        ex_extent = etree.SubElement(extent, util.nspath_eval('gmd:EX_Extent'))
        ge = etree.SubElement(ex_extent, util.nspath_eval('gmd:geographicElement'))
        gbb = etree.SubElement(ge, util.nspath_eval('gmd:EX_GeographicBoundingBox'))
        west = etree.SubElement(gbb, util.nspath_eval('gmd:westBoundLongitude'))
        east = etree.SubElement(gbb, util.nspath_eval('gmd:eastBoundLongitude'))
        north = etree.SubElement(gbb, util.nspath_eval('gmd:northBoundLatitude'))
        south = etree.SubElement(gbb, util.nspath_eval('gmd:southBoundLatitude'))

        bbox2 = loads(bbox).exterior.bounds

        etree.SubElement(west, util.nspath_eval('gco:Decimal')).text = str(bbox2[0])
        etree.SubElement(south, util.nspath_eval('gco:Decimal')).text = str(bbox2[1])
        etree.SubElement(east, util.nspath_eval('gco:Decimal')).text = str(bbox2[2])
        etree.SubElement(north, util.nspath_eval('gco:Decimal')).text = str(bbox2[3])

        return extent

    return None
