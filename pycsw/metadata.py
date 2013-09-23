# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
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

import logging
import uuid
from urlparse import urlparse
from lxml import etree
from owslib.util import build_get_url
from pycsw import util

LOGGER = logging.getLogger(__name__)

def parse_record(context, record, repos=None,
    mtype='http://www.opengis.net/cat/csw/2.0.2',
    identifier=None, pagesize=10):
    ''' parse metadata '''

    if identifier is None:
        identifier = uuid.uuid4().get_urn()

    # parse web services
    if (mtype == 'http://www.opengis.net/cat/csw/2.0.2' and
        isinstance(record, str) and record.startswith('http')):
        LOGGER.debug('CSW service detected, fetching via HTTP')
        # CSW service, not csw:Record
        try:
            return _parse_csw(context, repos, record, identifier, pagesize)
        except Exception, err:
            # TODO: implement better exception handling
            if str(err).find('ExceptionReport') != -1:
                msg = 'CSW harvesting error: %s' % str(err)
                LOGGER.debug(msg)
                raise RuntimeError(msg)
            LOGGER.debug('Not a CSW, attempting to fetch Dublin Core')
            try:
                content = util.http_request('GET', record)
            except Exception, err:
                raise RuntimeError('HTTP error: %s' % str(err))
            return [_parse_dc(context, repos, etree.fromstring(content))]

    elif mtype == 'urn:geoss:waf':  # WAF
        LOGGER.debug('WAF detected, fetching via HTTP')
        return _parse_waf(context, repos, record, identifier)

    elif mtype == 'http://www.opengis.net/wms':  # WMS
        LOGGER.debug('WMS detected, fetching via OWSLib')
        return _parse_wms(context, repos, record, identifier)
     
    elif mtype == 'http://www.opengis.net/wps/1.0.0':  # WPS
        LOGGER.debug('WPS detected, fetching via OWSLib')
        return [_parse_wps(context, repos, record, identifier)]

    elif mtype == 'http://www.opengis.net/wfs':  # WFS
        LOGGER.debug('WFS detected, fetching via OWSLib')
        return _parse_wfs(context, repos, record, identifier)

    elif mtype == 'http://www.opengis.net/wcs':  # WCS
        LOGGER.debug('WCS detected, fetching via OWSLib')
        return _parse_wcs(context, repos, record, identifier)

    elif mtype == 'http://www.opengis.net/sos/1.0':  # SOS 1.0.0
        LOGGER.debug('SOS 1.0.0 detected, fetching via OWSLib')
        return _parse_sos(context, repos, record, identifier, '1.0.0')

    elif mtype == 'http://www.opengis.net/sos/2.0':  # SOS 2.0.0
        LOGGER.debug('SOS 2.0.0 detected, fetching via OWSLib')
        return _parse_sos(context, repos, record, identifier, '2.0.0')

    elif (mtype == 'http://www.opengis.net/cat/csw/csdgm' and
          record.startswith('http')):  # FGDC
        LOGGER.debug('FGDC detected, fetching via HTTP')
        record = util.http_request('GET', record)

    return _parse_metadata(context, repos, record)

def _set(context, obj, name, value):
    ''' convenience method to set values '''
    setattr(obj, context.md_core_model['mappings'][name], value)

def _parse_metadata(context, repos, record):
    """parse metadata formats"""

    if isinstance(record, str):
        exml = etree.fromstring(record)
    else:  # already serialized to lxml
        if hasattr(record, 'getroot'):  # standalone document
            exml = record.getroot()
        else:  # part of a larger document
            exml = record

    root = exml.tag

    LOGGER.debug('Serialized metadata, parsing content model')

    if root == '{%s}MD_Metadata' % context.namespaces['gmd']:  # ISO
        return [_parse_iso(context, repos, exml)]
    elif root == '{http://www.isotc211.org/2005/gmi}MI_Metadata':
        # ISO Metadata for Imagery
        return [_parse_iso(context, repos, exml)]
    elif root == 'metadata':  # FGDC
        return [_parse_fgdc(context, repos, exml)]
    elif root == '{%s}Record' % context.namespaces['csw']:  # Dublin Core CSW
        return [_parse_dc(context, repos, exml)]
    elif root == '{%s}RDF' % context.namespaces['rdf']:  # Dublin Core RDF
        return [_parse_dc(context, repos, exml)]
    elif root == '{%s}DIF' % context.namespaces['dif']:  # DIF
        pass  # TODO
    else:
        raise RuntimeError('Unsupported metadata format')


def _parse_csw(context, repos, record, identifier, pagesize=10):

    from owslib.csw import CatalogueServiceWeb

    recobjs = []  # records
    serviceobj = repos.dataset()

    # if init raises error, this might not be a CSW
    md = CatalogueServiceWeb(record)

    # generate record of service instance
    _set(context, serviceobj, 'pycsw:Identifier', identifier)
    _set(context, serviceobj, 'pycsw:Typename', 'csw:Record')
    _set(context, serviceobj, 'pycsw:Schema', 'http://www.opengis.net/cat/csw/2.0.2')
    _set(context, serviceobj, 'pycsw:MdSource', record)
    _set(context, serviceobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, serviceobj, 'pycsw:XML', md.response)
    _set(context, serviceobj, 'pycsw:AnyText', util.get_anytext(md._exml))
    _set(context, serviceobj, 'pycsw:Type', 'service')
    _set(context, serviceobj, 'pycsw:Title', md.identification.title)
    _set(context, serviceobj, 'pycsw:Abstract', md.identification.abstract)
    _set(context, serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
    _set(context, serviceobj, 'pycsw:Creator', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:Publisher', md.provider.name)
    _set(context, serviceobj, 'pycsw:Contributor', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:AccessConstraints', md.identification.accessconstraints)
    _set(context, serviceobj, 'pycsw:OtherConstraints', md.identification.fees)
    _set(context, serviceobj, 'pycsw:Source', record)
    _set(context, serviceobj, 'pycsw:Format', md.identification.type)

    _set(context, serviceobj, 'pycsw:ServiceType', md.identification.type)
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:CouplingType', 'tight')

    links = [
        '%s,OGC-CSW Catalogue Service for the Web,OGC:CSW,%s' % (identifier, md.url),
        '%s,OGC-CSW Capabilities service (ver 2.0.2),OGC:CSW-2.0.2-http-get-capabilities,%s' % (identifier, md.url),
    ]

    _set(context, serviceobj, 'pycsw:Links', '^'.join(links))

    recobjs.append(serviceobj)

    # get all supported typenames of metadata
    # so we can harvest the entire CSW

    csw_typenames = 'csw:Record'

    # now get all records
    # get total number of records to loop against

    try:
        md.getrecords(typenames=csw_typenames, resulttype='hits')
        matches = md.results['matches']
    except:  # this is a CSW, but server rejects query
        raise RuntimeError(md.response)

    if pagesize > matches:
        pagesize = matches

    LOGGER.debug('Harvesting %d CSW records' % matches)

    # loop over all catalogue records incrementally
    for r in range(1, matches, pagesize):
        try:
            md.getrecords(typenames=csw_typenames, startposition=r,
                          maxrecords=pagesize)
        except Exception, err:  # this is a CSW, but server rejects query
            raise RuntimeError(md.response)
        for k, v in md.records.iteritems():
            recobjs.append(_parse_dc(context, repos, etree.fromstring(v.xml)))

    return recobjs

def _parse_waf(context, repos, record, identifier):

    recobjs = []

    content = util.http_request('GET', record)

    LOGGER.debug(content)

    try:
        parser = etree.HTMLParser()
        tree = etree.fromstring(content, parser=parser)
    except Exception, err:
        raise Exception('Could not parse WAF: %s' % str(err))
        
    up = urlparse(record)
    links = []

    LOGGER.debug('collecting links')
    for link in tree.xpath('//a/@href'):
        link = link.strip()
        if not link:
            continue
        if link.find('?') != -1:
            continue
        if not link.endswith('.xml'):
            LOGGER.debug('Skipping, not .xml')
            continue
        if '/' in link:  # path is embedded in link
            if link[-1] == '/':  # directory, skip
                continue
            if link[0] == '/':
                # strip path of WAF URL
                link = '%s://%s%s' % (up.scheme, up.netloc, link)
        else:  # tack on href to WAF URL
            link = '%s/%s' % (record, link)
        LOGGER.debug('URL is: %s', link)
        links.append(link)

    LOGGER.debug('%d links found', len(links))
    for link in links:
        LOGGER.debug('Processing link %s', link)
        # fetch and parse
        linkcontent = util.http_request('GET', link)
        recobj = _parse_metadata(context, repos, linkcontent)[0]
        recobj.source = link
        recobj.mdsource = link
        recobjs.append(recobj)

    return recobjs

def _parse_wms(context, repos, record, identifier):

    from owslib.wms import WebMapService

    recobjs = []
    serviceobj = repos.dataset()

    md = WebMapService(record)

    # generate record of service instance
    _set(context, serviceobj, 'pycsw:Identifier', identifier)
    _set(context, serviceobj, 'pycsw:Typename', 'csw:Record')
    _set(context, serviceobj, 'pycsw:Schema', 'http://www.opengis.net/wms')
    _set(context, serviceobj, 'pycsw:MdSource', record)
    _set(context, serviceobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, serviceobj, 'pycsw:XML', md.getServiceXML())
    _set(context, serviceobj, 'pycsw:AnyText', util.get_anytext(md.getServiceXML()))
    _set(context, serviceobj, 'pycsw:Type', 'service')
    _set(context, serviceobj, 'pycsw:Title', md.identification.title)
    _set(context, serviceobj, 'pycsw:Abstract', md.identification.abstract)
    _set(context, serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
    _set(context, serviceobj, 'pycsw:Creator', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:Publisher', md.provider.name)
    _set(context, serviceobj, 'pycsw:Contributor', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:AccessConstraints', md.identification.accessconstraints)
    _set(context, serviceobj, 'pycsw:OtherConstraints', md.identification.fees)
    _set(context, serviceobj, 'pycsw:Source', record)
    _set(context, serviceobj, 'pycsw:Format', md.identification.type)
    for c in md.contents:
        if md.contents[c].parent is None:
            bbox = md.contents[c].boundingBoxWGS84
            tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
            _set(context, serviceobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
            break
    _set(context, serviceobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
    _set(context, serviceobj, 'pycsw:DistanceUOM', 'degrees')
    _set(context, serviceobj, 'pycsw:ServiceType', md.identification.type)
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:OperatesOn', ','.join(list(md.contents)))
    _set(context, serviceobj, 'pycsw:CouplingType', 'tight')

    links = [
        '%s,OGC-WMS Web Map Service,OGC:WMS,%s' % (identifier, md.url),
        '%s,OGC-WMS Capabilities service (ver 1.1.1),OGC:WMS-1.1.1-http-get-capabilities,%s' % (identifier, build_get_url(md.url, {'service': 'WMS', 'version': '1.1.1', 'request': 'GetCapabilities'})),
    ]

    _set(context, serviceobj, 'pycsw:Links', '^'.join(links))

    recobjs.append(serviceobj) 
         
    # generate record foreach layer

    LOGGER.debug('Harvesting %d WMS layers' % len(md.contents))

    for layer in md.contents:
        recobj = repos.dataset()
        identifier2 = '%s-%s' % (identifier, md.contents[layer].name)
        _set(context, recobj, 'pycsw:Identifier', identifier2)
        _set(context, recobj, 'pycsw:Typename', 'csw:Record')
        _set(context, recobj, 'pycsw:Schema', 'http://www.opengis.net/wms')
        _set(context, recobj, 'pycsw:MdSource', record)
        _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(context, recobj, 'pycsw:XML', md.getServiceXML())
        _set(context, recobj, 'pycsw:Type', 'dataset')
        _set(context, recobj, 'pycsw:ParentIdentifier', identifier)
        _set(context, recobj, 'pycsw:Title', md.contents[layer].title)
        _set(context, recobj, 'pycsw:Abstract', md.contents[layer].abstract)
        _set(context, recobj, 'pycsw:Keywords', ','.join(md.contents[layer].keywords))

        _set(context, recobj, 'pycsw:AnyText',
             util.get_anytext([md.contents[layer].title,
                              md.contents[layer].abstract,
                              ','.join(md.contents[layer].keywords)]))

        bbox = md.contents[layer].boundingBoxWGS84
        if bbox is not None:
            tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
            _set(context, recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
            _set(context, recobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
            _set(context, recobj, 'pycsw:DistanceUOM', 'degrees')
        else:
            bbox = md.contents[layer].boundingBox
            if bbox:
                tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
                _set(context, recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
                _set(context, recobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:%s' % \
                bbox[-1].split(':')[1])

        params = {
            'service': 'WMS',
            'version': '1.1.1',
            'request': 'GetMap',
            'layers': md.contents[layer].name,
            'format': 'image/png',
            'height': '200',
            'width': '200',
            'srs': 'EPSG:4326',
            'bbox':  '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3]),
            'styles': ''
        }

        links = [
            '%s,Web image thumbnail (URL),WWW:LINK-1.0-http--image-thumbnail,%s' % (md.contents[layer].name, build_get_url(md.url, params))
        ]

        params['width'] = '500'
        params['height'] = '300'

        links.append('%s,OGC Web Map Service (ver 1.1.1),OGC:WMS-1.1.1-http-get-map,%s' % (md.contents[layer].name, build_get_url(md.url, params)))

        _set(context, recobj, 'pycsw:Links', '^'.join(links))

        recobjs.append(recobj)

    return recobjs

def _parse_wfs(context, repos, record, identifier):

    from owslib.wfs import WebFeatureService

    bboxs = []
    recobjs = []
    serviceobj = repos.dataset()

    md = WebFeatureService(record, '1.1.0')

    # generate record of service instance
    _set(context, serviceobj, 'pycsw:Identifier', identifier)
    _set(context, serviceobj, 'pycsw:Typename', 'csw:Record')
    _set(context, serviceobj, 'pycsw:Schema', 'http://www.opengis.net/wfs')
    _set(context, serviceobj, 'pycsw:MdSource', record)
    _set(context, serviceobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, serviceobj, 'pycsw:XML', etree.tostring(md._capabilities))
    _set(context, serviceobj, 'pycsw:AnyText', util.get_anytext(etree.tostring(md._capabilities)))
    _set(context, serviceobj, 'pycsw:Type', 'service')
    _set(context, serviceobj, 'pycsw:Title', md.identification.title)
    _set(context, serviceobj, 'pycsw:Abstract', md.identification.abstract)
    _set(context, serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
    _set(context, serviceobj, 'pycsw:Creator', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:Publisher', md.provider.name)
    _set(context, serviceobj, 'pycsw:Contributor', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:AccessConstraints', md.identification.accessconstraints)
    _set(context, serviceobj, 'pycsw:OtherConstraints', md.identification.fees)
    _set(context, serviceobj, 'pycsw:Source', record)
    _set(context, serviceobj, 'pycsw:Format', md.identification.type)
    _set(context, serviceobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
    _set(context, serviceobj, 'pycsw:DistanceUOM', 'degrees')
    _set(context, serviceobj, 'pycsw:ServiceType', md.identification.type)
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:OperatesOn', ','.join(list(md.contents)))
    _set(context, serviceobj, 'pycsw:CouplingType', 'tight')

    links = [
        '%s,OGC-WFS Web Feature Service,OGC:WFS,%s' % (identifier, md.url),
        '%s,OGC-WFS Capabilities service (ver 1.1.0),OGC:WFS-1.1.0-http-get-capabilities,%s' % (identifier, build_get_url(md.url, {'service': 'WFS', 'version': '1.1.0', 'request': 'GetCapabilities'})),
    ]

    _set(context, serviceobj, 'pycsw:Links', '^'.join(links))

    # generate record foreach featuretype

    LOGGER.debug('Harvesting %d WFS featuretypes' % len(md.contents))

    for featuretype in md.contents:
        recobj = repos.dataset()
        identifier2 = '%s-%s' % (identifier, md.contents[featuretype].id)
        _set(context, recobj, 'pycsw:Identifier', identifier2)
        _set(context, recobj, 'pycsw:Typename', 'csw:Record')
        _set(context, recobj, 'pycsw:Schema', 'http://www.opengis.net/wfs')
        _set(context, recobj, 'pycsw:MdSource', record)
        _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(context, recobj, 'pycsw:XML', etree.tostring(md._capabilities))
        _set(context, recobj, 'pycsw:Type', 'dataset')
        _set(context, recobj, 'pycsw:ParentIdentifier', identifier)
        _set(context, recobj, 'pycsw:Title', md.contents[featuretype].title)
        _set(context, recobj, 'pycsw:Abstract', md.contents[featuretype].abstract)
        _set(context, recobj, 'pycsw:Keywords', ','.join(md.contents[featuretype].keywords))

        _set(context, recobj, 'pycsw:AnyText',
             util.get_anytext([md.contents[featuretype].title,
                              md.contents[featuretype].abstract,
                              ','.join(md.contents[featuretype].keywords)]))

        bbox = md.contents[featuretype].boundingBoxWGS84
        if bbox is not None:
            tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
            wkt_polygon = util.bbox2wktpolygon(tmp)
            _set(context, recobj, 'pycsw:BoundingBox', wkt_polygon)
            _set(context, recobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
            _set(context, recobj, 'pycsw:DistanceUOM', 'degrees')
            bboxs.append(wkt_polygon)

        params = {
            'service': 'WFS',
            'version': '1.1.0',
            'request': 'GetFeature',
            'typename': md.contents[featuretype].id,
        }

        links = [
            '%s,File for download,WWW:DOWNLOAD-1.0-http--download,%s' % (md.contents[featuretype].id, build_get_url(md.url, params))
        ]

        _set(context, recobj, 'pycsw:Links', '^'.join(links))

        recobjs.append(recobj)

    # Derive a bbox based on aggregated featuretype bbox values

    bbox_agg = util.bbox_from_polygons(bboxs)

    if bbox_agg is not None:
        _set(context, serviceobj, 'pycsw:BoundingBox', bbox_agg)

    recobjs.insert(0, serviceobj)

    return recobjs

def _parse_wcs(context, repos, record, identifier):

    from owslib.wcs import WebCoverageService

    bboxs = []
    recobjs = []
    serviceobj = repos.dataset()

    md = WebCoverageService(record, '1.0.0')

    # generate record of service instance
    _set(context, serviceobj, 'pycsw:Identifier', identifier)
    _set(context, serviceobj, 'pycsw:Typename', 'csw:Record')
    _set(context, serviceobj, 'pycsw:Schema', 'http://www.opengis.net/wcs')
    _set(context, serviceobj, 'pycsw:MdSource', record)
    _set(context, serviceobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, serviceobj, 'pycsw:XML', etree.tostring(md._capabilities))
    _set(context, serviceobj, 'pycsw:AnyText', util.get_anytext(etree.tostring(md._capabilities)))
    _set(context, serviceobj, 'pycsw:Type', 'service')
    _set(context, serviceobj, 'pycsw:Title', md.identification.title)
    _set(context, serviceobj, 'pycsw:Abstract', md.identification.abstract)
    _set(context, serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
    _set(context, serviceobj, 'pycsw:Creator', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:Publisher', md.provider.name)
    _set(context, serviceobj, 'pycsw:Contributor', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:AccessConstraints', md.identification.accessConstraints)
    _set(context, serviceobj, 'pycsw:OtherConstraints', md.identification.fees)
    _set(context, serviceobj, 'pycsw:Source', record)
    _set(context, serviceobj, 'pycsw:Format', md.identification.type)
    _set(context, serviceobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
    _set(context, serviceobj, 'pycsw:DistanceUOM', 'degrees')
    _set(context, serviceobj, 'pycsw:ServiceType', md.identification.type)
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:OperatesOn', ','.join(list(md.contents)))
    _set(context, serviceobj, 'pycsw:CouplingType', 'tight')

    links = [
        '%s,OGC-WCS Web Coverage Service,OGC:WCS,%s' % (identifier, md.url),
        '%s,OGC-WCS Capabilities service (ver 1.0.0),OGC:WCS-1.1.0-http-get-capabilities,%s' % (identifier, build_get_url(md.url, {'service': 'WCS', 'version': '1.0.0', 'request': 'GetCapabilities'})),
    ]

    _set(context, serviceobj, 'pycsw:Links', '^'.join(links))

    # generate record foreach coverage

    LOGGER.debug('Harvesting %d WCS coverages ' % len(md.contents))

    for coverage in md.contents:
        recobj = repos.dataset()
        identifier2 = '%s-%s' % (identifier, md.contents[coverage].id)
        _set(context, recobj, 'pycsw:Identifier', identifier2)
        _set(context, recobj, 'pycsw:Typename', 'csw:Record')
        _set(context, recobj, 'pycsw:Schema', 'http://www.opengis.net/wcs')
        _set(context, recobj, 'pycsw:MdSource', record)
        _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(context, recobj, 'pycsw:XML', etree.tostring(md._capabilities))
        _set(context, recobj, 'pycsw:Type', 'dataset')
        _set(context, recobj, 'pycsw:ParentIdentifier', identifier)
        _set(context, recobj, 'pycsw:Title', md.contents[coverage].title)
        _set(context, recobj, 'pycsw:Abstract', md.contents[coverage].abstract)
        _set(context, recobj, 'pycsw:Keywords', ','.join(md.contents[coverage].keywords))

        _set(context, recobj, 'pycsw:AnyText',
             util.get_anytext([md.contents[coverage].title,
                              md.contents[coverage].abstract,
                              ','.join(md.contents[coverage].keywords)]))

        bbox = md.contents[coverage].boundingBoxWGS84
        if bbox is not None:
            tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
            wkt_polygon = util.bbox2wktpolygon(tmp)
            _set(context, recobj, 'pycsw:BoundingBox', wkt_polygon)
            _set(context, recobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
            _set(context, recobj, 'pycsw:DistanceUOM', 'degrees')
            bboxs.append(wkt_polygon)

        recobjs.append(recobj)

    # Derive a bbox based on aggregated coverage bbox values

    bbox_agg = util.bbox_from_polygons(bboxs)

    if bbox_agg is not None:
        _set(context, serviceobj, 'pycsw:BoundingBox', bbox_agg)

    recobjs.insert(0, serviceobj)

    return recobjs

def _parse_wps(context, repos, record, identifier):

    from owslib.wps import WebProcessingService

    serviceobj = repos.dataset()

    md = WebProcessingService(record)

    # generate record of service instance
    _set(context, serviceobj, 'pycsw:Identifier', identifier)
    _set(context, serviceobj, 'pycsw:Typename', 'csw:Record')
    _set(context, serviceobj, 'pycsw:Schema', 'http://www.opengis.net/wps/1.0.0')
    _set(context, serviceobj, 'pycsw:MdSource', record)
    _set(context, serviceobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, serviceobj, 'pycsw:XML', etree.tostring(md._capabilities))
    _set(context, serviceobj, 'pycsw:AnyText', util.get_anytext(md._capabilities))
    _set(context, serviceobj, 'pycsw:Type', 'service')
    _set(context, serviceobj, 'pycsw:Title', md.identification.title)
    _set(context, serviceobj, 'pycsw:Abstract', md.identification.abstract)
    _set(context, serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
    _set(context, serviceobj, 'pycsw:Creator', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:Publisher', md.provider.name)
    _set(context, serviceobj, 'pycsw:Contributor', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:AccessConstraints', md.identification.accessconstraints)
    _set(context, serviceobj, 'pycsw:OtherConstraints', md.identification.fees)
    _set(context, serviceobj, 'pycsw:Source', record)
    _set(context, serviceobj, 'pycsw:Format', md.identification.type)

    _set(context, serviceobj, 'pycsw:ServiceType', md.identification.type)
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:OperatesOn', ','.join([o.identifier for o in md.processes]))
    _set(context, serviceobj, 'pycsw:CouplingType', 'loose')

    links = [
        '%s,OGC-WPS Web Processing Service,OGC:WPS,%s' % (identifier, md.url),
        '%s,OGC-WPS Capabilities service (ver 1.0.0),OGC:WPS-1.1.0-http-get-capabilities,%s' % (identifier, build_get_url(md.url, {'service': 'WPS', 'version': '1.0.0', 'request': 'GetCapabilities'})),
    ]

    _set(context, serviceobj, 'pycsw:Links', '^'.join(links))

    return serviceobj


def _parse_sos(context, repos, record, identifier, version):

    from owslib.sos import SensorObservationService

    bboxs = []
    recobjs = []
    serviceobj = repos.dataset()

    if version == '1.0.0':
        schema = 'http://www.opengis.net/sos/1.0'
    else:
        schema = 'http://www.opengis.net/sos/2.0'

    md = SensorObservationService(record, version=version)

    # generate record of service instance
    _set(context, serviceobj, 'pycsw:Identifier', identifier)
    _set(context, serviceobj, 'pycsw:Typename', 'csw:Record')
    _set(context, serviceobj, 'pycsw:Schema', schema)
    _set(context, serviceobj, 'pycsw:MdSource', record)
    _set(context, serviceobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, serviceobj, 'pycsw:XML', etree.tostring(md._capabilities))
    _set(context, serviceobj, 'pycsw:AnyText', util.get_anytext(etree.tostring(md._capabilities)))
    _set(context, serviceobj, 'pycsw:Type', 'service')
    _set(context, serviceobj, 'pycsw:Title', md.identification.title)
    _set(context, serviceobj, 'pycsw:Abstract', md.identification.abstract)
    _set(context, serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
    _set(context, serviceobj, 'pycsw:Creator', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:Publisher', md.provider.name)
    _set(context, serviceobj, 'pycsw:Contributor', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:AccessConstraints', md.identification.accessconstraints)
    _set(context, serviceobj, 'pycsw:OtherConstraints', md.identification.fees)
    _set(context, serviceobj, 'pycsw:Source', record)
    _set(context, serviceobj, 'pycsw:Format', md.identification.type)
    _set(context, serviceobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
    _set(context, serviceobj, 'pycsw:DistanceUOM', 'degrees')
    _set(context, serviceobj, 'pycsw:ServiceType', md.identification.type)
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:OperatesOn', ','.join(list(md.contents)))
    _set(context, serviceobj, 'pycsw:CouplingType', 'tight')

    links = [
        '%s,OGC-SOS Sensor Observation Service,OGC:SOS,%s' % (identifier, md.url),
        '%s,OGC-SOS Capabilities service (ver %s),OGC:SOS-%s-http-get-capabilities,%s' % (identifier, version, version, build_get_url(md.url, {'service': 'SOS', 'version': version, 'request': 'GetCapabilities'})),
    ]

    _set(context, serviceobj, 'pycsw:Links', '^'.join(links))

    # generate record foreach offering

    LOGGER.debug('Harvesting %d SOS ObservationOffering\'s ', len(md.contents))

    for offering in md.contents:
        recobj = repos.dataset()
        identifier2 = '%s-%s' % (identifier, md.contents[offering].id)
        _set(context, recobj, 'pycsw:Identifier', identifier2)
        _set(context, recobj, 'pycsw:Typename', 'csw:Record')
        _set(context, recobj, 'pycsw:Schema', schema)
        _set(context, recobj, 'pycsw:MdSource', record)
        _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(context, recobj, 'pycsw:XML', etree.tostring(md._capabilities))
        _set(context, recobj, 'pycsw:Type', 'dataset')
        _set(context, recobj, 'pycsw:ParentIdentifier', identifier)
        _set(context, recobj, 'pycsw:Title', md.contents[offering].description)
        _set(context, recobj, 'pycsw:Abstract', md.contents[offering].description)
        _set(context, recobj, 'pycsw:TempExtent_begin', util.datetime2iso8601(md.contents[offering].begin_position))
        _set(context, recobj, 'pycsw:TempExtent_end', util.datetime2iso8601(md.contents[offering].end_position))

        _set(context, recobj, 'pycsw:AnyText',
             util.get_anytext([md.contents[offering].description]))

        bbox = md.contents[offering].bbox
        if bbox is not None:
            tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
            wkt_polygon = util.bbox2wktpolygon(tmp)
            _set(context, recobj, 'pycsw:BoundingBox', wkt_polygon)
            _set(context, recobj, 'pycsw:CRS', md.contents[offering].bbox_srs.id)
            _set(context, recobj, 'pycsw:DistanceUOM', 'degrees')
            bboxs.append(wkt_polygon)

        recobjs.append(recobj)

    # Derive a bbox based on aggregated featuretype bbox values

    bbox_agg = util.bbox_from_polygons(bboxs)

    if bbox_agg is not None:
        _set(context, serviceobj, 'pycsw:BoundingBox', bbox_agg)

    recobjs.insert(0, serviceobj)

    return recobjs


def _parse_fgdc(context, repos, exml):

    from owslib.fgdc import Metadata

    recobj = repos.dataset()
    links = []

    md = Metadata(exml)

    if md.idinfo.datasetid is not None:  # we need an identifier
        _set(context, recobj, 'pycsw:Identifier', md.idinfo.datasetid)
    else:  # generate one ourselves
        _set(context, recobj, 'pycsw:Identifier', uuid.uuid1().get_urn())

    _set(context, recobj, 'pycsw:Typename', 'fgdc:metadata')
    _set(context, recobj, 'pycsw:Schema', context.namespaces['fgdc'])
    _set(context, recobj, 'pycsw:MdSource', 'local')
    _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, recobj, 'pycsw:XML', md.xml)
    _set(context, recobj, 'pycsw:AnyText', util.get_anytext(exml))
    _set(context, recobj, 'pycsw:Language', 'en-US')

    if hasattr(md.idinfo, 'descript'):
        _set(context, recobj, 'pycsw:Abstract', md.idinfo.descript.abstract)

    if hasattr(md.idinfo, 'keywords'):
        if md.idinfo.keywords.theme:
            _set(context, recobj, 'pycsw:Keywords', \
            ','.join(md.idinfo.keywords.theme[0]['themekey']))

    if hasattr(md.idinfo.timeperd, 'timeinfo'):
        if hasattr(md.idinfo.timeperd.timeinfo, 'rngdates'):
            _set(context, recobj, 'pycsw:TempExtent_begin',
                 md.idinfo.timeperd.timeinfo.rngdates.begdate)
            _set(context, recobj, 'pycsw:TempExtent_end',
                 md.idinfo.timeperd.timeinfo.rngdates.enddate)

    if hasattr(md.idinfo, 'origin'):
        _set(context, recobj, 'pycsw:Creator', md.idinfo.origin)
        _set(context, recobj, 'pycsw:Publisher',  md.idinfo.origin)
        _set(context, recobj, 'pycsw:Contributor', md.idinfo.origin)

    if hasattr(md.idinfo, 'ptcontac'):
        _set(context, recobj, 'pycsw:OrganizationName', md.idinfo.ptcontac.cntorg)
    _set(context, recobj, 'pycsw:AccessConstraints', md.idinfo.accconst)
    _set(context, recobj, 'pycsw:OtherConstraints', md.idinfo.useconst)
    _set(context, recobj, 'pycsw:Date', md.metainfo.metd)

    if hasattr(md.idinfo, 'spdom') and hasattr(md.idinfo.spdom, 'bbox'):
        bbox = md.idinfo.spdom.bbox
    else:
        bbox = None

    if hasattr(md.idinfo, 'citation'):
        if hasattr(md.idinfo.citation, 'citeinfo'):
            _set(context, recobj, 'pycsw:Type',  md.idinfo.citation.citeinfo['geoform'])
            _set(context, recobj, 'pycsw:Title', md.idinfo.citation.citeinfo['title'])
            _set(context, recobj,
            'pycsw:PublicationDate', md.idinfo.citation.citeinfo['pubdate'])
            _set(context, recobj, 'pycsw:Format', md.idinfo.citation.citeinfo['geoform'])
            if md.idinfo.citation.citeinfo['onlink']:
                for link in md.idinfo.citation.citeinfo['onlink']:
                    tmp = ',,,%s' % link
                    links.append(tmp)

    if hasattr(md, 'distinfo') and hasattr(md.distinfo, 'stdorder'):
        for link in md.distinfo.stdorder['digform']:
            tmp = ',%s,,%s' % (link['name'], link['url'])
            links.append(tmp)

    if len(links) > 0:
        _set(context, recobj, 'pycsw:Links', '^'.join(links))

    if bbox is not None:
        try:
            tmp = '%s,%s,%s,%s' % (bbox.minx, bbox.miny, bbox.maxx, bbox.maxy)
            _set(context, recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
        except:  # coordinates are corrupted, do not include
            _set(context, recobj, 'pycsw:BoundingBox', None)
    else:
        _set(context, recobj, 'pycsw:BoundingBox', None)

    return recobj

def _parse_iso(context, repos, exml):

    from owslib.iso import MD_Metadata

    recobj = repos.dataset()
    links = []

    md = MD_Metadata(exml)

    _set(context, recobj, 'pycsw:Identifier', md.identifier)
    _set(context, recobj, 'pycsw:Typename', 'gmd:MD_Metadata')
    _set(context, recobj, 'pycsw:Schema', context.namespaces['gmd'])
    _set(context, recobj, 'pycsw:MdSource', 'local')
    _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, recobj, 'pycsw:XML', md.xml)
    _set(context, recobj, 'pycsw:AnyText', util.get_anytext(exml))
    _set(context, recobj, 'pycsw:Language', md.language)
    _set(context, recobj, 'pycsw:Type', md.hierarchy)
    _set(context, recobj, 'pycsw:ParentIdentifier', md.parentidentifier)
    _set(context, recobj, 'pycsw:Date', md.datestamp)
    _set(context, recobj, 'pycsw:Source', md.dataseturi)
    if md.referencesystem is not None:
        _set(context, recobj, 'pycsw:CRS','urn:ogc:def:crs:EPSG:6.11:%s' %
        md.referencesystem.code)

    if hasattr(md, 'identification'):
        _set(context, recobj, 'pycsw:Title', md.identification.title)
        _set(context, recobj, 'pycsw:AlternateTitle', md.identification.alternatetitle)
        _set(context, recobj, 'pycsw:Abstract', md.identification.abstract)
        _set(context, recobj, 'pycsw:Relation', md.identification.aggregationinfo)

        if hasattr(md.identification, 'temporalextent_start'):
            _set(context, recobj, 'pycsw:TempExtent_begin', md.identification.temporalextent_start)
        if hasattr(md.identification, 'temporalextent_end'):
            _set(context, recobj, 'pycsw:TempExtent_end', md.identification.temporalextent_end)

        if len(md.identification.topiccategory) > 0:
            _set(context, recobj, 'pycsw:TopicCategory', md.identification.topiccategory[0])

        if len(md.identification.resourcelanguage) > 0:
            _set(context, recobj, 'pycsw:ResourceLanguage', md.identification.resourcelanguage[0])
 
        if hasattr(md.identification, 'bbox'):
            bbox = md.identification.bbox
        else:
            bbox = None

        if (hasattr(md.identification, 'keywords') and
        len(md.identification.keywords) > 0):
            if None not in md.identification.keywords[0]['keywords']:
                _set(context, recobj, 'pycsw:Keywords', ','.join(
                md.identification.keywords[0]['keywords']))
                _set(context, recobj, 'pycsw:KeywordType', md.identification.keywords[0]['type'])

        if hasattr(md.identification, 'creator'):
            _set(context, recobj, 'pycsw:Creator', md.identification.creator)
        if hasattr(md.identification, 'publisher'):
            _set(context, recobj, 'pycsw:Publisher', md.identification.publisher)
        if hasattr(md.identification, 'contributor'):
            _set(context, recobj, 'pycsw:Contributor', md.identification.contributor)

        if (hasattr(md.identification, 'contact') and 
        hasattr(md.identification.contact, 'organization')):
            _set(context, recobj, 'pycsw:OrganizationName', md.identification.contact.organization)

        if len(md.identification.securityconstraints) > 0:
            _set(context, recobj, 'pycsw:SecurityConstraints', 
            md.identification.securityconstraints[0])
        if len(md.identification.accessconstraints) > 0:
            _set(context, recobj, 'pycsw:AccessConstraints', 
            md.identification.accessconstraints[0])
        if len(md.identification.otherconstraints) > 0:
            _set(context, recobj, 'pycsw:OtherConstraints', md.identification.otherconstraints[0])

        if hasattr(md.identification, 'date'):
            for datenode in md.identification.date:
                if datenode.type == 'revision':
                    _set(context, recobj, 'pycsw:RevisionDate', datenode.date)
                elif datenode.type == 'creation':
                    _set(context, recobj, 'pycsw:CreationDate', datenode.date)
                elif datenode.type == 'publication':
                    _set(context, recobj, 'pycsw:PublicationDate', datenode.date)

        if hasattr(md.identification, 'extent') and hasattr(md.identification.extent, 'description_code'):
            _set(context, recobj, 'pycsw:GeographicDescriptionCode', md.identification.extent.description_code)

        if len(md.identification.denominators) > 0:
            _set(context, recobj, 'pycsw:Denominator', md.identification.denominators[0])
        if len(md.identification.distance) > 0:
            _set(context, recobj, 'pycsw:DistanceValue', md.identification.distance[0])
        if len(md.identification.uom) > 0:
            _set(context, recobj, 'pycsw:DistanceUOM', md.identification.uom[0])

        if len(md.identification.classification) > 0:
            _set(context, recobj, 'pycsw:Classification', md.identification.classification[0])
        if len(md.identification.uselimitation) > 0:
            _set(context, recobj, 'pycsw:ConditionApplyingToAccessAndUse',
            md.identification.uselimitation[0])

    if hasattr(md.identification, 'format'):
        _set(context, recobj, 'pycsw:Format', md.distribution.format)

    if md.serviceidentification is not None:
        _set(context, recobj, 'pycsw:ServiceType', md.serviceidentification.type)
        _set(context, recobj, 'pycsw:ServiceTypeVersion', md.serviceidentification.version)

        _set(context, recobj, 'pycsw:CouplingType', md.serviceidentification.couplingtype)
   
        #if len(md.serviceidentification.operateson) > 0: 
        #    _set(context, recobj, 'pycsw:operateson = VARCHAR(32), 
        #_set(context, recobj, 'pycsw:operation VARCHAR(32), 
        #_set(context, recobj, 'pycsw:operatesonidentifier VARCHAR(32), 
        #_set(context, recobj, 'pycsw:operatesoname VARCHAR(32), 


    if hasattr(md.identification, 'dataquality'):     
        _set(context, recobj, 'pycsw:Degree', md.dataquality.conformancedegree)
        _set(context, recobj, 'pycsw:Lineage', md.dataquality.lineage)
        _set(context, recobj, 'pycsw:SpecificationTitle', md.dataquality.specificationtitle)
        if hasattr(md.dataquality, 'specificationdate'):
            _set(context, recobj, 'pycsw:specificationDate',
            md.dataquality.specificationdate[0].date)
            _set(context, recobj, 'pycsw:SpecificationDateType',
            md.dataquality.specificationdate[0].datetype)

    if hasattr(md, 'contact') and len(md.contact) > 0:
        _set(context, recobj, 'pycsw:ResponsiblePartyRole', md.contact[0].role)

    if hasattr(md, 'distribution') and hasattr(md.distribution, 'online'):
        for link in md.distribution.online:
            linkstr = '%s,%s,%s,%s' % \
            (link.name, link.description, link.protocol, link.url)
            links.append(linkstr)

    if len(links) > 0:
        _set(context, recobj, 'pycsw:Links', '^'.join(links))

    if bbox is not None:
        try:
            tmp = '%s,%s,%s,%s' % (bbox.minx, bbox.miny, bbox.maxx, bbox.maxy)
            _set(context, recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
        except:  # coordinates are corrupted, do not include
            _set(context, recobj, 'pycsw:BoundingBox', None)
    else:
        _set(context, recobj, 'pycsw:BoundingBox', None)

    return recobj

def _parse_dc(context, repos, exml):

    from owslib.csw import CswRecord

    recobj = repos.dataset()
    links = []

    md = CswRecord(exml)

    if md.bbox is None:
        bbox = None
    else:
        bbox = md.bbox

    _set(context, recobj, 'pycsw:Identifier', md.identifier)
    _set(context, recobj, 'pycsw:Typename', 'csw:Record')
    _set(context, recobj, 'pycsw:Schema', context.namespaces['csw'])
    _set(context, recobj, 'pycsw:MdSource', 'local')
    _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, recobj, 'pycsw:XML', md.xml)
    _set(context, recobj, 'pycsw:AnyText', util.get_anytext(exml))
    _set(context, recobj, 'pycsw:Language', md.language)
    _set(context, recobj, 'pycsw:Type', md.type)
    _set(context, recobj, 'pycsw:Title', md.title)
    _set(context, recobj, 'pycsw:AlternateTitle', md.alternative)
    _set(context, recobj, 'pycsw:Abstract', md.abstract)

    if len(md.subjects) > 0 and None not in md.subjects:
        _set(context, recobj, 'pycsw:Keywords', ','.join(md.subjects))

    _set(context, recobj, 'pycsw:ParentIdentifier', md.ispartof)
    _set(context, recobj, 'pycsw:Relation', md.relation)
    _set(context, recobj, 'pycsw:TempExtent_begin', md.temporal)
    _set(context, recobj, 'pycsw:TempExtent_end', md.temporal)
    _set(context, recobj, 'pycsw:ResourceLanguage', md.language)
    _set(context, recobj, 'pycsw:Creator', md.creator)
    _set(context, recobj, 'pycsw:Publisher', md.publisher)
    _set(context, recobj, 'pycsw:Contributor', md.contributor)
    _set(context, recobj, 'pycsw:OrganizationName', md.rightsholder)
    _set(context, recobj, 'pycsw:AccessConstraints', md.accessrights)
    _set(context, recobj, 'pycsw:OtherConstraints', md.license)
    _set(context, recobj, 'pycsw:Date', md.date)
    _set(context, recobj, 'pycsw:CreationDate', md.created)
    _set(context, recobj, 'pycsw:PublicationDate', md.issued)
    _set(context, recobj, 'pycsw:Modified', md.modified)
    _set(context, recobj, 'pycsw:Format', md.format)
    _set(context, recobj, 'pycsw:Source', md.source)

    for ref in md.references:
        tmp = ',,%s,%s' % (ref['scheme'], ref['url'])
        links.append(tmp)
    for uri in md.uris:
        tmp = '%s,%s,%s,%s' % \
        (uri['name'], uri['description'], uri['protocol'], uri['url'])
        links.append(tmp)

    if len(links) > 0:
        _set(context, recobj, 'pycsw:Links', '^'.join(links))

    if bbox is not None:
        try:
            tmp = '%s,%s,%s,%s' % (bbox.minx, bbox.miny, bbox.maxx, bbox.maxy)
            _set(context, recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
        except:  # coordinates are corrupted, do not include
            _set(context, recobj, 'pycsw:BoundingBox', None)
    else:
        _set(context, recobj, 'pycsw:BoundingBox', None)

    return recobj

