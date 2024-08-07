# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2024 Tom Kralidis
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

from pycsw.core import util
from pycsw.core.etree import etree

NAMESPACE = 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/'
NAMESPACES = {'dif': NAMESPACE}

XPATH_MAPPINGS = {
    'pycsw:Title': 'dif:Entry_Title',
    'pycsw:Creator': 'dif:Data_Set_Citation/dif:Dataset_Creator',
    'pycsw:TopicCategory': 'dif:ISO_Topic_Category',
    'pycsw:Keywords': 'dif:Keyword',
    'pycsw:Abstract': 'dif:Summary',
    'pycsw:Publisher': 'dif:Data_Set_Citation/dif:Dataset_Publisher',
    'pycsw:OrganizationName': 'dif:Originating_Center',
    'pycsw:CreationDate': 'dif:DIF_Creation_Date','pycsw:PublicationDate': 'dif:Data_Set_Citation/dif:Dataset_Release_Date',
    'pycsw:Format': 'dif:Data_Set_Citation/dif:Data_Presentation_Form',
    'pycsw:ResourceLanguage': 'dif:Data_Set_Language',
    'pycsw:Relation': 'dif:Related_URL/dif:URL',
    'pycsw:AccessConstraints': 'dif:Access_Constraints',
    'pycsw:TempExtent_begin': 'dif:Temporal_Coverage/dif:Start_Date',
    'pycsw:TempExtent_end': 'dif:Temporal_Coverage/dif:Stop_Date',
}

def write_record(result, esn, context, url=None):
    ''' Return csw:SearchResults child as lxml.etree.Element '''

    typename = util.getqattr(result, context.md_core_model['mappings']['pycsw:Typename'])

    if esn == 'full' and typename == 'dif:DIF':
        # dump record as is and exit
        return etree.fromstring(util.getqattr(result, context.md_core_model['mappings']['pycsw:XML']), context.parser)

    node = etree.Element(util.nspath_eval('dif:DIF', NAMESPACES))
    node.attrib[util.nspath_eval('xsi:schemaLocation', context.namespaces)] = \
    '%s http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/dif.xsd' % NAMESPACE

    # identifier
    etree.SubElement(node, util.nspath_eval('dif:Entry_ID', NAMESPACES)).text = util.getqattr(result, context.md_core_model['mappings']['pycsw:Identifier'])

    # title
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Title'])
    if not val:
        val = ''
    etree.SubElement(node, util.nspath_eval('dif:Entry_Title', NAMESPACES)).text = val

    # citation
    citation = etree.SubElement(node, util.nspath_eval('dif:Data_Set_Citation', NAMESPACES))

    # creator
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Creator'])
    etree.SubElement(citation, util.nspath_eval('dif:Dataset_Creator', NAMESPACES)).text = val

    # date
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:PublicationDate'])
    etree.SubElement(citation, util.nspath_eval('dif:Dataset_Release_Date', NAMESPACES)).text = val

    # publisher
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Publisher'])
    etree.SubElement(citation, util.nspath_eval('dif:Dataset_Publisher', NAMESPACES)).text = val

    # format
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Format'])
    etree.SubElement(citation, util.nspath_eval('dif:Data_Presentation_Form', NAMESPACES)).text = val

    # keywords dif:Parameters
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Keywords'])
    if val:
        kws = val.split(',')
        parameters_indexes = []
        for index, kw in enumerate(kws):
            if "Earth Science".lower() in kw.lower() and len(kw.split(">")) >= 2:
                values = kw.upper().split(">")
                parameters = etree.SubElement(node, util.nspath_eval('dif:Parameters', NAMESPACES))  # .text = kw
                etree.SubElement(parameters, util.nspath_eval('dif:Category', NAMESPACES)).text = values[0].strip().upper()
                etree.SubElement(parameters, util.nspath_eval('dif:Topic', NAMESPACES)).text = values[1].strip().upper()
                etree.SubElement(parameters, util.nspath_eval('dif:Term', NAMESPACES)).text = values[2].strip().upper()
                for i, v in enumerate(values[3:]):
                    etree.SubElement(parameters, util.nspath_eval(f'dif:Variable_Level_{i + 1}', NAMESPACES)).text = v.strip()
                parameters_indexes.append(index)
                # kws.pop(index)

    # iso topic category
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:TopicCategory'])
    etree.SubElement(node, util.nspath_eval('dif:ISO_Topic_Category', NAMESPACES)).text = val

    # keywords dif:keywords
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Keywords'])
    if val:
        kws = val.split(',')
        kws = [i for j, i in enumerate(kws) if j not in parameters_indexes]
        for index, kw in enumerate(kws):
            etree.SubElement(node, util.nspath_eval('dif:Keyword', NAMESPACES)).text = kw.strip()

    # temporal
    temporal = etree.SubElement(node, util.nspath_eval('dif:Temporal_Coverage', NAMESPACES))
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:TempExtent_begin'])
    val2 = util.getqattr(result, context.md_core_model['mappings']['pycsw:TempExtent_end'])
    etree.SubElement(temporal, util.nspath_eval('dif:Start_Date', NAMESPACES)).text = val
    etree.SubElement(temporal, util.nspath_eval('dif:End_Date', NAMESPACES)).text = val2

    # bbox extent
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:BoundingBox'])
    bboxel = write_extent(val, NAMESPACES)
    if bboxel is not None:
        node.append(bboxel)

    # access constraints
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:AccessConstraints'])
    etree.SubElement(node, util.nspath_eval('dif:Access_Constraints', NAMESPACES)).text = val

    # language
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:ResourceLanguage'])
    etree.SubElement(node, util.nspath_eval('dif:Data_Set_Language', NAMESPACES)).text = val

    # contributor
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:OrganizationName'])
    etree.SubElement(node, util.nspath_eval('dif:Originating_Center', NAMESPACES)).text = val

    # abstract
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Abstract'])
    if not val:
        val = ''
    etree.SubElement(node, util.nspath_eval('dif:Summary', NAMESPACES)).text = val

    # URL
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Relation'])
    if val:
        url = etree.SubElement(node, util.nspath_eval('dif:Related_URL', NAMESPACES))
        etree.SubElement(url, util.nspath_eval('dif:URL', NAMESPACES)).text = val

    rlinks = util.getqattr(result, context.md_core_model['mappings']['pycsw:Links'])
    if rlinks:
        for link in util.jsonify_links(rlinks):
            url2 = etree.SubElement(node, util.nspath_eval('dif:Related_URL', NAMESPACES))

            urltype = etree.SubElement(url2, util.nspath_eval('dif:URL_Content_Type', NAMESPACES))
            if link['protocol'] == 'download':
                etree.SubElement(urltype, util.nspath_eval('dif:Type', NAMESPACES)).text = 'GET DATA'
            elif link['protocol'] == 'OPENDAP:OPENDAP':
                etree.SubElement(urltype, util.nspath_eval('dif:Type', NAMESPACES)).text = 'GET DATA'
                etree.SubElement(urltype, util.nspath_eval('dif:Subtype', NAMESPACES)).text = 'OPENDAP DATA (DODS)'
            elif link['protocol'] == 'OGC:WMS':
                etree.SubElement(urltype, util.nspath_eval('dif:Type', NAMESPACES)).text = 'GET SERVICE'
                etree.SubElement(urltype, util.nspath_eval('dif:Subtype', NAMESPACES)).text = 'GET WEB MAP SERVICE (WMS)'
            else:
                etree.SubElement(urltype, util.nspath_eval('dif:Type', NAMESPACES)).text = 'GET DATA'

            etree.SubElement(url2, util.nspath_eval('dif:URL', NAMESPACES)).text = link['url']
            if link['description']:
                etree.SubElement(url2, util.nspath_eval('dif:Description', NAMESPACES)).text = link['description']

    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Source'])
    if val:
        url2 = etree.SubElement(node, util.nspath_eval('dif:Related_URL', NAMESPACES))
        urltype = etree.SubElement(url2, util.nspath_eval('dif:URL_Content_Type', NAMESPACES))
        etree.SubElement(urltype, util.nspath_eval('dif:Type', NAMESPACES)).text = 'DATASET LANDING PAGE'
        etree.SubElement(url2, util.nspath_eval('dif:URL', NAMESPACES)).text = val

    etree.SubElement(node, util.nspath_eval('dif:Metadata_Name', NAMESPACES)).text = 'CEOS IDN DIF'
    etree.SubElement(node, util.nspath_eval('dif:Metadata_Version', NAMESPACES)).text = '9.7'

    # date
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:CreationDate'])
    etree.SubElement(node, util.nspath_eval('dif:DIF_Creation_Date', NAMESPACES)).text = val

    return node

def write_extent(bbox, nsmap):
    ''' Generate BBOX extent '''

    if bbox is not None:
        try:
            bbox2 = util.wkt2geom(bbox)
        except Exception as err:
            LOGGER.debug(f'Geometry parsing error: {err}')
            return None
        extent = etree.Element(util.nspath_eval('dif:Spatial_Coverage', nsmap))
        etree.SubElement(extent, util.nspath_eval('dif:Southernmost_Latitude', nsmap)).text = str(bbox2[1])
        etree.SubElement(extent, util.nspath_eval('dif:Northernmost_Latitude', nsmap)).text = str(bbox2[3])
        etree.SubElement(extent, util.nspath_eval('dif:Westernmost_Longitude', nsmap)).text = str(bbox2[0])
        etree.SubElement(extent, util.nspath_eval('dif:Easternmost_Longitude', nsmap)).text = str(bbox2[2])
        return extent
    return None
