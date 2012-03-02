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

import uuid
from lxml import etree
import config, util
from owslib.csw import CswRecord
from owslib.wms import WebMapService
from owslib.iso import MD_Metadata
from owslib.fgdc import Metadata

def parse_record(record, repos=None,
    mtype='http://www.opengis.net/cat/csw/2.0.2', identifier=None):
    ''' parse metadata '''

    recobj = repos.dataset()
    links = []

    # parse web services
    if mtype == 'http://www.opengis.net/wms':

        recobjs = []
        serviceobj = repos.dataset()

        md = WebMapService(record)

        if identifier is None:
            identifier = uuid.uuid1().get_urn()

        # generate record of service instance
        _set(serviceobj, 'pycsw:Identifier', identifier)
        _set(serviceobj, 'pycsw:Typename', 'gmd:MD_Metadata')
        _set(serviceobj, 'pycsw:Schema', 'http://www.opengis.net/wms')
        _set(serviceobj, 'pycsw:MdSource', record)
        _set(serviceobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(serviceobj, 'pycsw:XML', md.getServiceXML())
        _set(serviceobj, 'pycsw:AnyText', util.get_anytext(md.getServiceXML()))
        _set(serviceobj, 'pycsw:Type', 'service')
        _set(serviceobj, 'pycsw:Title', md.identification.title)
        _set(serviceobj, 'pycsw:Abstract', md.identification.abstract)
        _set(serviceobj, 'pycsw:Keywords', ','.join(md.identification.keywords))
        _set(serviceobj, 'pycsw:Creator', md.provider.contact.name)
        _set(serviceobj, 'pycsw:Publisher', md.provider.contact.name)
        _set(serviceobj, 'pycsw:Contributor', md.provider.contact.name)
        _set(serviceobj, 'pycsw:OrganizationName', md.provider.contact.name)
        _set(serviceobj, 'pycsw:AccessConstraints', md.identification.accessconstraints)
        _set(serviceobj, 'pycsw:OtherConstraints', md.identification.fees)
        _set(serviceobj,  'pycsw:Source', record)
        _set(serviceobj, 'pycsw:Format', md.identification.type)
        for c in md.contents:
            if md.contents[c].parent is None:
                bbox = md.contents[c].boundingBoxWGS84
                tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
                _set(serviceobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
                break
        _set(serviceobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
        _set(serviceobj, 'pycsw:DistanceUOM', 'degrees')
        _set(serviceobj, 'pycsw:ServiceType', md.identification.type)
        _set(serviceobj, 'pycsw:ServiceTypeVersion', md.identification.version)
        _set(serviceobj, 'pycsw:Operation', ','.join([d.name for d in md.operations]))
        _set(serviceobj, 'pycsw:OperatesOn', ','.join(list(md.contents)))
        _set(serviceobj, 'pycsw:CouplingType', 'tight')

        recobjs.append(serviceobj) 
         
        # generate record foreach layer
        for layer in md.contents:
            recobj = repos.dataset()
            _set(recobj, 'pycsw:Identifier', md.contents[layer].name)
            _set(recobj, 'pycsw:Typename', 'gmd:MD_Metadata')
            _set(recobj, 'pycsw:Schema', 'http://www.opengis.net/wms')
            _set(recobj, 'pycsw:MdSource', record)
            _set(recobj, 'pycsw:InsertDate', util.get_today_and_now())
            _set(recobj, 'pycsw:XML', md.getServiceXML())
            _set(recobj, 'pycsw:AnyText', util.get_anytext(md._capabilities))
            _set(recobj, 'pycsw:Type', 'dataset')
            _set(recobj, 'pycsw:ParentIdentifier', identifier)
            _set(recobj, 'pycsw:Title', md.contents[layer].title)
            _set(recobj, 'pycsw:Abstract', md.contents[layer].abstract)
            _set(recobj, 'pycsw:Keywords', ','.join(md.contents[layer].keywords))

            bbox = md.contents[layer].boundingBoxWGS84
            if bbox is not None:
                tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
                _set(recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
                _set(recobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:4326')
                _set(recobj, 'pycsw:Denominator', 'degrees')
            else:
                bbox = md.contents[layer].boundingBox
                if bbox:
                    tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
                    _set(recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
                    _set(recobj, 'pycsw:CRS', 'urn:ogc:def:crs:EPSG:6.11:%s' % \
                    bbox[-1].split(':')[1])

            recobjs.append(recobj)

        return recobjs
     
    # parse metadata records
    if isinstance(record, str):
        exml = etree.fromstring(record)
    else:  # already serialized to lxml
        if hasattr(record, 'getroot'):  # standalone document
            exml = record.getroot()
        else:  # part of a larger document
            exml = record

    root = exml.tag

    if root == '{%s}MD_Metadata' % config.NAMESPACES['gmd']:  # ISO

        md = MD_Metadata(exml)

        _set(recobj, 'pycsw:Identifier', md.identifier)
        _set(recobj, 'pycsw:Typename', 'gmd:MD_Metadata')
        _set(recobj, 'pycsw:Schema', config.NAMESPACES['gmd'])
        _set(recobj, 'pycsw:MdSource', 'local')
        _set(recobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(recobj, 'pycsw:XML', md.xml)
        _set(recobj, 'pycsw:AnyText', util.get_anytext(exml))
        _set(recobj, 'pycsw:Language', md.language)
        _set(recobj, 'pycsw:Type', md.hierarchy)
        _set(recobj, 'pycsw:ParentIdentifier', md.parentidentifier)
        _set(recobj, 'pycsw:Date', md.datestamp)
        _set(recobj, 'pycsw:Source', md.dataseturi)
        if md.referencesystem is not None:
            _set(recobj, 'pycsw:CRS','urn:ogc:def:crs:EPSG:6.11:%s' %
            md.referencesystem.code)

        if hasattr(md, 'identification'):
            _set(recobj, 'pycsw:Title', md.identification.title)
            _set(recobj, 'pycsw:AlternateTitle', md.identification.alternatetitle)
            _set(recobj, 'pycsw:Abstract', md.identification.abstract)
            _set(recobj, 'pycsw:Relation', md.identification.aggregationinfo)
            _set(recobj, 'pycsw:TempExtent_begin', md.identification.temporalextent_start)
            _set(recobj, 'pycsw:TempExtent_end', md.identification.temporalextent_end)

            if len(md.identification.topiccategory) > 0:
                _set(recobj, 'pycsw:TopiCategory', md.identification.topiccategory[0])

            if len(md.identification.resourcelanguage) > 0:
                _set(recobj, 'pycsw:ResourceLanguage', md.identification.resourcelanguage[0])
 
            if hasattr(md.identification, 'bbox'):
                bbox = md.identification.bbox
            else:
                bbox = None

            if (hasattr(md.identification, 'keywords') and
            len(md.identification.keywords) > 0):
                if None not in md.identification.keywords[0]['keywords']:
                    _set(recobj, 'pycsw:Keywords', ','.join(
                    md.identification.keywords[0]['keywords']))
                    _set(recobj, 'pycsw:KeywordType', md.identification.keywords[0]['type'])

            if hasattr(md.identification, 'creator'):
                _set(recobj, 'pycsw:Creator', md.identification.creator)
            if hasattr(md.identification, 'publisher'):
                _set(recobj, 'pycsw:Publisher', md.identification.publisher)
            if hasattr(md.identification, 'contributor'):
                _set(recobj, 'pycsw:Contributor', md.identification.contributor)

            if (hasattr(md.identification, 'contact') and 
            hasattr(md.identification.contact, 'organization')):
                _set(recobj, 'pycsw:OrganizationName', md.identification.contact.organization)

            if len(md.identification.securityconstraints) > 0:
                _set(recobj, 'pycsw:SecurityConstraints', 
                md.identification.securityconstraints[0])
            if len(md.identification.accessconstraints) > 0:
                _set(recobj, 'pycsw:AccessConstraints', 
                md.identification.accessconstraints[0])
            if len(md.identification.otherconstraints) > 0:
                _set(recobj, 'pycsw:OtherConstraints', md.identification.otherconstraints[0])

            if hasattr(md.identification, 'date'):
                for datenode in md.identification.date:
                    if datenode.type == 'revision':
                        _set(recobj, 'pycsw:RevisionDate', datenode.date)
                    elif datenode.type == 'creation':
                        _set(recobj, 'pycsw:CreationDate', datenode.date)
                    elif datenode.type == 'publication':
                        _set(recobj, 'pycsw:PublicationDate', datenode.date)

            _set(recobj, 'pycsw:GeographicDescriptionCode', md.identification.bbox.description_code)

            if len(md.identification.denominators) > 0:
                _set(recobj, 'pycsw:Denominator', md.identification.denominators[0])
            if len(md.identification.distance) > 0:
                _set(recobj, 'pycsw:DistanceValue', md.identification.distance[0])
            if len(md.identification.uom) > 0:
                _set(recobj, 'pycsw:DistanceUOM', md.identification.uom[0])

            if len(md.identification.classification) > 0:
                _set(recobj, 'pycsw:Classification', md.identification.classification[0])
            if len(md.identification.uselimitation) > 0:
                _set(recobj, 'pycsw:ConditionApplyingToAccessAndUse',
                md.identification.uselimitation[0])

        if hasattr(md.identification, 'format'):
            _set(recobj, 'pycsw:Format', md.distribution.format)

        if md.serviceidentification is not None:
            _set(recobj, 'pycsw:ServiceType', md.serviceidentification.type)
            _set(recobj, 'pycsw:ServiceTypeVersion', md.serviceidentification.version)

            _set(recobj, 'pycsw:CouplingType', md.serviceidentification.couplingtype)
       
            #if len(md.serviceidentification.operateson) > 0: 
            #    _set(recobj, 'pycsw:operateson = VARCHAR(32), 
            #_set(recobj, 'pycsw:operation VARCHAR(32), 
            #_set(recobj, 'pycsw:operatesonidentifier VARCHAR(32), 
            #_set(recobj, 'pycsw:operatesoname VARCHAR(32), 


        if hasattr(md.identification, 'dataquality'):     
            _set(recobj, 'pycsw:Degree', md.dataquality.conformancedegree)
            _set(recobj, 'pycsw:Lineage', md.dataquality.lineage)
            _set(recobj, 'pycsw:SpecificationTitle', md.dataquality.specificationtitle)
            if hasattr(md.dataquality, 'specificationdate'):
                _set(recobj, 'pycsw:specificationDate',
                md.dataquality.specificationdate[0].date)
                _set(recobj, 'pycsw:SpecificationDateType',
                md.dataquality.specificationdate[0].datetype)

        if hasattr(md, 'contact') and len(md.contact) > 0:
            _set(recobj, 'pycsw:ResponsiblePartyRole', md.contact[0].role)

        if hasattr(md, 'distribution') and hasattr(md.distribution, 'online'):
            for link in md.distribution.online:
                linkstr = '%s,%s,%s,%s' % \
                (link.name, link.description, link.protocol, link.url)
                links.append(linkstr)

    elif root == 'metadata':  # FGDC
        md = Metadata(exml)

        if md.idinfo.datasetid is not None:  # we need an identifier
            _set(recobj, 'pycsw:Identifier', md.idinfo.datasetid)
        else:  # generate one ourselves
            _set(recobj, 'pycsw:Identifier', uuid.uuid1().get_urn())

        _set(recobj, 'pycsw:Typename', 'fgdc:metadata')
        _set(recobj, 'pycsw:Schema', config.NAMESPACES['fgdc'])
        _set(recobj, 'pycsw:MdSource', 'local')
        _set(recobj, 'pycsw:InsertDate', util.get_today_and_now())
        _set(recobj, 'pycsw:XML', md.xml)
        _set(recobj, 'pycsw:AnyText', util.get_anytext(exml))
        _set(recobj, 'pycsw:Language', 'en-US')
        _set(recobj, 'pycsw:Type',  md.idinfo.citation.citeinfo['geoform'])
        _set(recobj, 'pycsw:Title', md.idinfo.citation.citeinfo['title'])

        if hasattr(md.idinfo, 'descript'):
            _set(recobj, 'pycsw:Abstract', md.idinfo.descript.abstract)

        if hasattr(md.idinfo, 'keywords'):
            if md.idinfo.keywords.theme:
                _set(recobj, 'pycsw:Keywords', \
                ','.join(md.idinfo.keywords.theme[0]['themekey']))

        if hasattr(md.idinfo.timeperd, 'timeinfo'):
            if hasattr(md.idinfo.timeperd.timeinfo, 'rngdates'):
                _set(recobj, 'pycsw:TempExtent_begin',
                     md.idinfo.timeperd.timeinfo.rngdates.begdate)
                _set(recobj, 'pycsw:TempExtent_end',
                     md.idinfo.timeperd.timeinfo.rngdates.enddate)

        if hasattr(md.idinfo, 'origin'):
            _set(recobj, 'pycsw:Creator', md.idinfo.origin)
            _set(recobj, 'pycsw:Publisher',  md.idinfo.origin)
            _set(recobj, 'pycsw:Contributor', md.idinfo.origin)

        if hasattr(md.idinfo, 'ptcontac'):
            _set(recobj, 'pycsw:OrganizationName', md.idinfo.ptcontac.cntorg)
        _set(recobj, 'pycsw:AccessConstraints', md.idinfo.accconst)
        _set(recobj, 'pycsw:OtherConstraints', md.idinfo.useconst)
        _set(recobj, 'pycsw:Date', md.metainfo.metd)
        _set(recobj, 
        'pycsw:PublicationDate', md.idinfo.citation.citeinfo['pubdate'])
        _set(recobj, 'pycsw:Format', md.idinfo.citation.citeinfo['geoform'])

        if hasattr(md.idinfo, 'spdom') and hasattr(md.idinfo.spdom, 'bbox'):
            bbox = md.idinfo.spdom.bbox
        else:
            bbox = None

        if hasattr(md, 'citation'):
            if md.citation.citeinfo['onlink']:
                for link in md.citation.citeinfo['onlink']:
                    tmp = '%s,%s,%s,%s' % \
                    (uri['name'], uri['description'],
                     uri['protocol'], uri['url'])
                    links.append(tmp)

    elif root == '{%s}Record' % config.NAMESPACES['csw']:  # Dublin Core
        md = CswRecord(exml)

        if md.bbox is None:
            bbox = None
        else:
            bbox = md.bbox

	_set(recobj, 'pycsw:Identifier', md.identifier)
	_set(recobj, 'pycsw:Typename', 'csw:Record')
	_set(recobj, 'pycsw:Schema', config.NAMESPACES['csw'])
	_set(recobj, 'pycsw:MdSource', 'local')
	_set(recobj, 'pycsw:InsertDate', util.get_today_and_now())
	_set(recobj, 'pycsw:XML', md.xml)
	_set(recobj, 'pycsw:AnyText', util.get_anytext(exml))
	_set(recobj, 'pycsw:Language', md.language)
	_set(recobj, 'pycsw:Type', md.type)
	_set(recobj, 'pycsw:Title', md.title)
	_set(recobj, 'pycsw:AlternateTitle', md.alternative)
	_set(recobj, 'pycsw:Abstract', md.abstract)
	_set(recobj, 'pycsw:Keywords', ','.join(md.subjects))
	_set(recobj, 'pycsw:ParentIdentifier', md.ispartof)
	_set(recobj, 'pycsw:Relation', md.relation)
	_set(recobj, 'pycsw:TempExtent_begin', md.temporal)
	_set(recobj, 'pycsw:TempExtent_end', md.temporal)
	_set(recobj, 'pycsw:ResourceLanguage', md.language)
	_set(recobj, 'pycsw:Creator', md.creator)
	_set(recobj, 'pycsw:Publisher', md.publisher)
	_set(recobj, 'pycsw:Contributor', md.contributor)
	_set(recobj, 'pycsw:OrganizationName', md.rightsholder)
	_set(recobj, 'pycsw:AccessConstraints', md.accessrights)
	_set(recobj, 'pycsw:OtherConstraints', md.license)
	_set(recobj, 'pycsw:Date', md.date)
	_set(recobj, 'pycsw:CreationDate', md.created)
	_set(recobj, 'pycsw:PublicationDate', md.issued)
	_set(recobj, 'pycsw:Modified', md.modified)
	_set(recobj, 'pycsw:Format', md.format)
	_set(recobj, 'pycsw:Source', md.source)

        for ref in md.references:
            tmp = ',,%s,%s' % (ref['scheme'], ref['url'])
            links.append(tmp)
        for uri in md.uris:
            tmp = '%s,%s,%s,%s' % \
            (uri['name'], uri['description'], uri['protocol'], uri['url'])
            links.append(tmp)

    else:
        raise RuntimeError('Unsupported metadata format')

    if len(links) > 0:
        _set(recobj, 'pycsw:Links', '^'.join(links))

    if bbox is not None:
        try:
            tmp = '%s,%s,%s,%s' % (bbox.minx, bbox.miny, bbox.maxx, bbox.maxy)
            _set(recobj, 'pycsw:BoundingBox', util.bbox2wktpolygon(tmp))
        except:  # coordinates are corrupted, do not include
            _set(recobj, 'pycsw:BoundingBox', None)
    else:
        _set(recobj, 'pycsw:BoundingBox', None)

    return [recobj]

def _set(obj, name, value):
   ''' convenice method to set values'''
   setattr(obj, config.MD_CORE_MODEL['mappings'][name], value)
