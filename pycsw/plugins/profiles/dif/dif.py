# -*- coding: iso-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2011 Tom Kralidis
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
from pycsw import config, util
from pycsw.plugins.profiles import profile

class DIF(profile.Profile):
    ''' DIF class '''
    def __init__(self, model, namespaces, context):
        self.context = context

        self.namespaces = {
            'dif': 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/'
        }

        self.repository = {
            'dif:DIF': {
                'outputschema': 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/',
                'queryables': {
                    'SupportedDIFQueryables': {
                        'dif:Identifier': {'xpath': 'dif:Entry_Title', 'dbcol': self.context.md_core_model['mappings']['pycsw:Identifier']},
                        'dif:Entry_Title': {'xpath': 'dif:Entry_Title', 'dbcol': self.context.md_core_model['mappings']['pycsw:Title']},
                        'dif:Dataset_Creator': {'xpath': 'dif:Data_Set_Citation/dif:Dataset_Creator', 'dbcol': self.context.md_core_model['mappings']['pycsw:Creator']},
                        'dif:ISO_Topic_Category': {'xpath': 'dif:ISO_Topic_Category', 'dbcol': self.context.md_core_model['mappings']['pycsw:TopicCategory']},
                        'dif:Keyword': {'xpath': 'dif:Keyword', 'dbcol': self.context.md_core_model['mappings']['pycsw:Keywords']},
                        'dif:Summary': {'xpath': 'dif:Summary', 'dbcol': self.context.md_core_model['mappings']['pycsw:Abstract']},
                        'dif:Dataset_Publisher': {'xpath': 'dif:Data_Set_Citation/dif:Dataset_Publisher', 'dbcol': self.context.md_core_model['mappings']['pycsw:Publisher']},
                        'dif:Originating_Center': {'xpath': 'dif:Originating_Center', 'dbcol': self.context.md_core_model['mappings']['pycsw:OrganizationName']},
                        'dif:DIF_Creation_Date': {'xpath': 'dif:DIF_Creation_Date', 'dbcol': self.context.md_core_model['mappings']['pycsw:CreationDate']},
                        'dif:Dataset_Release_Date': {'xpath': 'dif:Data_Set_Citation/dif:Dataset_Release_Date', 'dbcol': self.context.md_core_model['mappings']['pycsw:PublicationDate']},
                        'dif:Data_Presentation_Form': {'xpath': 'dif:Data_Set_Citation/dif:Data_Presentation_Form', 'dbcol': self.context.md_core_model['mappings']['pycsw:Format']},
                        'dif:Data_Set_Language': {'xpath': 'dif:Data_Set_Language', 'dbcol': self.context.md_core_model['mappings']['pycsw:ResourceLanguage']},
                        'dif:Related_URL': {'xpath': 'dif:Related_URL/dif:URL', 'dbcol': self.context.md_core_model['mappings']['pycsw:Relation']},
                        'dif:Access_Constraints': {'xpath': 'dif:Access_Constraints', 'dbcol': self.context.md_core_model['mappings']['pycsw:AccessConstraints']},
                        'dif:Start_Date': {'xpath': 'dif:Temporal_Coverage/dif:Start_Date', 'dbcol': self.context.md_core_model['mappings']['pycsw:TempExtent_begin']},
                        'dif:Stop_Date': {'xpath': 'dif:Temporal_Coverage/dif:Stop_Date', 'dbcol': self.context.md_core_model['mappings']['pycsw:TempExtent_end']},
                        'dif:AnyText': {'xpath': '//', 'dbcol': self.context.md_core_model['mappings']['pycsw:AnyText']},
                        'dif:Spatial_Coverage': {'xpath': 'dif:Spatial_Coverage', 'dbcol': self.context.md_core_model['mappings']['pycsw:BoundingBox']}
                    }
                },
                'mappings': {
                    'csw:Record': {
                        # map DIF queryables to DC queryables
                        'dif:Entry_Title': 'dc:title',
                        'dif:Dataset_Creator': 'dc:creator',
                        'dif:Keyword': 'dc:subject',
                        'dif:Summary': 'dct:abstract',
                        'dif:Dataset_Publisher': 'dc:publisher',
                        'dif:Originating_Center': 'dc:contributor',
                        'dif:DIF_Creation_Date': 'dct:modified',
                        'dif:Dataset_Release_Date': 'dc:date',
                        'dif:Data_Presentation_Form': 'dc:type',
                        'dif:Data_Presentation_Form': 'dc:format',
                        'dif:Data_Set_Language': 'dc:language',
                        'dif:Access_Constraints': 'dc:rights',
                        'dif:Related_URL': 'dc:source',
                        'dif:AnyText': 'csw:AnyText',
                        'dif:Spatial_Coverage': 'ows:BoundingBox'
                    }
                }
            }
        }

        profile.Profile.__init__(self,
            name='dif',
            version='9.7',
            title='Directory Interchange Format',
            url='http://gcmd.nasa.gov/User/difguide/difman.html',
            namespace=self.namespaces['dif'],
            typename='dif:DIF',
            outputschema=self.namespaces['dif'],
            prefixes=['dif'],
            model=model,
            core_namespaces=namespaces,
            added_namespaces=self.namespaces,
            repository=self.repository['dif:DIF'])

    def extend_core(self, model, namespaces, config):
        ''' Extend core configuration '''
        return None

    def check_parameters(self, kvp):
        '''Perform extra parameters checking '''
        return None

    def get_extendedcapabilities(self):
        ''' Add child to ows:OperationsMetadata Element '''
        return None

    def get_schemacomponents(self):
        ''' Return schema components as lxml.etree.Element list '''

        node = etree.Element(
        util.nspath_eval('csw:SchemaComponent', self.context.namespaces),
        schemaLanguage='XMLSCHEMA', targetNamespace=self.namespace)

        schema = etree.parse(os.path.join(self.context.pycsw_home,
                 'plugins', 'profiles', 'dif',
                 'schemas', 'dif', 'dif.xsd')).getroot()
        node.append(schema)

        return [node]

    def check_getdomain(self, kvp):
        '''Perform extra profile specific checks in the GetDomain request'''
        return None

    def write_record(self, result, esn, outputschema, queryables):
        ''' Return csw:SearchResults child as lxml.etree.Element '''

        typename = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Typename'])

        if esn == 'full' and typename == 'dif:DIF':
            # dump record as is and exit
            return etree.fromstring(util.getqattr(result, self.context.md_core_model['mappings']['pycsw:XML']))

        if typename == 'csw:Record':  # transform csw:Record -> dif:DIF model mappings
            util.transform_mappings(queryables, self.repository['mappings']['csw:Record'])

        node = etree.Element(util.nspath_eval('dif:DIF', self.namespaces))
        node.attrib[util.nspath_eval('xsi:schemaLocation', self.context.namespaces)] = \
        '%s http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/dif.xsd' % self.namespace

        # identifier
        etree.SubElement(node, util.nspath_eval('dif:Entry_ID', self.namespaces)).text = util.getqattr(result, queryables['dif:Identifier']['dbcol'])

        # title
        val = util.getqattr(result, queryables['dif:Entry_Title']['dbcol'])
        if not val:
            val = ''
        etree.SubElement(node, util.nspath_eval('dif:Entry_Title', self.namespaces)).text = val

        # citation
        citation = etree.SubElement(node, util.nspath_eval('dif:Data_Set_Citation', self.namespaces))

        # creator
        val = util.getqattr(result, queryables['dif:Dataset_Creator']['dbcol'])
        etree.SubElement(citation, util.nspath_eval('dif:Dataset_Creator', self.namespaces)).text = val

        # date
        val = util.getqattr(result, queryables['dif:Dataset_Release_Date']['dbcol'])
        etree.SubElement(citation, util.nspath_eval('dif:Dataset_Release_Date', self.namespaces)).text = val

        # publisher
        val = util.getqattr(result, queryables['dif:Dataset_Publisher']['dbcol'])
        etree.SubElement(citation, util.nspath_eval('dif:Dataset_Publisher', self.namespaces)).text = val

        # format
        val = util.getqattr(result, queryables['dif:Data_Presentation_Form']['dbcol'])
        etree.SubElement(citation, util.nspath_eval('dif:Data_Presentation_Form', self.namespaces)).text = val

        # iso topic category
        val = util.getqattr(result, queryables['dif:ISO_Topic_Category']['dbcol'])
        etree.SubElement(node, util.nspath_eval('dif:ISO_Topic_Category', self.namespaces)).text = val

        # keywords
        val = util.getqattr(result, queryables['dif:Keyword']['dbcol'])

        if val:
            for kw in val.split(','):
                etree.SubElement(node, util.nspath_eval('dif:Keyword', self.namespaces)).text = kw

        # temporal
        temporal = etree.SubElement(node, util.nspath_eval('dif:Temporal_Coverage', self.namespaces))
        val = util.getqattr(result, queryables['dif:Start_Date']['dbcol'])
        val2 = util.getqattr(result, queryables['dif:Stop_Date']['dbcol'])
        etree.SubElement(temporal, util.nspath_eval('dif:Start_Date', self.namespaces)).text = val 
        etree.SubElement(temporal, util.nspath_eval('dif:End_Date', self.namespaces)).text = val2

        # bbox extent
        val = util.getqattr(result, queryables['dif:Spatial_Coverage']['dbcol'])
        bboxel = write_extent(val, self.namespaces)
        if bboxel is not None:
            node.append(bboxel)

        # access constraints
        val = util.getqattr(result, queryables['dif:Access_Constraints']['dbcol'])
        etree.SubElement(node, util.nspath_eval('dif:Access_Constraints', self.namespaces)).text = val

        # language
        val = util.getqattr(result, queryables['dif:Data_Set_Language']['dbcol'])
        etree.SubElement(node, util.nspath_eval('dif:Data_Set_Language', self.namespaces)).text = val

        # contributor
        val = util.getqattr(result, queryables['dif:Originating_Center']['dbcol'])
        etree.SubElement(node, util.nspath_eval('dif:Originating_Center', self.namespaces)).text = val

        # abstract
        val = util.getqattr(result, queryables['dif:Summary']['dbcol'])
        if not val:
            val = ''
        etree.SubElement(node, util.nspath_eval('dif:Summary', self.namespaces)).text = val

        # date 
        val = util.getqattr(result, queryables['dif:DIF_Creation_Date']['dbcol'])
        etree.SubElement(node, util.nspath_eval('dif:DIF_Creation_Date', self.namespaces)).text = val

        # URL
        val = util.getqattr(result, queryables['dif:Related_URL']['dbcol'])
        url = etree.SubElement(node, util.nspath_eval('dif:Related_URL', self.namespaces))
        etree.SubElement(url, util.nspath_eval('dif:URL', self.namespaces)).text = val

        rlinks = util.getqattr(result, self.context.md_core_model['mappings']['pycsw:Links'])
        if rlinks:
            for link in rlinks.split('^'):
                linkset = link.split(',')
           
                url2 = etree.SubElement(node, util.nspath_eval('dif:Related_URL', self.namespaces))

                urltype = etree.SubElement(url2, util.nspath_eval('dif:URL_Content_Type', self.namespaces))
                etree.SubElement(urltype, util.nspath_eval('dif:Type', self.namespaces)).text = linkset[2]

                etree.SubElement(url2, util.nspath_eval('dif:URL', self.namespaces)).text = linkset[-1]
                etree.SubElement(url2, util.nspath_eval('dif:Description', self.namespaces)).text = linkset[1]

        etree.SubElement(node, util.nspath_eval('dif:Metadata_Name', self.namespaces)).text = 'CEOS IDN DIF'
        etree.SubElement(node, util.nspath_eval('dif:Metadata_Version', self.namespaces)).text = '9.7'

        return node

def write_extent(bbox, nsmap):
    ''' Generate BBOX extent '''

    from shapely.wkt import loads

    if bbox is not None:
        if bbox.find('SRID') != -1:  # it's EWKT; chop off 'SRID=\d+;'
            bbox2 = loads(bbox.split(';')[-1]).envelope.bounds
        else:
            bbox2 = loads(bbox).envelope.bounds
        extent = etree.Element(util.nspath_eval('dif:Spatial_Coverage', nsmap))
        etree.SubElement(extent, util.nspath_eval('dif:Southernmost_Latitude', nsmap)).text = str(bbox2[1])
        etree.SubElement(extent, util.nspath_eval('dif:Northernmost_Latitude', nsmap)).text = str(bbox2[3])
        etree.SubElement(extent, util.nspath_eval('dif:Westernmost_Longitude', nsmap)).text = str(bbox2[0])
        etree.SubElement(extent, util.nspath_eval('dif:Easternmost_Longitude', nsmap)).text = str(bbox2[2])
        return extent
    return None
