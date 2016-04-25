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

#NAMESPACE = 'http://www.fgdc.gov/metadata/csdgm'
NAMESPACE = 'http://www.opengis.net/cat/csw/csdgm'
NAMESPACES = {'fgdc': NAMESPACE}

XPATH_MAPPINGS = {
    'pycsw:Identifier': 'idinfo/datasetid',
    'pycsw:Title': 'idinfo/citation/citeinfo/title',
    'pycsw:Creator': 'idinfo/citation/citeinfo/origin',
    'pycsw:Publisher': 'idinfo/citation/citeinfo/publinfo/publish',
    'pycsw:Abstract': 'idinfo/descript/abstract',
    'pycsw:Format': 'idinfo/citation/citeinfo/geoform',
    'pycsw:PublicationDate': 'idinfo/citation/citeinfo/pubdate',
    'pycsw:Keywords': 'idinfo/keywords/theme/themekey',
    'pycsw:TempExtent_begin': 'idinfo/timeperd/timeinfo/rngdates/begdate',
    'pycsw:TempExtent_end': 'idinfo/timeperd/timeinfo/rngdates/enddate',
    'pycsw:Contributor': 'idinfo/datacred',
    'pycsw:AccessConstraints': 'idinfo/accconst',
    'pycsw:Modified': 'metainfo/metd',
    'pycsw:Type': 'spdoinfo/direct',
    'pycsw:Source': 'lineage/srcinfo/srccite/citeinfo/title',
    'pycsw:Relation': 'idinfo/citation/citeinfo/onlink',
}

def write_record(recobj, esn, context, url=None):
    ''' Return csw:SearchResults child as lxml.etree.Element '''
    typename = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Typename'])
    if esn == 'full' and typename == 'fgdc:metadata':
        # dump record as is and exit
        return etree.fromstring(util.getqattr(recobj, context.md_core_model['mappings']['pycsw:XML']), context.parser)

    node = etree.Element('metadata')
    node.attrib[util.nspath_eval('xsi:noNamespaceSchemaLocation', context.namespaces)] = \
    'http://www.fgdc.gov/metadata/fgdc-std-001-1998.xsd'

    idinfo = etree.SubElement(node, 'idinfo')
    # identifier
    etree.SubElement(idinfo, 'datasetid').text = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Identifier'])

    citation = etree.SubElement(idinfo, 'citation')
    citeinfo = etree.SubElement(citation, 'citeinfo')

    # title
    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Title'])
    etree.SubElement(citeinfo, 'title').text = val

    # publisher
    publinfo = etree.SubElement(citeinfo, 'publinfo')
    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Publisher']) or ''
    etree.SubElement(publinfo, 'publish').text = val

    # origin
    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Creator']) or ''
    etree.SubElement(citeinfo, 'origin').text = val

    # keywords
    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Keywords'])
    if val:
        keywords = etree.SubElement(idinfo, 'keywords')
        theme = etree.SubElement(keywords, 'theme')
        for v in val.split(','):
            etree.SubElement(theme, 'themekey').text = v

    # accessconstraints
    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:AccessConstraints']) or ''
    etree.SubElement(idinfo, 'accconst').text = val

    # abstract
    descript = etree.SubElement(idinfo, 'descript')
    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Abstract']) or ''
    etree.SubElement(descript, 'abstract').text = val

    # time
    datebegin = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:TempExtent_begin'])
    dateend = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:TempExtent_end'])
    if all([datebegin, dateend]):
        timeperd = etree.SubElement(idinfo, 'timeperd')
        timeinfo = etree.SubElement(timeperd, 'timeinfo')
        rngdates = etree.SubElement(timeinfo, 'timeinfo')
        begdate = etree.SubElement(rngdates, 'begdate').text = datebegin
        enddate = etree.SubElement(rngdates, 'enddate').text = dateend

    # bbox extent
    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:BoundingBox'])
    bboxel = write_extent(val)
    if bboxel is not None:
        idinfo.append(bboxel)

    # contributor
    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Contributor']) or ''
    etree.SubElement(idinfo, 'datacred').text = val

    # direct
    spdoinfo = etree.SubElement(idinfo, 'spdoinfo')
    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Type']) or ''
    etree.SubElement(spdoinfo, 'direct').text = val

    # formname
    distinfo = etree.SubElement(node, 'distinfo')
    stdorder = etree.SubElement(distinfo, 'stdorder')
    digform = etree.SubElement(stdorder, 'digform')
    digtinfo = etree.SubElement(digform, 'digtinfo')
    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Format']) or ''
    etree.SubElement(digtinfo, 'formname').text = val
    etree.SubElement(citeinfo, 'geoform').text = val

    # source
    lineage = etree.SubElement(node, 'lineage')
    srcinfo = etree.SubElement(lineage, 'srcinfo')
    srccite = etree.SubElement(srcinfo, 'srccite')
    sciteinfo = etree.SubElement(srccite, 'citeinfo')
    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Source']) or ''
    etree.SubElement(sciteinfo, 'title').text = val

    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Relation']) or ''
    etree.SubElement(citeinfo, 'onlink').text = val

    # links
    rlinks = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Links'])
    if rlinks:
        for link in rlinks.split('^'):
            linkset = link.split(',')
            etree.SubElement(citeinfo, 'onlink', type=linkset[2]).text = linkset[-1]

    # metd
    metainfo = etree.SubElement(node, 'metainfo')
    val = util.getqattr(recobj, context.md_core_model['mappings']['pycsw:Modified']) or ''
    etree.SubElement(metainfo, 'metd').text = val

    return node

def write_extent(bbox):
    ''' Generate BBOX extent '''

    if bbox is not None:
        try:
            bbox2 = util.wkt2geom(bbox)
        except:
            return None

        spdom = etree.Element('spdom')
        bounding = etree.SubElement(spdom, 'bounding')
        etree.SubElement(bounding, 'westbc').text = str(bbox2[0])
        etree.SubElement(bounding, 'eastbc').text = str(bbox2[2])
        etree.SubElement(bounding, 'northbc').text = str(bbox2[3])
        etree.SubElement(bounding, 'southbc').text = str(bbox2[1])
        return spdom
    return None
