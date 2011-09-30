# -*- coding: ISO-8859-15 -*-
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
from server import config, util
from server.plugins.profiles import profile

NAMESPACES = {
    'dif': 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/'
}

REPOSITORY = {
    'dif:DIF': {
        'outputschema': 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/',
        'queryables': {
            'SupportedDIFQueryables': {
                'dif:Entry_Title': {'xpath': 'dif:Entry_Title', 'dbcol': 'title'},
                'dif:Dataset_Creator': {'xpath': 'dif:Data_Set_Citation/dif:Dataset_Creator', 'dbcol': 'creator'},
                'dif:Keyword': {'xpath': 'dif:Keyword', 'dbcol': 'keywords'},
                'dif:Summary': {'xpath': 'dif:Summary', 'dbcol': 'abstract'},
                'dif:Dataset_Publisher': {'xpath': 'dif:Data_Set_Citation/dif:Dataset_Publisher', 'dbcol': 'publisher'},
                'dif:Originating_Center': {'xpath': 'dif:Originating_Center', 'dbcol': 'organization'},
                'dif:DIF_Creation_Date': {'xpath': 'dif:DIF_Creation_Date', 'dbcol': 'date_creation'},
                'dif:Dataset_Release_Date': {'xpath': 'dif:Data_Set_Citation/dif:Dataset_Release_Date', 'dbcol': 'date_publication'},
                'dif:Data_Presentation_Form': {'xpath': 'dif:Data_Set_Citation/dif:Data_Presentation_Form', 'dbcol': 'format'},
                'dif:Data_Set_Language': {'xpath': 'dif:Data_Set_Language', 'dbcol': 'resourcelanguage'},
                'dif:Related_URL': {'xpath': 'dif:Related_URL/dif:URL', 'dbcol': 'relation'},
                'dif:Access_Constraints': {'xpath': 'dif:Access_Constraints', 'dbcol': 'accessconstraints'},
                'dif:AnyText': {'xpath': '//', 'dbcol': 'anytext'},
                'dif:Spatial_Coverage': {'xpath': 'dif:Spatial_Coverage', 'dbcol': 'geometry'}
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

class DIF(profile.Profile):
    ''' DIF class '''
    def __init__(self, model, namespaces):
        profile.Profile.__init__(self,
            name='dif',
            version='9.7',
            title='Directory Interchange Format',
            url='http://gcmd.nasa.gov/User/difguide/difman.html',
            namespace=NAMESPACES['dif'],
            typename='dif:DIF',
            outputschema=NAMESPACES['dif'],
            prefixes=['dif'],
            model=model,
            core_namespaces=namespaces,
            added_namespaces=NAMESPACES,
            repository=REPOSITORY['dif:DIF'])

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
        util.nspath_eval('csw:SchemaComponent'),
        schemaLanguage = 'XMLSCHEMA', targetNamespace = self.namespace)

        schema = etree.parse(os.path.join(
                'server', 'plugins', 'profiles', 'dif',
                'etc', 'schemas', 'dif', 'dif.xsd')).getroot()
        node.append(schema)

        return [node]

    def check_getdomain(self, kvp):
        '''Perform extra profile specific checks in the GetDomain request'''
        return None

    def write_record(self, result, esn, outputschema, queryables):
        ''' Return csw:SearchResults child as lxml.etree.Element '''
        xml = etree.fromstring(result.xml)
        if outputschema == self.namespace:
            if esn == 'full':  # dump the full record
                node = xml
            else:  # it's a brief or summary record

                if result.typename == 'csw:Record':  # transform csw:Record -> dif:DIF model mappings
                    util.transform_mappings(queryables, REPOSITORY['dif:DIF']['mappings']['csw:Record'])

                node = etree.Element(util.nspath_eval('dif:DIF'))
                node.attrib[util.nspath_eval('xsi:schemaLocation')] = \
                '%s http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/dif.xsd' % self.namespace

                # identifier
                etree.SubElement(node, util.nspath_eval('dif:Entry_ID')).text = result.identifier

                # title
                val = getattr(result, queryables['dif:Entry_Title']['dbcol'])
                if not val:
                    val = ''
                etree.SubElement(node, util.nspath_eval('dif:Entry_Title')).text = val

                # citation
                citation = etree.SubElement(node, util.nspath_eval('dif:Data_Set_Citation'))

                # creator
                val = getattr(result, queryables['dif:Dataset_Creator']['dbcol'])
                etree.SubElement(citation, util.nspath_eval('dif:Dataset_Creator')).text = val

                # date
                val = getattr(result, queryables['dif:Dataset_Release_Date']['dbcol'])
                etree.SubElement(citation, util.nspath_eval('dif:Dataset_Release_Date')).text = val

                # publisher
                val = getattr(result, queryables['dif:Dataset_Publisher']['dbcol'])
                etree.SubElement(citation, util.nspath_eval('dif:Dataset_Publisher')).text = val

                # format
                val = getattr(result, queryables['dif:Data_Presentation_Form']['dbcol'])
                etree.SubElement(citation, util.nspath_eval('dif:Data_Presentation_Form')).text = val

                # keywords
                val = getattr(result, queryables['dif:Keyword']['dbcol'])

                if val:
                    for kw in val.split(','):
                        etree.SubElement(node, util.nspath_eval('dif:Keyword')).text = kw

                # bbox extent
                val = getattr(result, queryables['dif:Spatial_Coverage']['dbcol'])
                bboxel = write_extent(val)
                if bboxel is not None:
                    node.append(bboxel)

                # access constraints
                val = getattr(result, queryables['dif:Access_Constraints']['dbcol'])
                etree.SubElement(node, util.nspath_eval('dif:Access_Constraints')).text = val

                # language
                val = getattr(result, queryables['dif:Data_Set_Language']['dbcol'])
                etree.SubElement(node, util.nspath_eval('dif:Data_Set_Language')).text = val

                # contributor
                val = getattr(result, queryables['dif:Originating_Center']['dbcol'])
                etree.SubElement(node, util.nspath_eval('dif:Originating_Center')).text = val

                # abstract
                val = getattr(result, queryables['dif:Summary']['dbcol'])
                if not val:
                    val = ''
                etree.SubElement(node, util.nspath_eval('dif:Summary')).text = val

                # date 
                val = getattr(result, queryables['dif:DIF_Creation_Date']['dbcol'])
                etree.SubElement(node, util.nspath_eval('dif:DIF_Creation_Date')).text = val

                # URL
                val = getattr(result, queryables['dif:Related_URL']['dbcol'])
                url = etree.SubElement(node, util.nspath_eval('dif:Related_URL'))
                etree.SubElement(url, util.nspath_eval('dif:URL')).text = val

                etree.SubElement(url, util.nspath_eval('dif:Metadata_Name')).text = 'CEOS IDN DIF'
                etree.SubElement(url, util.nspath_eval('dif:Metadata_Version')).text = '9.7'

        return node

def write_extent(bbox):
    ''' Generate BBOX extent '''

    from shapely.wkt import loads

    if bbox is not None:
        bbox2 = loads(bbox).exterior.bounds
        extent = etree.Element(util.nspath_eval('dif:Spatial_Coverage'))
        etree.SubElement(extent, util.nspath_eval('dif:Southernmost_Latitude')).text = str(bbox2[1])
        etree.SubElement(extent, util.nspath_eval('dif:Northernmost_Latitude')).text = str(bbox2[3])
        etree.SubElement(extent, util.nspath_eval('dif:Westernmost_Longitude')).text = str(bbox2[0])
        etree.SubElement(extent, util.nspath_eval('dif:Easternmost_Longitude')).text = str(bbox2[2])
        return extent
    return None
