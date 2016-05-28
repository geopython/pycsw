# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
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

NAMESPACE = 'http://www.interlis.ch/INTERLIS2.3'
NAMESPACES = {'gm03': NAMESPACE}

XPATH_MAPPINGS = {}

def write_record(result, esn, context, url=None):
    ''' Return csw:SearchResults child as lxml.etree.Element '''

    typename = util.getqattr(result, context.md_core_model['mappings']['pycsw:Typename'])

    if typename == 'gm03:TRANSFER':
        # dump record as is and exit
        # TODO: provide brief and summary elementsetname's
        return etree.fromstring(util.getqattr(result, context.md_core_model['mappings']['pycsw:XML']), context.parser)

    node = etree.Element(util.nspath_eval('gm03:TRANSFER', NAMESPACES), nsmap=NAMESPACES)

    header = etree.SubElement(node, util.nspath_eval('gm03:HEADERSECTION', NAMESPACES))
    header.attrib['version'] = '2.3'
    header.attrib['sender'] = 'pycsw'

    etree.SubElement(header, util.nspath_eval('gm03:MODELS', NAMESPACES))

    data = etree.SubElement(node, util.nspath_eval('gm03:DATASECTION', NAMESPACES))

    core = etree.SubElement(data, util.nspath_eval('gm03:GM03_2_1Core.Core', NAMESPACES))
    core_meta = etree.SubElement(core, util.nspath_eval('gm03:GM03_2_1Core.Core.MD_Metadata', NAMESPACES))

    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Identifier'])
    etree.SubElement(core_meta, util.nspath_eval('gm03:fileIdentifier', NAMESPACES)).text = val

    language = util.getqattr(result, context.md_core_model['mappings']['pycsw:Language'])
    etree.SubElement(core_meta, util.nspath_eval('gm03:language', NAMESPACES)).text = language

    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Modified'])
    etree.SubElement(core_meta, util.nspath_eval('gm03:dateStamp', NAMESPACES)).text = val

    hierarchy_level_val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Type'])

    # metadata standard name
    standard = etree.SubElement(core_meta, util.nspath_eval('gm03:metadataStandardName', NAMESPACES)).text = 'GM03'

    # metadata standard version
    standardver = etree.SubElement(core_meta, util.nspath_eval('gm03:metadataStandardVersion', NAMESPACES)).text = '2.3'

    # hierarchy level
    hierarchy_level = etree.SubElement(core_meta, util.nspath_eval('gm03:hierarchyLevel', NAMESPACES))
    scope_code = etree.SubElement(hierarchy_level, util.nspath_eval('gm03:GM03_2_1Core.Core.MD_ScopeCode_', NAMESPACES))
    etree.SubElement(scope_code, util.nspath_eval('gm03:value', NAMESPACES)).text = hierarchy_level_val

    # parent identifier
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:ParentIdentifier'])
    parent_identifier = etree.SubElement(core_meta, util.nspath_eval('gm03:parentIdentifier', NAMESPACES))
    scope_code = etree.SubElement(parent_identifier, util.nspath_eval('gm03:GM03_2_1Core.Core.MD_ScopeCode_', NAMESPACES))
    etree.SubElement(scope_code, util.nspath_eval('gm03:value', NAMESPACES)).text = val

    # title
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Title'])
    citation = etree.SubElement(core, util.nspath_eval('gm03:GM03_2_1Core.Core.CI_Citation', NAMESPACES))
    title = etree.SubElement(citation, util.nspath_eval('gm03:title', NAMESPACES))
    title.append(_get_pt_freetext(val, language))

    # abstract
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Abstract'])
    data_ident = etree.SubElement(core, util.nspath_eval('gm03:GM03_2_1Core.Core.MD_DataIdentification', NAMESPACES))
    abstract = etree.SubElement(data_ident, util.nspath_eval('gm03:abstract', NAMESPACES))
    abstract.append(_get_pt_freetext(val, language))

    # resource language
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:ResourceLanguage'])
    if val:
        topicategory = etree.SubElement(data_ident, util.nspath_eval('gm03:language', NAMESPACES))
        cat_code = etree.SubElement(topicategory, util.nspath_eval('gm03:CodeISO.LanguageCodeISO_', NAMESPACES))
        etree.SubElement(cat_code, util.nspath_eval('gm03:value', NAMESPACES)).text = val

    # topic category
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:TopicCategory'])
    if val:
        topicategory = etree.SubElement(data_ident, util.nspath_eval('gm03:topicCategory', NAMESPACES))
        cat_code = etree.SubElement(topicategory, util.nspath_eval('gm03:GM03_2_1Core.Core.MD_TopicCategoryCode_', NAMESPACES))
        etree.SubElement(cat_code, util.nspath_eval('gm03:value', NAMESPACES)).text = val

    # keywords
    keywords_val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Keywords'])

    if keywords_val:
        md_keywords = etree.SubElement(core, util.nspath_eval('gm03:GM03_2_1Core.Core.MD_Keywords', NAMESPACES))

        val = util.getqattr(result, context.md_core_model['mappings']['pycsw:KeywordType'])
        if val:
            etree.SubElement(md_keywords, util.nspath_eval('gm03:type', NAMESPACES)).text = val

        keyword = etree.SubElement(md_keywords, util.nspath_eval('gm03:keyword', NAMESPACES))
        for kw in keywords_val.split(','):
            keyword.append(_get_pt_freetext(kw, language))

    # format
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:Format'])
    if val:
        md_format = etree.SubElement(core, util.nspath_eval('gm03:GM03_2_1Core.Core.MD_Format', NAMESPACES))
        etree.SubElement(md_format, util.nspath_eval('gm03:name', NAMESPACES)).text = val

    # creation date
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:CreationDate'])
    if val:
        ci_date = etree.SubElement(core, util.nspath_eval('gm03:GM03_2_1Core.Core.CI_Date', NAMESPACES))
        etree.SubElement(ci_date, util.nspath_eval('gm03:date', NAMESPACES)).text = val
        etree.SubElement(ci_date, util.nspath_eval('gm03:dateType', NAMESPACES)).text = 'creation'

    # revision date
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:RevisionDate'])
    if val:
        ci_date = etree.SubElement(core, util.nspath_eval('gm03:GM03_2_1Core.Core.CI_Date', NAMESPACES))
        etree.SubElement(ci_date, util.nspath_eval('gm03:date', NAMESPACES)).text = val
        etree.SubElement(ci_date, util.nspath_eval('gm03:dateType', NAMESPACES)).text = 'revision'

    # publication date
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:PublicationDate'])
    if val:
        ci_date = etree.SubElement(core, util.nspath_eval('gm03:GM03_2_1Core.Core.CI_Date', NAMESPACES))
        etree.SubElement(ci_date, util.nspath_eval('gm03:date', NAMESPACES)).text = val
        etree.SubElement(ci_date, util.nspath_eval('gm03:dateType', NAMESPACES)).text = 'publication'

    # bbox extent
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:BoundingBox'])
    bboxel = write_extent(val, context.namespaces)
    if bboxel is not None:
        core.append(bboxel)

    # geographic description
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:GeographicDescriptionCode'])
    if val:
        geo_desc = etree.SubElement(core, util.nspath_eval('gm03:GM03_2_1Core.Core.EX_GeographicDescription', NAMESPACES))
        etree.SubElement(geo_desc, util.nspath_eval('gm03:geographicIdentifier', NAMESPACES)).text = val

    # crs
    val = util.getqattr(result, context.md_core_model['mappings']['pycsw:CRS'])
    if val:
        rs_identifier = etree.SubElement(core, util.nspath_eval('gm03:GM03_2_1Core.Core.RS_Identifier', NAMESPACES))
        rs_code = etree.SubElement(rs_identifier, util.nspath_eval('gm03:code', NAMESPACES))
        rs_code.append(_get_pt_freetext(val, language))

    # temporal extent
    time_begin = util.getqattr(result, context.md_core_model['mappings']['pycsw:TempExtent_begin'])
    time_end = util.getqattr(result, context.md_core_model['mappings']['pycsw:TempExtent_end'])
    if time_begin:
        temp_ext = etree.SubElement(core, util.nspath_eval('gm03:GM03_2_1Core.Core.EX_TemporalExtent', NAMESPACES))
        extent = etree.SubElement(temp_ext, util.nspath_eval('gm03:extent', NAMESPACES))
        tm_primitive = etree.SubElement(extent, util.nspath_eval('gm03:GM03_2_1Core.Core.TM_Primitive', NAMESPACES))
        etree.SubElement(tm_primitive, util.nspath_eval('gm03:begin', NAMESPACES)).text = time_begin
        if time_end:
            etree.SubElement(tm_primitive, util.nspath_eval('gm03:end', NAMESPACES)).text = time_end

    # links
    rlinks = util.getqattr(result, context.md_core_model['mappings']['pycsw:Links'])
    if rlinks:
        for link in rlinks.split('^'):
            name, description, protocol, url = link.split(',')
            online_resource = etree.SubElement(core, util.nspath_eval('gm03:GM03_2_1Core.Core.OnlineResource', NAMESPACES))
            if protocol:
                etree.SubElement(online_resource, util.nspath_eval('gm03:protocol', NAMESPACES)).text = protocol
            if description:
                desc = etree.SubElement(online_resource, util.nspath_eval('gm03:description', NAMESPACES))
                desc.append(_get_pt_freetext(description, language))
            if name:
                name_el = etree.SubElement(online_resource, util.nspath_eval('gm03:name', NAMESPACES))
                name_el.append(_get_pt_freetext(name, language))
            linkage = etree.SubElement(online_resource, util.nspath_eval('gm03:linkage', NAMESPACES))
            linkage.append(_get_pt_freeurl(url, language))

    return node

def _get_pt_freetext(val, language):
    freetext = etree.Element(util.nspath_eval('gm03:GM03_2_1Core.Core.PT_FreeText', NAMESPACES))
    textgroup = etree.SubElement(freetext, util.nspath_eval('gm03:textGroup', NAMESPACES))
    ptgroup = etree.SubElement(textgroup, util.nspath_eval('gm03:GM03_2_1Core.Core.PT_Group', NAMESPACES))
    if language:
        etree.SubElement(ptgroup, util.nspath_eval('gm03:language', NAMESPACES)).text = language
    etree.SubElement(ptgroup, util.nspath_eval('gm03:plainText', NAMESPACES)).text = val

    return freetext

def _get_pt_freeurl(val, language):
    freeurl = etree.Element(util.nspath_eval('gm03:GM03_2_1Core.Core.PT_FreeURL', NAMESPACES))
    urlgroup = etree.SubElement(freeurl, util.nspath_eval('gm03:URLGroup', NAMESPACES))
    ptgroup = etree.SubElement(urlgroup, util.nspath_eval('gm03:GM03_2_1Core.Core.PT_URLGroup', NAMESPACES))
    if language:
        etree.SubElement(ptgroup, util.nspath_eval('gm03:language', NAMESPACES)).text = language
    etree.SubElement(ptgroup, util.nspath_eval('gm03:plainURL', NAMESPACES)).text = val

    return freeurl

def write_extent(bbox, nsmap):
    ''' Generate BBOX extent '''
    
    if bbox is not None:
        try:
            bbox2 = util.wkt2geom(bbox)
        except:
            return None
        bounding_box = etree.Element(util.nspath_eval('gm03:GM03_2_1Core.Core.EX_GeographicBoundingBox', NAMESPACES))
        etree.SubElement(bounding_box, util.nspath_eval('gm03:northBoundLatitude', nsmap)).text = str(bbox2[3])
        etree.SubElement(bounding_box, util.nspath_eval('gm03:southBoundLatitude', nsmap)).text = str(bbox2[1])
        etree.SubElement(bounding_box, util.nspath_eval('gm03:eastBoundLongitude', nsmap)).text = str(bbox2[0])
        etree.SubElement(bounding_box, util.nspath_eval('gm03:westBoundLongitude', nsmap)).text = str(bbox2[2])
        return bounding_box
    return None
