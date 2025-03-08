# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2025 Tom Kralidis
# Copyright (c) 2016 James F. Dickens
# Copyright (c) 2017 Ricardo Garcia Silva
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

import json
import logging
import uuid
from urllib.parse import urlparse

from geolinks import sniff_link
from owslib.util import build_get_url
from shapely.wkt import loads
from shapely.geometry import MultiPolygon

from pycsw.core.etree import etree
from pycsw.core import util
from pycsw.plugins.outputschemas import atom

LOGGER = logging.getLogger(__name__)

def parse_record(context, record, repos=None,
    mtype='http://www.opengis.net/cat/csw/2.0.2',
    identifier=None, pagesize=10):
    ''' parse metadata '''

    if identifier is None:
        identifier = uuid.uuid4().urn

    # parse web services
    if (mtype == 'http://www.opengis.net/cat/csw/2.0.2' and
        isinstance(record, str) and record.startswith('http')):
        LOGGER.info('CSW service detected, fetching via HTTP')
        # CSW service, not csw:Record
        try:
            return _parse_csw(context, repos, record, identifier, pagesize)
        except Exception as err:
            # TODO: implement better exception handling
            if str(err).find('ExceptionReport') != -1:
                msg = 'CSW harvesting error: %s' % str(err)
                LOGGER.exception(msg)
                raise RuntimeError(msg)
            LOGGER.debug('Not a CSW, attempting to fetch Dublin Core')
            try:
                content = util.http_request('GET', record)
            except Exception as err:
                raise RuntimeError('HTTP error: %s' % str(err))
            return [_parse_dc(context, repos, etree.fromstring(content, context.parser))]

    elif mtype == 'urn:geoss:waf':  # WAF
        LOGGER.info('WAF detected, fetching via HTTP')
        return _parse_waf(context, repos, record, identifier)

    elif mtype == 'http://www.opengis.net/wms':  # WMS
        LOGGER.info('WMS detected, fetching via OWSLib')
        return _parse_wms(context, repos, record, identifier)

    elif mtype == 'http://www.opengis.net/wmts/1.0':  # WMTS
        LOGGER.info('WMTS 1.0.0 detected, fetching via OWSLib')
        return _parse_wmts(context, repos, record, identifier)

    elif mtype == 'http://www.opengis.net/wps/1.0.0':  # WPS
        LOGGER.info('WPS detected, fetching via OWSLib')
        return _parse_wps(context, repos, record, identifier)

    elif mtype == 'http://www.opengis.net/wfs':  # WFS 1.1.0
        LOGGER.info('WFS detected, fetching via OWSLib')
        return _parse_wfs(context, repos, record, identifier, '1.1.0')

    elif mtype == 'http://www.opengis.net/wfs/2.0':  # WFS 2.0.0
        LOGGER.info('WFS detected, fetching via OWSLib')
        return _parse_wfs(context, repos, record, identifier, '2.0.0')

    elif mtype == 'http://www.opengis.net/wcs':  # WCS
        LOGGER.info('WCS detected, fetching via OWSLib')
        return _parse_wcs(context, repos, record, identifier)

    elif mtype == 'http://www.opengis.net/sos/1.0':  # SOS 1.0.0
        LOGGER.info('SOS 1.0.0 detected, fetching via OWSLib')
        return _parse_sos(context, repos, record, identifier, '1.0.0')

    elif mtype == 'http://www.opengis.net/sos/2.0':  # SOS 2.0.0
        LOGGER.info('SOS 2.0.0 detected, fetching via OWSLib')
        return _parse_sos(context, repos, record, identifier, '2.0.0')

    elif (mtype == 'http://www.opengis.net/cat/csw/csdgm' and
          record.startswith('http')):  # FGDC
        LOGGER.info('FGDC detected, fetching via HTTP')
        record = util.http_request('GET', record)

    return _parse_metadata(context, repos, record)

def _get(context, obj, name):
    ''' convenience method to get values '''
    return getattr(obj, context.md_core_model['mappings'][name])

def _set(context, obj, name, value):
    ''' convenience method to set values '''
    setattr(obj, context.md_core_model['mappings'][name], value)

def _parse_metadata(context, repos, record):
    """parse metadata formats"""

    if isinstance(record, dict):  # JSON
        LOGGER.debug('Record is JSON based')
        return [_parse_json_record(context, repos, record)]

    if isinstance(record, bytes) or isinstance(record, str):
        exml = etree.fromstring(record, context.parser)
    else:  # already serialized to lxml
        if hasattr(record, 'getroot'):  # standalone document
            exml = record.getroot()
        else:  # part of a larger document
            exml = record

    root = exml.tag

    LOGGER.info('Serialized metadata, parsing content model')

    if root == '{%s}MD_Metadata' % context.namespaces['gmd']:  # ISO
        return [_parse_iso(context, repos, exml)]
    elif root == '{http://www.isotc211.org/2005/gmi}MI_Metadata':
        # ISO Metadata for Imagery
        return [_parse_iso(context, repos, exml)]
    elif root == 'metadata':  # FGDC
        return [_parse_fgdc(context, repos, exml)]
    elif root == '{%s}TRANSFER' % context.namespaces['gm03']:  # GM03
        return [_parse_gm03(context, repos, exml)]
    elif root == '{http://www.geocat.ch/2008/che}CHE_MD_Metadata': # GM03 ISO profile
        return [_parse_iso(context, repos, exml)]
    elif root == '{%s}Record' % context.namespaces['csw']:  # Dublin Core CSW
        return [_parse_dc(context, repos, exml)]
    elif root == '{%s}RDF' % context.namespaces['rdf']:  # Dublin Core RDF
        return [_parse_dc(context, repos, exml)]
    elif root == '{%s}DIF' % context.namespaces['dif']:  # DIF
        pass  # TODO
    elif root == '{%s}MD_Metadata' % context.namespaces['mdb']:
        # ISO 19115p3 XML
        return [_parse_iso(context, repos, exml)]
    else:
        raise RuntimeError('Unsupported metadata format')


def _parse_csw(context, repos, record, identifier, pagesize=10):

    from owslib.csw import CatalogueServiceWeb

    recobjs = []  # records
    serviceobj = repos.dataset()

    # if init raises error, this might not be a CSW
    md = CatalogueServiceWeb(record, timeout=60)

    LOGGER.info('Setting CSW service metadata')
    # generate record of service instance
    _set(context, serviceobj, 'pycsw:Identifier', identifier)
    _set(context, serviceobj, 'pycsw:Typename', 'csw:Record')
    _set(context, serviceobj, 'pycsw:Schema', 'http://www.opengis.net/cat/csw/2.0.2')
    _set(context, serviceobj, 'pycsw:MdSource', record)
    _set(context, serviceobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(
        context,
        serviceobj,
        'pycsw:AnyText',
        util.get_anytext(md._exml)
    )
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

    _set(context, serviceobj, 'pycsw:ServiceType', 'OGC:CSW')
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:CouplingType', 'tight')

    links = [{
        'name': identifier,
        'description': 'OGC-CSW Catalogue Service for the Web',
        'protocol': 'OGC:CSW',
        'url': md.url
    }]

    _set(context, serviceobj, 'pycsw:Links', json.dumps(links))
    _set(context, serviceobj, 'pycsw:XML', caps2iso(serviceobj, md, context))
    _set(context, serviceobj, 'pycsw:MetadataType', 'application/xml')

    recobjs.append(serviceobj)

    # get all supported typenames of metadata
    # so we can harvest the entire CSW

    # try for ISO, settle for Dublin Core
    csw_typenames = 'csw:Record'
    csw_outputschema = 'http://www.opengis.net/cat/csw/2.0.2'

    grop = md.get_operation_by_name('GetRecords')
    if all(['gmd:MD_Metadata' in grop.parameters['typeNames']['values'],
            'http://www.isotc211.org/2005/gmd' in grop.parameters['outputSchema']['values']]):
        LOGGER.debug('CSW supports ISO')
        csw_typenames = 'gmd:MD_Metadata'
        csw_outputschema = 'http://www.isotc211.org/2005/gmd'


    # now get all records
    # get total number of records to loop against

    try:
        md.getrecords2(typenames=csw_typenames, resulttype='hits',
                       outputschema=csw_outputschema)
        matches = md.results['matches']
    except Exception:  # this is a CSW, but server rejects query
        LOGGER.debug('CSW query failed')
        raise RuntimeError(md.response)

    if pagesize > matches:
        pagesize = matches

    LOGGER.info('Harvesting %d CSW records', matches)

    # loop over all catalogue records incrementally
    for r in range(1, matches+1, pagesize):
        try:
            md.getrecords2(typenames=csw_typenames, startposition=r,
                           maxrecords=pagesize, outputschema=csw_outputschema, esn='full')
        except Exception as err:  # this is a CSW, but server rejects query
            raise RuntimeError(md.response)
        for k, v in md.records.items():
            # try to parse metadata
            try:
                LOGGER.info('Parsing metadata record: %s', v.xml)
                if csw_typenames == 'gmd:MD_Metadata':
                    recobjs.append(_parse_iso(context, repos,
                                              etree.fromstring(v.xml, context.parser)))
                else:
                    recobjs.append(_parse_dc(context, repos,
                                             etree.fromstring(v.xml, context.parser)))
            except Exception as err:  # parsing failed for some reason
                LOGGER.exception('Metadata parsing failed')

    return recobjs

def _parse_waf(context, repos, record, identifier):

    recobjs = []

    content = util.http_request('GET', record)

    LOGGER.debug(content)

    try:
        parser = etree.HTMLParser()
        tree = etree.fromstring(content, parser)
    except Exception as err:
        raise Exception('Could not parse WAF: %s' % str(err))

    up = urlparse(record)
    links = []

    LOGGER.info('collecting links')
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
        LOGGER.info('Processing link %s', link)
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
    try:
        md = WebMapService(record, version='1.3.0')
    except Exception as err:
        LOGGER.info('Looks like WMS 1.3.0 is not supported; trying 1.1.1', err)
        md = WebMapService(record)

    # generate record of service instance
    _set(context, serviceobj, 'pycsw:Identifier', identifier)
    _set(context, serviceobj, 'pycsw:Typename', 'csw:Record')
    _set(context, serviceobj, 'pycsw:Schema', 'http://www.opengis.net/wms')
    _set(context, serviceobj, 'pycsw:MdSource', record)
    _set(context, serviceobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(
        context,
        serviceobj,
        'pycsw:AnyText',
        util.get_anytext(md.getServiceXML())
    )
    _set(context, serviceobj, 'pycsw:Type', 'service')
    _set(context, serviceobj, 'pycsw:Title', md.identification.title)
    _set(context, serviceobj, 'pycsw:Abstract', md.identification.abstract)
    _set(context, serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
    _set(context, serviceobj, 'pycsw:Creator', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:Publisher', md.provider.name)
    _set(context, serviceobj, 'pycsw:Contributor', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)

    contacts = [vars(md.provider.contact)]
    contacts[0]['role'] = 'pointOfContact'
    _set(context, serviceobj, 'pycsw:Contacts', 
         json.dumps(contacts,default=lambda o: o.__dict__))

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
    _set(context, serviceobj, 'pycsw:ServiceType', 'OGC:WMS')
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:OperatesOn', ','.join(list(md.contents)))
    _set(context, serviceobj, 'pycsw:CouplingType', 'tight')

    links = [{
        'name': identifier,
        'description': 'OGC-WMS Web Map Service',
        'protocol': 'OGC:WMS',
        'url': md.url
    }]

    _set(context, serviceobj, 'pycsw:Links', json.dumps(links))
    _set(context, serviceobj, 'pycsw:XML', caps2iso(serviceobj, md, context))
    _set(context, serviceobj, 'pycsw:MetadataType', 'application/xml')

    recobjs.append(serviceobj)

    # generate record foreach layer

    LOGGER.info('Harvesting %d WMS layers', len(md.contents))

    for layer in md.contents:
        recobj = repos.dataset()
        identifier2 = '%s-%s' % (identifier, md.contents[layer].name)
        _set(context, recobj, 'pycsw:Identifier', identifier2)
        _set(context, recobj, 'pycsw:Typename', 'csw:Record')
        _set(context, recobj, 'pycsw:Schema', 'http://www.opengis.net/wms')
        _set(context, recobj, 'pycsw:MdSource', record)
        _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(context, recobj, 'pycsw:Type', 'dataset')
        _set(context, recobj, 'pycsw:ParentIdentifier', identifier)
        _set(context, recobj, 'pycsw:Title', md.contents[layer].title)
        _set(context, recobj, 'pycsw:Abstract', md.contents[layer].abstract)
        _set(context, recobj, 'pycsw:Keywords', ','.join(md.contents[layer].keywords))

        _set(
            context,
            recobj,
            'pycsw:AnyText',
            util.get_anytext([
                md.contents[layer].title,
                md.contents[layer].abstract,
                ','.join(md.contents[layer].keywords)
            ])
        )

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

        _set(context, recobj, 'pycsw:Contacts', 
            json.dumps(contacts,default=lambda o: o.__dict__))

        times = md.contents[layer].timepositions
        if times is not None:  # get temporal extent
            time_begin = time_end = None
            if len(times) == 1 and len(times[0].split('/')) > 1:
                time_envelope = times[0].split('/')
                time_begin = time_envelope[0]
                time_end = time_envelope[1]
            elif len(times) > 1:  # get first/last
                time_begin = times[0]
                time_end = times[-1]
            if all([time_begin is not None, time_end is not None]):
                _set(context, recobj, 'pycsw:TempExtent_begin', time_begin)
                _set(context, recobj, 'pycsw:TempExtent_end', time_end)

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

        links = [{
            'name': md.contents[layer].name,
            'description': 'OGC-Web Map Service',
            'protocol': 'OGC:WMS',
            'url': md.url
            }, {
            'name': md.contents[layer].name,
            'description': 'Web image thumbnail (URL)',
            'protocol': 'WWW:LINK-1.0-http--image-thumbnail',
            'url': build_get_url(md.url, params)
        }]

        _set(context, recobj, 'pycsw:Links', json.dumps(links))
        _set(context, recobj, 'pycsw:XML', caps2iso(recobj, md, context))
        _set(context, recobj, 'pycsw:MetadataType', 'application/xml')

        recobjs.append(recobj)

    return recobjs

def _parse_wmts(context, repos, record, identifier):

    from owslib.wmts import WebMapTileService

    recobjs = []
    serviceobj = repos.dataset()

    md = WebMapTileService(record)
    # generate record of service instance
    _set(context, serviceobj, 'pycsw:Identifier', identifier)
    _set(context, serviceobj, 'pycsw:Typename', 'csw:Record')
    _set(context, serviceobj, 'pycsw:Schema', 'http://www.opengis.net/wmts/1.0')
    _set(context, serviceobj, 'pycsw:MdSource', record)
    _set(context, serviceobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(
        context,
        serviceobj,
        'pycsw:AnyText',
        util.get_anytext(md.getServiceXML())
    )
    _set(context, serviceobj, 'pycsw:Type', 'service')
    _set(context, serviceobj, 'pycsw:Title', md.identification.title)
    _set(context, serviceobj, 'pycsw:Abstract', md.identification.abstract)
    _set(context, serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
    _set(context, serviceobj, 'pycsw:Creator', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:Publisher', md.provider.name)
    _set(context, serviceobj, 'pycsw:Contributor', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)

    contacts = [vars(md.provider.contact)]
    contacts[0]['role'] = 'pointOfContact'
    _set(context, serviceobj, 'pycsw:Contacts', 
         json.dumps(contacts,default=lambda o: o.__dict__))

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
    _set(context, serviceobj, 'pycsw:ServiceType', 'OGC:WMTS')
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:OperatesOn', ','.join(list(md.contents)))
    _set(context, serviceobj, 'pycsw:CouplingType', 'tight')

    links = [{
        'name': identifier,
        'description': 'OGC-WMTS Web Map Service',
        'protocol': 'OGC:WMTS',
        'url': md.url
    }]

    _set(context, serviceobj, 'pycsw:Links', json.dumps(links))
    _set(context, serviceobj, 'pycsw:XML', caps2iso(serviceobj, md, context))
    _set(context, serviceobj, 'pycsw:MetadataType', 'application/xml')

    recobjs.append(serviceobj)

    # generate record for each layer

    LOGGER.debug('Harvesting %d WMTS layers', len(md.contents))

    for layer in md.contents:
        recobj = repos.dataset()
        keywords = ''
        identifier2 = '%s-%s' % (identifier, md.contents[layer].name)
        _set(context, recobj, 'pycsw:Identifier', identifier2)
        _set(context, recobj, 'pycsw:Typename', 'csw:Record')
        _set(context, recobj, 'pycsw:Schema', 'http://www.opengis.net/wmts/1.0')
        _set(context, recobj, 'pycsw:MdSource', record)
        _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(context, recobj, 'pycsw:Type', 'dataset')
        _set(context, recobj, 'pycsw:ParentIdentifier', identifier)
        if md.contents[layer].title:
             _set(context, recobj, 'pycsw:Title', md.contents[layer].title)
        else:
            _set(context, recobj, 'pycsw:Title', "")
        if md.contents[layer].abstract:
            _set(context, recobj, 'pycsw:Abstract', md.contents[layer].abstract)
        else:
            _set(context, recobj, 'pycsw:Abstract', "")
        if hasattr(md.contents[layer], 'keywords'):  # safeguard against older OWSLib installs
            keywords = ','.join(md.contents[layer].keywords)
        _set(context, recobj, 'pycsw:Keywords', keywords)

        _set(
            context,
            recobj,
            'pycsw:AnyText',
             util.get_anytext([
                 md.contents[layer].title,
                 md.contents[layer].abstract,
                 ','.join(keywords)
             ])
        )

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

        _set(context, recobj, 'pycsw:Contacts', 
            json.dumps(contacts,default=lambda o: o.__dict__))

        params = {
            'service': 'WMTS',
            'version': '1.0.0',
            'request': 'GetTile',
            'layer': md.contents[layer].name,
        }

        links = [{
           'name': md.contents[layer].name,
           'description': 'OGC-Web Map Tile Service',
           'protocol': 'OGC:WMTS',
           'url': md.url
           }, {
           'name': md.contents[layer].name,
           'description': 'Web image thumbnail (URL)',
           'protocol': 'WWW:LINK-1.0-http--image-thumbnai',
           'url': build_get_url(md.url, params)
        }]

        _set(context, recobj, 'pycsw:Links', json.dumps(links))
        _set(context, recobj, 'pycsw:XML', caps2iso(recobj, md, context))
        _set(context, recobj, 'pycsw:MetadataType', 'application/xml')

        recobjs.append(recobj)

    return recobjs


def _parse_wfs(context, repos, record, identifier, version):

    import requests
    from owslib.wfs import WebFeatureService

    bboxs = []
    recobjs = []
    serviceobj = repos.dataset()

    try:
        md = WebFeatureService(record, version)
    except requests.exceptions.HTTPError as err:
        raise
    except Exception as err:
        if version == '1.1.0':
            md = WebFeatureService(record, '1.0.0')

    # generate record of service instance
    _set(context, serviceobj, 'pycsw:Identifier', identifier)
    _set(context, serviceobj, 'pycsw:Typename', 'csw:Record')
    _set(context, serviceobj, 'pycsw:Schema', 'http://www.opengis.net/wfs')
    _set(context, serviceobj, 'pycsw:MdSource', record)
    _set(context, serviceobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(
        context,
        serviceobj,
        'pycsw:AnyText',
        util.get_anytext(etree.tostring(md._capabilities))
    )
    _set(context, serviceobj, 'pycsw:Type', 'service')
    _set(context, serviceobj, 'pycsw:Title', md.identification.title)
    _set(context, serviceobj, 'pycsw:Abstract', md.identification.abstract)
    _set(context, serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
    _set(context, serviceobj, 'pycsw:Creator', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:Publisher', md.provider.name)
    _set(context, serviceobj, 'pycsw:Contributor', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)

    contacts = [vars(md.provider.contact)]
    contacts[0]['role'] = 'pointOfContact'
    _set(context, serviceobj, 'pycsw:Contacts', 
         json.dumps(contacts,default=lambda o: o.__dict__))

    _set(context, serviceobj, 'pycsw:AccessConstraints', md.identification.accessconstraints)
    _set(context, serviceobj, 'pycsw:OtherConstraints', md.identification.fees)
    _set(context, serviceobj, 'pycsw:Source', record)
    _set(context, serviceobj, 'pycsw:Format', md.identification.type)
    _set(context, serviceobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
    _set(context, serviceobj, 'pycsw:DistanceUOM', 'degrees')
    _set(context, serviceobj, 'pycsw:ServiceType', 'OGC:WFS')
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:OperatesOn', ','.join(list(md.contents)))
    _set(context, serviceobj, 'pycsw:CouplingType', 'tight')

    links = [{
        'name': identifier,
        'description': 'OGC-WFS Web Feature Service',
        'protocol': 'OGC:WFS',
        'url': md.url
    }]

    _set(context, serviceobj, 'pycsw:Links', json.dumps(links))

    # generate record foreach featuretype

    LOGGER.info('Harvesting %d WFS featuretypes', len(md.contents))

    for featuretype in md.contents:
        recobj = repos.dataset()
        identifier2 = '%s-%s' % (identifier, md.contents[featuretype].id)
        _set(context, recobj, 'pycsw:Identifier', identifier2)
        _set(context, recobj, 'pycsw:Typename', 'csw:Record')
        _set(context, recobj, 'pycsw:Schema', 'http://www.opengis.net/wfs')
        _set(context, recobj, 'pycsw:MdSource', record)
        _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(context, recobj, 'pycsw:Type', 'dataset')
        _set(context, recobj, 'pycsw:ParentIdentifier', identifier)
        _set(context, recobj, 'pycsw:Title', md.contents[featuretype].title)
        _set(context, recobj, 'pycsw:Abstract', md.contents[featuretype].abstract)
        _set(context, recobj, 'pycsw:Keywords', ','.join(md.contents[featuretype].keywords))

        _set(
            context,
            recobj,
            'pycsw:AnyText',
            util.get_anytext([
                md.contents[featuretype].title,
                md.contents[featuretype].abstract,
                ','.join(md.contents[featuretype].keywords)
            ])
        )

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

        links = [{
            'name': md.contents[featuretype].id,
            'description': 'OGC-Web Feature Service',
            'protocol': 'OGC:WFS',
            'url': md.url
            }, {
            'name': md.contents[featuretype].id,
            'description': 'File for download',
            'protocol': 'WWW:DOWNLOAD-1.0-http--download',
            'url': build_get_url(md.url, params)
        }]

        _set(context, recobj, 'pycsw:Links', json.dumps(links))
        _set(context, recobj, 'pycsw:XML', caps2iso(recobj, md, context))
        _set(context, recobj, 'pycsw:MetadataType', 'application/xml')
        _set(context, recobj, 'pycsw:Contacts', 
             json.dumps(contacts,default=lambda o: o.__dict__))

        recobjs.append(recobj)

    # Derive a bbox based on aggregated featuretype bbox values

    bbox_agg = bbox_from_polygons(bboxs)

    if bbox_agg is not None:
        _set(context, serviceobj, 'pycsw:BoundingBox', bbox_agg)

    _set(context, serviceobj, 'pycsw:XML', caps2iso(serviceobj, md, context))

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
    _set(
        context,
        serviceobj,
        'pycsw:AnyText',
        util.get_anytext(etree.tostring(md._capabilities))
    )
    _set(context, serviceobj, 'pycsw:Type', 'service')
    _set(context, serviceobj, 'pycsw:Title', md.identification.title)
    _set(context, serviceobj, 'pycsw:Abstract', md.identification.abstract)
    _set(context, serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
    _set(context, serviceobj, 'pycsw:Creator', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:Publisher', md.provider.name)
    _set(context, serviceobj, 'pycsw:Contributor', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)

    contacts = [vars(md.provider.contact)]
    contacts[0]['role'] = 'pointOfContact'
    _set(context, serviceobj, 'pycsw:Contacts', 
         json.dumps(contacts,default=lambda o: o.__dict__))

    _set(context, serviceobj, 'pycsw:AccessConstraints', md.identification.accessConstraints)
    _set(context, serviceobj, 'pycsw:OtherConstraints', md.identification.fees)
    _set(context, serviceobj, 'pycsw:Source', record)
    _set(context, serviceobj, 'pycsw:Format', md.identification.type)
    _set(context, serviceobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
    _set(context, serviceobj, 'pycsw:DistanceUOM', 'degrees')
    _set(context, serviceobj, 'pycsw:ServiceType', 'OGC:WCS')
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:OperatesOn', ','.join(list(md.contents)))
    _set(context, serviceobj, 'pycsw:CouplingType', 'tight')

    links = [{
        'name': identifier,
        'description': 'OGC-WCS Web Coverage Service',
        'protocol': 'OGC:WCS',
        'url': md.url
    }]

    _set(context, serviceobj, 'pycsw:Links', json.dumps(links))

    # generate record foreach coverage

    LOGGER.info('Harvesting %d WCS coverages ', len(md.contents))

    for coverage in md.contents:
        recobj = repos.dataset()
        identifier2 = '%s-%s' % (identifier, md.contents[coverage].id)
        _set(context, recobj, 'pycsw:Identifier', identifier2)
        _set(context, recobj, 'pycsw:Typename', 'csw:Record')
        _set(context, recobj, 'pycsw:Schema', 'http://www.opengis.net/wcs')
        _set(context, recobj, 'pycsw:MdSource', record)
        _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(context, recobj, 'pycsw:Type', 'dataset')
        _set(context, recobj, 'pycsw:ParentIdentifier', identifier)
        _set(context, recobj, 'pycsw:Title', md.contents[coverage].title)
        _set(context, recobj, 'pycsw:Abstract', md.contents[coverage].abstract)
        _set(context, recobj, 'pycsw:Keywords', ','.join(md.contents[coverage].keywords))

        _set(
            context,
            recobj,
            'pycsw:AnyText',
            util.get_anytext([
                md.contents[coverage].title,
                md.contents[coverage].abstract,
                ','.join(md.contents[coverage].keywords)
            ])
        )

        bbox = md.contents[coverage].boundingBoxWGS84
        if bbox is not None:
            tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
            wkt_polygon = util.bbox2wktpolygon(tmp)
            _set(context, recobj, 'pycsw:BoundingBox', wkt_polygon)
            _set(context, recobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
            _set(context, recobj, 'pycsw:DistanceUOM', 'degrees')
            bboxs.append(wkt_polygon)

        links = [{
            'name': md.contents[coverage].id,
            'description': 'OGC-Web Coverage Service',
            'protocol': 'OGC:WCS',
            'url': md.url
        }]

        _set(context, recobj, 'pycsw:Links', json.dumps(links))
        _set(context, recobj, 'pycsw:Contacts', 
             json.dumps(contacts,default=lambda o: o.__dict__))
        _set(context, recobj, 'pycsw:XML', caps2iso(recobj, md, context))

        recobjs.append(recobj)

    # Derive a bbox based on aggregated coverage bbox values

    bbox_agg = bbox_from_polygons(bboxs)

    if bbox_agg is not None:
        _set(context, serviceobj, 'pycsw:BoundingBox', bbox_agg)

    _set(context, serviceobj, 'pycsw:XML', caps2iso(serviceobj, md, context))
    recobjs.insert(0, serviceobj)

    return recobjs

def _parse_wps(context, repos, record, identifier):

    from owslib.wps import WebProcessingService

    recobjs = []
    serviceobj = repos.dataset()

    md = WebProcessingService(record)

    # generate record of service instance
    _set(context, serviceobj, 'pycsw:Identifier', identifier)
    _set(context, serviceobj, 'pycsw:Typename', 'csw:Record')
    _set(context, serviceobj, 'pycsw:Schema', 'http://www.opengis.net/wps/1.0.0')
    _set(context, serviceobj, 'pycsw:MdSource', record)
    _set(context, serviceobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(
        context,
        serviceobj,
        'pycsw:AnyText',
        util.get_anytext(md._capabilities)
    )
    _set(context, serviceobj, 'pycsw:Type', 'service')
    _set(context, serviceobj, 'pycsw:Title', md.identification.title)
    _set(context, serviceobj, 'pycsw:Abstract', md.identification.abstract)
    _set(context, serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
    _set(context, serviceobj, 'pycsw:Creator', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:Publisher', md.provider.name)
    _set(context, serviceobj, 'pycsw:Contributor', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)

    contacts = [vars(md.provider.contact)]
    contacts[0]['role'] = 'pointOfContact'
    _set(context, serviceobj, 'pycsw:Contacts', 
         json.dumps(contacts,default=lambda o: o.__dict__))

    _set(context, serviceobj, 'pycsw:AccessConstraints', md.identification.accessconstraints)
    _set(context, serviceobj, 'pycsw:OtherConstraints', md.identification.fees)
    _set(context, serviceobj, 'pycsw:Source', record)
    _set(context, serviceobj, 'pycsw:Format', md.identification.type)

    _set(context, serviceobj, 'pycsw:ServiceType', 'OGC:WPS')
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:OperatesOn', ','.join([o.identifier for o in md.processes]))
    _set(context, serviceobj, 'pycsw:CouplingType', 'loose')

    links = [{
        'name': identifier,
        'description': 'OGC-WPS Web Processing Service',
        'protocol': 'OGC:WPS',
        'url': md.url
        }, {
        'name': identifier,
        'description': 'OGC-WPS Capabilities service (ver 1.0.0)',
        'protocol': 'OGC:WPS-1.1.0-http-get-capabilities',
        'url': build_get_url(md.url, {'service': 'WPS', 'version': '1.0.0', 'request': 'GetCapabilities'})
    }]

    _set(context, serviceobj, 'pycsw:Links', json.dumps(links))
    _set(context, serviceobj, 'pycsw:XML', caps2iso(serviceobj, md, context))
    _set(context, serviceobj, 'pycsw:MetadataType', 'application/xml')

    recobjs.append(serviceobj)

    # generate record foreach process

    LOGGER.info('Harvesting %d WPS processes', len(md.processes))

    for process in md.processes:
        recobj = repos.dataset()
        identifier2 = '%s-%s' % (identifier, process.identifier)
        _set(context, recobj, 'pycsw:Identifier', identifier2)
        _set(context, recobj, 'pycsw:Typename', 'csw:Record')
        _set(context, recobj, 'pycsw:Schema', 'http://www.opengis.net/wps/1.0.0')
        _set(context, recobj, 'pycsw:MdSource', record)
        _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(context, recobj, 'pycsw:Type', 'software')
        _set(context, recobj, 'pycsw:ParentIdentifier', identifier)
        _set(context, recobj, 'pycsw:Title', process.title)
        _set(context, recobj, 'pycsw:Abstract', process.abstract)

        _set(
            context,
            recobj,
            'pycsw:AnyText',
            util.get_anytext([process.title, process.abstract])
        )

        params = {
            'service': 'WPS',
            'version': '1.0.0',
            'request': 'DescribeProcess',
            'identifier': process.identifier
        }

        links.append({
            'name': identifier,
            'description': 'OGC-WPS DescribeProcess service (ver 1.0.0)',
            'protocol': 'OGC:WPS-1.0.0-http-describe-process',
            'url': build_get_url(md.url, {'service': 'WPS', 'version': '1.0.0', 'request': 'DescribeProcess', 'identifier': process.identifier})
        })

        _set(context, recobj, 'pycsw:Links', json.dumps(links))
        _set(context, recobj, 'pycsw:Contacts', 
             json.dumps(contacts,default=lambda o: o.__dict__))
        _set(context, recobj, 'pycsw:XML', caps2iso(recobj, md, context))
        _set(context, recobj, 'pycsw:MetadataType', 'application/xml')

        recobjs.append(recobj)

    return recobjs


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
    _set(
        context,
        serviceobj,
        'pycsw:AnyText',
        util.get_anytext(etree.tostring(md._capabilities))
    )
    _set(context, serviceobj, 'pycsw:Type', 'service')
    _set(context, serviceobj, 'pycsw:Title', md.identification.title)
    _set(context, serviceobj, 'pycsw:Abstract', md.identification.abstract)
    _set(context, serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
    _set(context, serviceobj, 'pycsw:Creator', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:Publisher', md.provider.name)
    _set(context, serviceobj, 'pycsw:Contributor', md.provider.contact.name)
    _set(context, serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)

    contacts = [vars(md.provider.contact)]
    contacts[0]['role'] = 'pointOfContact'
    _set(context, serviceobj, 'pycsw:Contacts', 
         json.dumps(contacts,default=lambda o: o.__dict__))

    _set(context, serviceobj, 'pycsw:AccessConstraints', md.identification.accessconstraints)
    _set(context, serviceobj, 'pycsw:OtherConstraints', md.identification.fees)
    _set(context, serviceobj, 'pycsw:Source', record)
    _set(context, serviceobj, 'pycsw:Format', md.identification.type)
    _set(context, serviceobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
    _set(context, serviceobj, 'pycsw:DistanceUOM', 'degrees')
    _set(context, serviceobj, 'pycsw:ServiceType', 'OGC:SOS')
    _set(context, serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
    _set(context, serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
    _set(context, serviceobj, 'pycsw:OperatesOn', ','.join(list(md.contents)))
    _set(context, serviceobj, 'pycsw:CouplingType', 'tight')

    links = [{
        'name': identifier,
        'description': 'OGC-SOS Sensor Observation Service',
        'protocol': 'OGC:SOS',
        'url': md.url
    }]

    _set(context, serviceobj, 'pycsw:Links', json.dumps(links))

    # generate record foreach offering

    LOGGER.info('Harvesting %d SOS ObservationOffering\'s ', len(md.contents))

    for offering in md.contents:
        recobj = repos.dataset()
        identifier2 = '%s-%s' % (identifier, md.contents[offering].id)
        _set(context, recobj, 'pycsw:Identifier', identifier2)
        _set(context, recobj, 'pycsw:Typename', 'csw:Record')
        _set(context, recobj, 'pycsw:Schema', schema)
        _set(context, recobj, 'pycsw:MdSource', record)
        _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(context, recobj, 'pycsw:Type', 'dataset')
        _set(context, recobj, 'pycsw:ParentIdentifier', identifier)
        _set(context, recobj, 'pycsw:Title', md.contents[offering].description)
        _set(context, recobj, 'pycsw:Abstract', md.contents[offering].description)
        begin = md.contents[offering].begin_position
        end = md.contents[offering].end_position
        _set(context, recobj, 'pycsw:TempExtent_begin',
             util.datetime2iso8601(begin) if begin is not None else None)
        _set(context, recobj, 'pycsw:TempExtent_end',
             util.datetime2iso8601(end) if end is not None else None)

        #For observed_properties that have mmi url or urn, we simply want the observation name.
        observed_properties = []
        for obs in md.contents[offering].observed_properties:
          #Observation is stored as urn representation: urn:ogc:def:phenomenon:mmisw.org:cf:sea_water_salinity
          if obs.lower().startswith(('urn:', 'x-urn')):
            observed_properties.append(obs.rsplit(':', 1)[-1])
          #Observation is stored as uri representation: http://mmisw.org/ont/cf/parameter/sea_floor_depth_below_sea_surface
          elif obs.lower().startswith(('http://', 'https://')):
            observed_properties.append(obs.rsplit('/', 1)[-1])
          else:
            observed_properties.append(obs)
        #Build anytext from description and the observed_properties.
        anytext = []
        anytext.append(md.contents[offering].description)
        anytext.extend(observed_properties)
        _set(context, recobj, 'pycsw:AnyText', util.get_anytext(anytext))
        _set(context, recobj, 'pycsw:Keywords', ','.join(observed_properties))

        bbox = md.contents[offering].bbox
        if bbox is not None:
            tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
            wkt_polygon = util.bbox2wktpolygon(tmp)
            _set(context, recobj, 'pycsw:BoundingBox', wkt_polygon)
            _set(context, recobj, 'pycsw:CRS', md.contents[offering].bbox_srs.id)
            _set(context, recobj, 'pycsw:DistanceUOM', 'degrees')
            bboxs.append(wkt_polygon)
        _set(context, recobj, 'pycsw:Contacts', 
             json.dumps(contacts,default=lambda o: o.__dict__))
        _set(context, recobj, 'pycsw:XML', caps2iso(recobj, md, context))
        _set(context, recobj, 'pycsw:MetadataType', 'application/xml')
        recobjs.append(recobj)

    # Derive a bbox based on aggregated featuretype bbox values

    bbox_agg = bbox_from_polygons(bboxs)

    if bbox_agg is not None:
        _set(context, serviceobj, 'pycsw:BoundingBox', bbox_agg)

    _set(context, serviceobj, 'pycsw:XML', caps2iso(serviceobj, md, context))
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
        _set(context, recobj, 'pycsw:Identifier', uuid.uuid1().urn)

    _set(context, recobj, 'pycsw:Typename', 'fgdc:metadata')
    _set(context, recobj, 'pycsw:Schema', context.namespaces['fgdc'])
    _set(context, recobj, 'pycsw:MdSource', 'local')
    _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, recobj, 'pycsw:XML', md.xml)
    _set(context, recobj, 'pycsw:MetadataType', 'application/xml')
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
    
    contacts = []
    if hasattr(md.idinfo, 'ptcontac'):
        _set(context, recobj, 'pycsw:OrganizationName', md.idinfo.ptcontac.cntorg)
        contacts.append(fgdccontact2iso(md.idinfo.ptcontac, 'pointOfContact'))
    
    if hasattr(md.metainfo, 'metc'):
        contacts.append(fgdccontact2iso(md.metainfo.metc, 'pointOfContact'))
    
    if hasattr(md.distinfo, 'distrib'):
        contacts.append(fgdccontact2iso(md.distinfo.distrib, 'distributor'))
    
    if len(contacts) > 0:
        _set(context, recobj, 'pycsw:Contacts', json.dumps(contacts))

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
                    links.append({
                        'name': None,
                        'description': None,
                        'protocol': None,
                        'url': link
                    })

    if hasattr(md, 'distinfo') and hasattr(md.distinfo, 'stdorder'):
        for link in md.distinfo.stdorder['digform']:
            tmp = ',%s,,%s' % (link['name'], link['url'])
            links.append({
                'name': None,
                'description': link['name'],
                'protocol': None,
                'url': link['url']
            })

    if len(links) > 0:
        _set(context, recobj, 'pycsw:Links', json.dumps(links))

    if bbox is not None:
        try:
            tmp = '%s,%s,%s,%s' % (bbox.minx, bbox.miny, bbox.maxx, bbox.maxy)
            _set(context, recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
        except Exception:
            LOGGER.debug('Coordinates are corrupt')
            _set(context, recobj, 'pycsw:BoundingBox', None)
    else:
        _set(context, recobj, 'pycsw:BoundingBox', None)

    return recobj

def _parse_gm03(context, repos, exml):

    def get_value_by_language(pt_group, language, pt_type='text'):
        for ptg in pt_group:
            if ptg.language == language:
                if pt_type == 'url':
                    val = ptg.plain_url
                else:  # 'text'
                    val = ptg.plain_text
                return val

    from owslib.gm03 import GM03

    recobj = repos.dataset()
    links = []

    md = GM03(exml)

    if hasattr(md.data, 'core'):
        data = md.data.core
    elif hasattr(md.data, 'comprehensive'):
        data = md.data.comprehensive

    language = data.metadata.language

    _set(context, recobj, 'pycsw:Identifier', data.metadata.file_identifier)
    _set(context, recobj, 'pycsw:Typename', 'gm03:TRANSFER')
    _set(context, recobj, 'pycsw:Schema', context.namespaces['gm03'])
    _set(context, recobj, 'pycsw:MdSource', 'local')
    _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, recobj, 'pycsw:XML', md.xml)
    _set(context, recobj, 'pycsw:MetadataType', 'application/xml')
    _set(context, recobj, 'pycsw:AnyText', util.get_anytext(exml))
    _set(context, recobj, 'pycsw:Language', data.metadata.language)
    _set(context, recobj, 'pycsw:Type', data.metadata.hierarchy_level[0])
    _set(context, recobj, 'pycsw:Date', data.metadata.date_stamp)

    for dt in data.date:
        if dt.date_type == 'modified':
            _set(context, recobj, 'pycsw:Modified', dt.date)
        elif dt.date_type == 'creation':
            _set(context, recobj, 'pycsw:CreationDate', dt.date)
        elif dt.date_type == 'publication':
            _set(context, recobj, 'pycsw:PublicationDate', dt.date)
        elif dt.date_type == 'revision':
            _set(context, recobj, 'pycsw:RevisionDate', dt.date)

    if hasattr(data, 'metadata_point_of_contact'):
        _set(context, recobj, 'pycsw:ResponsiblePartyRole', data.metadata_point_of_contact.role)

    _set(context, recobj, 'pycsw:Source', data.metadata.dataset_uri)
    _set(context, recobj, 'pycsw:CRS','urn:ogc:def:crs:EPSG:6.11:4326')

    if hasattr(data, 'citation'):
        _set(context, recobj, 'pycsw:Title', get_value_by_language(data.citation.title.pt_group, language))

    if hasattr(data, 'data_identification'):
        _set(context, recobj, 'pycsw:Abstract', get_value_by_language(data.data_identification.abstract.pt_group, language))
        if hasattr(data.data_identification, 'topic_category'):
            _set(context, recobj, 'pycsw:TopicCategory', data.data_identification.topic_category)
        _set(context, recobj, 'pycsw:ResourceLanguage', data.data_identification.language)

    if hasattr(data, 'format'):
        _set(context, recobj, 'pycsw:Format', data.format.name)

    # bbox
    if hasattr(data, 'geographic_bounding_box'):
        try:
            tmp = '%s,%s,%s,%s' % (data.geographic_bounding_box.west_bound_longitude,
                                   data.geographic_bounding_box.south_bound_latitude,
                                   data.geographic_bounding_box.east_bound_longitude,
                                   data.geographic_bounding_box.north_bound_latitude)
            _set(context, recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
        except Exception:
            LOGGER.debug('Coordinates are corrupt')
            _set(context, recobj, 'pycsw:BoundingBox', None)
    else:
        _set(context, recobj, 'pycsw:BoundingBox', None)

    # temporal extent
    if hasattr(data, 'temporal_extent'):
        if data.temporal_extent.extent['begin'] is not None and data.temporal_extent.extent['end'] is not None:
            _set(context, recobj, 'pycsw:TempExtent_begin', data.temporal_extent.extent['begin'])
            _set(context, recobj, 'pycsw:TempExtent_end', data.temporal_extent.extent['end'])

    # online linkages
    name = description = protocol = ''

    if hasattr(data, 'online_resource'):
        if hasattr(data.online_resource, 'name'):
            name = get_value_by_language(data.online_resource.name.pt_group, language)
        if hasattr(data.online_resource, 'description'):
            description = get_value_by_language(data.online_resource.description.pt_group, language)
        linkage = get_value_by_language(data.online_resource.linkage.pt_group, language, 'url')

        links.append({
            'name': name,
            'description': description,
            'protocol': protocol,
            'url': linkage
        })

    if len(links) > 0:
        _set(context, recobj, 'pycsw:Links', json.dumps(links))

    keywords = []
    for kw in data.keywords:
        keywords.append(get_value_by_language(kw.keyword.pt_group, language))
        _set(context, recobj, 'pycsw:Keywords', ','.join(keywords))

    # contacts
    return recobj

def _parse_iso(context, repos, exml):
    """ Parses ISO 19139, ISO 19115p3 """

    from owslib.iso import MD_ImageDescription, MD_Metadata, SV_ServiceIdentification
    from owslib.iso_che import CHE_MD_Metadata

    recobj = repos.dataset()
    bbox = None
    links = []
    mdmeta_ns = 'gmd'

    if exml.tag == '{http://www.geocat.ch/2008/che}CHE_MD_Metadata':
        md = CHE_MD_Metadata(exml)
    elif exml.tag == '{http://standards.iso.org/iso/19115/-3/mdb/2.0}MD_Metadata':
        from owslib.iso3 import MD_Metadata
        md = MD_Metadata(exml)
        mdmeta_ns = 'mdb'
    else:
        md = MD_Metadata(exml)

    md_identification = md.identification[0]

    _set(context, recobj, 'pycsw:Identifier', md.identifier)
    _set(context, recobj, 'pycsw:Typename', f'{mdmeta_ns}:MD_Metadata')
    _set(context, recobj, 'pycsw:Schema', context.namespaces['gmd'])
    _set(context, recobj, 'pycsw:MdSource', 'local')
    _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, recobj, 'pycsw:XML', md.xml)
    _set(context, recobj, 'pycsw:MetadataType', 'application/xml')
    _set(context, recobj, 'pycsw:AnyText', util.get_anytext(exml))
    _set(context, recobj, 'pycsw:Language', md.language or md.languagecode)
    _set(context, recobj, 'pycsw:Type', md.hierarchy)
    _set(context, recobj, 'pycsw:ParentIdentifier', md.parentidentifier)
    _set(context, recobj, 'pycsw:Date', md.datestamp)
    _set(context, recobj, 'pycsw:Modified', md.datestamp)
    _set(context, recobj, 'pycsw:Source', md.dataseturi)

    if md.referencesystem is not None and md.referencesystem.code is not None:
        try:
            code_ = 'urn:ogc:def:crs:EPSG::%d' % int(md.referencesystem.code)
        except ValueError:
            code_ = md.referencesystem.code
        _set(context, recobj, 'pycsw:CRS', code_)

    if md_identification:
        _set(context, recobj, 'pycsw:Title', md_identification.title)
        _set(context, recobj, 'pycsw:Edition', md_identification.edition)
        _set(context, recobj, 'pycsw:AlternateTitle', md_identification.alternatetitle)
        _set(context, recobj, 'pycsw:Abstract', md_identification.abstract)
        _set(context, recobj, 'pycsw:Relation', md_identification.aggregationinfo)

        if hasattr(md_identification, 'temporalextent_start'):
            _set(context, recobj, 'pycsw:TempExtent_begin', md_identification.temporalextent_start)
        if hasattr(md_identification, 'temporalextent_end'):
            _set(context, recobj, 'pycsw:TempExtent_end', md_identification.temporalextent_end)

        if len(md_identification.topiccategory) > 0:
            _set(context, recobj, 'pycsw:TopicCategory', md_identification.topiccategory[0])

        if len(md_identification.resourcelanguage) > 0:
            _set(context, recobj, 'pycsw:ResourceLanguage', md_identification.resourcelanguage[0])
        elif len(md_identification.resourcelanguagecode) > 0:
            _set(context, recobj, 'pycsw:ResourceLanguage', md_identification.resourcelanguagecode[0])

        # Geographic bounding box
        if hasattr(md_identification, 'bbox'):
            bbox = md_identification.bbox
        else:
            bbox = None

        # Vertical extent of a bounding box
        if hasattr(md_identification, 'extent'):
            if hasattr(md_identification.extent, 'vertExtMin') and \
                md_identification.extent.vertExtMin is not None:
                _set(context, recobj, 'pycsw:VertExtentMin', md_identification.extent.vertExtMin)
            if hasattr(md_identification.extent, 'vertExtMax') and \
                md_identification.extent.vertExtMax is not None:
                _set(context, recobj, 'pycsw:VertExtentMax', md_identification.extent.vertExtMax)

        if (hasattr(md_identification, 'keywords') and
            len(md_identification.keywords) > 0):
            all_keywords = [item for sublist in md_identification.keywords for item in sublist.keywords if item is not None]
            _set(context, recobj, 'pycsw:Keywords', ','.join([
                k.name for k in all_keywords if hasattr(k,'name') and k.name not in [None,'']]))
            _set(context, recobj, 'pycsw:KeywordType', md_identification.keywords[0].type)
            _set(context, recobj, 'pycsw:Themes', 
                json.dumps([t for t in md_identification.keywords if t.thesaurus is not None], 
                            default=lambda o: o.__dict__))

        # Creator
        if (hasattr(md_identification, 'creator') and
            len(md_identification.creator) > 0):
            all_orgs = set([item.organization for item in md_identification.creator if hasattr(item, 'organization') and item.organization is not None])
            _set(context, recobj, 'pycsw:Creator', ';'.join(all_orgs))
        # Publisher
        if (hasattr(md_identification, 'publisher') and
            len(md_identification.publisher) > 0):
            all_orgs = set([item.organization for item in md_identification.publisher if hasattr(item, 'organization') and item.organization is not None])
            _set(context, recobj, 'pycsw:Publisher', ';'.join(all_orgs))
        # Contributor
        if (hasattr(md_identification, 'contributor') and
            len(md_identification.contributor) > 0):
            all_orgs = set([item.organization for item in md_identification.contributor if hasattr(item, 'organization') and item.organization is not None])
            _set(context, recobj, 'pycsw:Contributor', ';'.join(all_orgs))

        if (hasattr(md_identification, 'contact') and
            len(md_identification.contact) > 0):
            all_orgs = set([item.organization for item in md_identification.contact if hasattr(item, 'organization') and item.organization is not None])
            _set(context, recobj, 'pycsw:OrganizationName', ';'.join(all_orgs))
            _set(context, recobj, 'pycsw:Contacts', json.dumps(md_identification.contact, default=lambda o: o.__dict__))

        if len(md_identification.securityconstraints) > 0:
            _set(context, recobj, 'pycsw:SecurityConstraints',
            md_identification.securityconstraints[0])
        if len(md_identification.accessconstraints) > 0:
            _set(context, recobj, 'pycsw:AccessConstraints',
            md_identification.accessconstraints[0])
        if len(md_identification.otherconstraints) > 0:
            _set(context, recobj, 'pycsw:OtherConstraints', md_identification.otherconstraints[0])

        if hasattr(md_identification, 'date'):
            for datenode in md_identification.date:
                if datenode.type == 'revision':
                    _set(context, recobj, 'pycsw:RevisionDate', datenode.date)
                elif datenode.type == 'creation':
                    _set(context, recobj, 'pycsw:CreationDate', datenode.date)
                elif datenode.type == 'publication':
                    _set(context, recobj, 'pycsw:PublicationDate', datenode.date)

        if hasattr(md_identification, 'extent') and hasattr(md_identification.extent, 'description_code'):
            _set(context, recobj, 'pycsw:GeographicDescriptionCode', md_identification.extent.description_code)

        if len(md_identification.denominators) > 0:
            _set(context, recobj, 'pycsw:Denominator', md_identification.denominators[0])
        if len(md_identification.distance) > 0:
            _set(context, recobj, 'pycsw:DistanceValue', md_identification.distance[0])
        if len(md_identification.uom) > 0:
            _set(context, recobj, 'pycsw:DistanceUOM', md_identification.uom[0])

        if len(md_identification.classification) > 0:
            _set(context, recobj, 'pycsw:Classification', md_identification.classification[0])
        if len(md_identification.uselimitation) > 0:
            _set(context, recobj, 'pycsw:ConditionApplyingToAccessAndUse',
            md_identification.uselimitation[0])

    service_types = []
    from owslib.iso import SV_ServiceIdentification
    for smd in md.identification:
        if isinstance(smd, SV_ServiceIdentification):
            service_types.append(smd.type)
            _set(context, recobj, 'pycsw:ServiceTypeVersion', smd.version)
            _set(context, recobj, 'pycsw:CouplingType', smd.couplingtype)

    _set(context, recobj, 'pycsw:ServiceType', ','.join(service_types))

    if hasattr(md_identification, 'dataquality'):
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


    if hasattr(md, 'contentinfo') and len(md.contentinfo) > 0:
        for ci in md.contentinfo:
            if isinstance(ci, MD_ImageDescription):
                _set(context, recobj, 'pycsw:CloudCover', ci.cloud_cover)

                keywords = _get(context, recobj, 'pycsw:Keywords')
                if ci.processing_level is not None:
                    pl_keyword = 'eo:processingLevel:' + ci.processing_level
                    if keywords is None:
                        keywords  = pl_keyword
                    else:
                        keywords  += ',' + pl_keyword

                    _set(context, recobj, 'pycsw:Keywords', keywords)

                bands = []
                for band in ci.bands:
                    band_info = {
                        'id': band.id,
                        'units': band.units,
                        'min': band.min,
                        'max': band.max
                    }
                    bands.append(band_info)

                if len(bands) > 0:
                    _set(context, recobj, 'pycsw:Bands', json.dumps(bands))

    if hasattr(md, 'acquisition') and md.acquisition is not None:
        platform = md.acquisition.platforms[0]
        _set(context, recobj, 'pycsw:Platform', platform.identifier)

        if platform.instruments:
            instrument = platform.instruments[0]
            _set(context, recobj, 'pycsw:Instrument', instrument.identifier)
            _set(context, recobj, 'pycsw:SensorType', instrument.type)

    all_formats=[]
    if hasattr(md.distribution, 'format') and md.distribution.format is not None:
        all_formats.append(md.distribution.format)

    LOGGER.info('Scanning for links')
    if hasattr(md, 'distribution'):
        dist_links = []
        if hasattr(md.distribution, 'online'):
            LOGGER.debug(f'Scanning for {mdmeta_ns}:transferOptions element(s)')
            dist_links.extend(md.distribution.online)
        if hasattr(md.distribution, 'distributor'):
            LOGGER.debug(f'Scanning for {mdmeta_ns}:distributorTransferOptions element(s)')
            for dist_member in md.distribution.distributor:
                dist_links.extend(dist_member.online)
        for link in dist_links:
            if link.url is not None and link.protocol is None:  # take a best guess
                link.protocol = sniff_link(link.url)
            if (link.protocol is not None and link.protocol not in all_formats):
                all_formats.append(link.protocol)
            links.append({
                'name': link.name,
                'description': link.description,
                'protocol': link.protocol,
                'url': link.url,
                'function': link.function
            })

    _set(context, recobj, 'pycsw:Format', ','.join(all_formats))

    try:
        LOGGER.debug('Scanning for srv:SV_ServiceIdentification links')
        for sident in md.identification:
            if hasattr(sident, 'operations'):
                for sops in sident.operations:
                    for scpt in sops['connectpoint']:
                        LOGGER.debug('adding srv link %s', scpt.url)
                        linkobj = {
                            'name': scpt.name,
                            'description': scpt.description,
                            'protocol': scpt.protocol,
                            'url': scpt.url
                        }
                        links.append(linkobj)
    except Exception as err:  # srv: identification does not exist
        LOGGER.exception('no srv:SV_ServiceIdentification links found')

    if hasattr(md_identification, 'graphicoverview'):
        for thumb in  md_identification.graphicoverview:
            links.append({
                'name': 'preview',
                'description': 'Web image thumbnail (URL)',
                'protocol': 'WWW:LINK-1.0-http--image-thumbnail',
                'url': thumb
            })

    if len(links) > 0:
        _set(context, recobj, 'pycsw:Links', json.dumps(links))

    if bbox is not None:
        try:
            tmp = '%s,%s,%s,%s' % (bbox.minx, bbox.miny, bbox.maxx, bbox.maxy)
            _set(context, recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
        except Exception:
            LOGGER.debug('Coordinates are corrupt')
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
    _set(context, recobj, 'pycsw:MetadataType', 'application/xml')
    _set(context, recobj, 'pycsw:AnyText', util.get_anytext(exml))
    _set(context, recobj, 'pycsw:Language', md.language)
    _set(context, recobj, 'pycsw:Type', md.type)
    _set(context, recobj, 'pycsw:Title', md.title)
    _set(context, recobj, 'pycsw:AlternateTitle', md.alternative)
    _set(context, recobj, 'pycsw:Abstract', md.abstract)

    if md.subjects is not None and len(md.subjects) > 0 and None not in md.subjects:
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
    if md.rights is not None and len(md.rights) > 0 and None not in md.rights:
        _set(context, recobj, 'pycsw:ConditionApplyingToAccessAndUse', ','.join(md.rights))
    _set(context, recobj, 'pycsw:AccessConstraints', md.accessrights)
    _set(context, recobj, 'pycsw:OtherConstraints', md.license)
    _set(context, recobj, 'pycsw:Date', md.date)
    _set(context, recobj, 'pycsw:CreationDate', md.created)
    _set(context, recobj, 'pycsw:PublicationDate', md.issued)
    _set(context, recobj, 'pycsw:Modified', md.modified)
    _set(context, recobj, 'pycsw:Format', md.format)
    _set(context, recobj, 'pycsw:Source', md.source)

    for ref in md.references:
        links.append({
            'name': None,
            'description': None,
            'protocol': ref['scheme'],
            'url': ref['url'],
        })
    for uri in md.uris:
        links.append({
            'name': uri['name'],
            'description': uri['description'],
            'protocol': uri['protocol'],
            'url': uri['url'],
        })

    if len(links) > 0:
        _set(context, recobj, 'pycsw:Links', json.dumps(links))

    if bbox is not None:
        try:
            tmp = '%s,%s,%s,%s' % (bbox.minx, bbox.miny, bbox.maxx, bbox.maxy)
            _set(context, recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
        except Exception:
            LOGGER.debug('Coordinates are corrupt')
            _set(context, recobj, 'pycsw:BoundingBox', None)
    else:
        _set(context, recobj, 'pycsw:BoundingBox', None)

    return recobj


def _parse_json_record(context, repos, record):
    """Parse JSON record"""

    recobj = None

    if 'conformsTo' in record:
        LOGGER.debug('Parsing OGC API - Records record model')
        recobj = _parse_oarec_record(context, repos, record)
    elif 'stac_version' in record:
        LOGGER.debug('Parsing STAC resource')
        recobj = _parse_stac_resource(context, repos, record)

    if recobj is None:
        raise RuntimeError('Unsupported JSON metadata format')

    atom_xml = atom.write_record(recobj, 'full', context)

    _set(context, recobj, 'pycsw:XML', etree.tostring(atom_xml))

    return recobj


def _parse_oarec_record(context, repos, record):
    """Parse OARec record"""

    conformance = 'http://www.opengis.net/spec/ogcapi-records-1/1.0/req/record-core'

    recobj = repos.dataset()
    keywords = []
    links = []

    _set(context, recobj, 'pycsw:Identifier', record['id'])
    _set(context, recobj, 'pycsw:Typename', 'csw:Record')
    _set(context, recobj, 'pycsw:Schema', conformance)
    _set(context, recobj, 'pycsw:MdSource', 'local')
    _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, recobj, 'pycsw:XML', '')  # FIXME: transform into XML? or not, to validate
    _set(context, recobj, 'pycsw:Metadata', json.dumps(record))
    _set(context, recobj, 'pycsw:MetadataType', 'application/geo+json')

    _set(context, recobj, 'pycsw:AnyText', ' '.join([str(t) for t in util.get_anytext_from_obj(record)]))

    _set(context, recobj, 'pycsw:Language', record['properties'].get('language', {}).get('code'))
    _set(context, recobj, 'pycsw:Type', record['properties']['type'])
    _set(context, recobj, 'pycsw:Title', record['properties']['title'])
    _set(context, recobj, 'pycsw:Abstract', record['properties'].get('description'))

    if 'keywords' in record['properties']:
        keywords = record['properties']['keywords']
        _set(context, recobj, 'pycsw:Keywords', ','.join(keywords))

    if 'themes' in record['properties']:
        _set(context, recobj, 'pycsw:Themes', json.dumps(record['properties']['themes']))

    if 'links' in record:
        for link in record['links']:
            new_link = {
                'url': link.get('href')
            }

            if link.get('title') is not None:
                new_link['name'] = link.get('title')
                new_link['description'] = link.get('title')
            if link.get('description') is not None:
                new_link['description'] = link.get('description')
            if link.get('type') is not None:
                new_link['protocol'] = link.get('type')
            if link.get('rel') is not None:
                new_link['function'] = link.get('rel')

            links.append(new_link)

    if links:
        _set(context, recobj, 'pycsw:Links', json.dumps(links))

    if record.get('geometry') is not None:
        _set(context, recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(util.geojson_geometry2bbox(record['geometry'])))

    if 'temporal' in record['properties'].get('extent', []):
        _set(context, recobj, 'pycsw:TempExtent_begin', record['properties']['extent']['temporal']['interval'][0])
        _set(context, recobj, 'pycsw:TempExtent_end', record['properties']['extent']['temporal']['interval'][1])

    return recobj


def _parse_stac_resource(context, repos, record):
    """Parse STAC resource"""

    recobj = repos.dataset()
    keywords = []
    links = []
    bbox_wkt = None

    stac_type = record.get('type', 'Feature')
    if stac_type == 'Feature':
        LOGGER.debug('Parsing STAC Item')
        conformance = 'https://github.com/radiantearth/stac-spec/tree/master/item-spec/item-spec.md'
        typename = 'stac:Item'
        metadata_type = 'application/geo+json'
        stype = 'item'
        title = record['properties'].get('title')
        abstract = record['properties'].get('description')
        if record.get('geometry') is not None:
            bbox_wkt = util.bbox2wktpolygon(util.geojson_geometry2bbox(record['geometry']))
    elif stac_type == 'Collection':
        LOGGER.debug('Parsing STAC Collection')
        conformance = 'https://github.com/radiantearth/stac-spec/tree/master/collection-spec/collection-spec.md'
        typename = 'stac:Collection'
        metadata_type = 'application/json'
        stype = 'collection'
        title = record.get('title')
        abstract = record.get('description')
        if 'extent' in record and 'spatial' in record['extent']:
            bbox_csv = ','.join(str(t) for t in record['extent']['spatial']['bbox'][0])
            bbox_wkt = util.bbox2wktpolygon(bbox_csv)
        if 'extent' in record and 'temporal' in record['extent'] and 'interval' in record['extent']['temporal']:
            _set(context, recobj, 'pycsw:TempExtent_begin', record['extent']['temporal']['interval'][0][0])
            _set(context, recobj, 'pycsw:TempExtent_end', record['extent']['temporal']['interval'][0][1])
    elif stac_type == 'Catalog':
        LOGGER.debug('Parsing STAC Catalog')
        conformance = 'https://github.com/radiantearth/stac-spec/tree/master/catalog-spec/catalog-spec.md'
        typename = 'stac:Catalog'
        metadata_type = 'application/json'
        stype = 'catalog'
        title = record.get('title')
        abstract = record.get('description')

    _set(context, recobj, 'pycsw:Identifier', record['id'])
    _set(context, recobj, 'pycsw:Typename', typename)
    _set(context, recobj, 'pycsw:Schema', conformance)
    _set(context, recobj, 'pycsw:MdSource', 'local')
    _set(context, recobj, 'pycsw:InsertDate', util.get_today_and_now())
    _set(context, recobj, 'pycsw:XML', '')  # FIXME: transform into XML? or not, to validate
    _set(context, recobj, 'pycsw:Metadata', json.dumps(record))
    _set(context, recobj, 'pycsw:MetadataType', metadata_type)
    _set(context, recobj, 'pycsw:AnyText', ' '.join([str(t) for t in util.get_anytext_from_obj(record)]))
    _set(context, recobj, 'pycsw:Type', stype)
    _set(context, recobj, 'pycsw:Title', title)
    _set(context, recobj, 'pycsw:Abstract', abstract)
    _set(context, recobj, 'pycsw:BoundingBox', bbox_wkt)

    if 'links' in record:
        for link in record['links']:
            new_link = {
                'url': link.get('href')
            }

            if link.get('title') is not None:
                new_link['name'] = link.get('title')
                new_link['description'] = link.get('title')
            if link.get('description') is not None:
                new_link['description'] = link.get('description')
            if link.get('type') is not None:
                new_link['protocol'] = link.get('type')
            if link.get('rel') is not None:
                new_link['function'] = link.get('rel')

            links.append(new_link)

    if 'assets' in record:
        for key, link in record['assets'].items():
            new_link = {
                'url': link.get('href')
            }

            if link.get('title') is not None:
                new_link['name'] = link.get('title')
                new_link['description'] = link.get('title')
            if link.get('type') is not None:
                new_link['protocol'] = link.get('type')
            if link.get('rel') is not None:
                new_link['function'] = link.get('rel')
            else:
                new_link['function'] = 'enclosure'

            links.append(new_link)

    if links:
        _set(context, recobj, 'pycsw:Links', json.dumps(links))

    if stac_type == 'Feature':
        if 'keywords' in record['properties']:
            keywords = record['properties']['keywords']
            _set(context, recobj, 'pycsw:Keywords', ','.join(keywords))

        if 'start_datetime' in record['properties']:
            _set(context, recobj, 'pycsw:TempExtent_begin', record['properties']['start_datetime'])

        if 'end_datetime' in record['properties']:
            _set(context, recobj, 'pycsw:TempExtent_end', record['properties']['end_datetime'])

        if 'datetime' in record['properties']:
            _set(context, recobj, 'pycsw:Date', record['properties']['datetime'])
            if 'start_datetime' not in record['properties'] and 'end_datetime' not in record['properties']:
                _set(context, recobj, 'pycsw:TempExtent_begin', record['properties']['datetime'])
                _set(context, recobj, 'pycsw:TempExtent_end', record['properties']['datetime'])

        if 'eo:cloud_cover' in record['properties']:
            _set(context, recobj, 'pycsw:CloudCover', record['properties']['eo:cloud_cover'])

        if 'collection' in record:
            _set(context, recobj, 'pycsw:ParentIdentifier', record['collection'])

    if stac_type in ['Collection', 'Catalog']:
        if 'keywords' in record:
            keywords = record['keywords']
            _set(context, recobj, 'pycsw:Keywords', ','.join(keywords))

        if 'start_datetime' in record:
            _set(context, recobj, 'pycsw:TempExtent_begin', record['start_datetime'])

        if 'end_datetime' in record:
            _set(context, recobj, 'pycsw:TempExtent_end', record['end_datetime'])

        if 'datetime' in record:
            _set(context, recobj, 'pycsw:Date', record['datetime'])
            if 'start_datetime' not in record and 'end_datetime' not in record:
                _set(context, recobj, 'pycsw:TempExtent_begin', record['datetime'])
                _set(context, recobj, 'pycsw:TempExtent_end', record['datetime'])

    return recobj

def fgdccontact2iso(cnt, role='pointOfContact'):
    """Creates a iso format contact (owslib style) from fgdc format"""

    return {'name': cnt.cntper, 
            'organization': cnt.cntorg, 
            'position': cnt.cntpos, 
            'phone': cnt.voice, 
            'address': cnt.address, 
            'city': cnt.city, 
            'region': cnt.state,
            'postcode': cnt.postal, 
            'country': cnt.country, 
            'email': cnt.email, 
            'role': role
    }

def caps2iso(record, caps, context):
    """Creates ISO metadata from Capabilities XML"""

    from pycsw.plugins.profiles.apiso.apiso import APISO

    apiso_obj = APISO(context.model, context.namespaces, context)
    apiso_obj.ogc_schemas_base = 'http://schemas.opengis.net'
    apiso_obj.url = context.url
    queryables = dict(apiso_obj.repository['queryables']['SupportedISOQueryables'].items())
    iso_xml = apiso_obj.write_record(record, 'full', 'http://www.isotc211.org/2005/gmd', queryables, caps)
    return etree.tostring(iso_xml)


def bbox_from_polygons(bboxs):
    """Derive an aggregated bbox from n polygons

    Parameters
    ----------
    bboxs: list
        A sequence of strings containing Well-Known Text representations of
        polygons

    Returns
    -------
    str
        Well-Known Text representation of the aggregated bounding box for
        all the input polygons
    """

    try:
        multi_pol = MultiPolygon(
            [loads(bbox) for bbox in bboxs]
        )
        bstr = ",".join([f"{b:.2f}" for b in multi_pol.bounds])
        return util.bbox2wktpolygon(bstr)
    except Exception as err:
        raise RuntimeError('Cannot aggregate polygons: %s' % str(err)) from err
