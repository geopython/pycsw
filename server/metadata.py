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
        serviceobj.identifier = identifier
        serviceobj.typename = 'gmd:MD_Metadata'
        serviceobj.schema = 'http://www.opengis.net/wms'
        serviceobj.mdsource = record
        serviceobj.insert_date = util.get_today_and_now()
        serviceobj.xml = md.getServiceXML()
        serviceobj.anytext = util.get_anytext(md.getServiceXML())
        #serviceobj.anytext = util.get_anytext(md._capabilities)
        serviceobj.type = 'service'
        serviceobj.title = md.identification.title
        serviceobj.abstract = md.identification.abstract
        serviceobj.keywords = ','.join(md.identification.keywords)
        serviceobj.creator = serviceobj.publisher = serviceobj.contributor = \
        md.provider.contact.name
        serviceobj.organization = md.provider.contact.name
        serviceobj.accessconstraints = md.identification.accessconstraints
        serviceobj.otherconstraints = md.identification.fees
        serviceobj.mdsource = record
        serviceobj.format = md.identification.type
        for c in md.contents:
            if md.contents[c].parent is None:
                bbox = md.contents[c].boundingBoxWGS84
                tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
                serviceobj.wkt_geometry = util.bbox2wktpolygon(tmp)
                break
        serviceobj.crs = 'urn:ogc:def:crs:EPSG:6.3:4326'
        serviceobj.denominator = 'degrees'
        serviceobj.servicetype = md.identification.type
        serviceobj.servicetypeversion = md.identification.version
        serviceobj.operation = ','.join([d.name for d in md.operations])
        serviceobj.operateson = ','.join(list(md.contents))
        serviceobj.couplingtype = 'tight'

        return serviceobj
        recobjs.append(serviceobj) 
         
        # generate record foreach layer
        for layer in md.contents:
            recobj = repos.dataset()
            recobj.identifier = md.contents[layer].name
            recobj.schema = 'http://www.opengis.net/wms'
            recobj.mdsource = record
            recobj.insert_date = util.get_today_and_now()
            recobj.xml = md.getServiceXML()
            recobj.anytext = util.get_anytext(md._capabilities)
            recobj.type = 'dataset'
            recobj.parentidentifier = identifier
            recobj.title = md.contents[layer].title
            recobj.abstract = md.contents[layer].abstract
            recobj.keywords = ','.join(md.contents[layer].keywords)

            bbox = md.contents[layer].boundingBoxWGS84
            if bbox is not None:
                tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
                recobj.wkt_geometry = util.bbox2wktpolygon(tmp)
                recobj.crs = 'urn:ogc:def:crs:EPSG:6.3:4326'
                recobj.denominator = 'degrees'
            else:
                bbox = md.contents[layer].boundingBox
                if bbox:
                    tmp = '%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
                    recobj.wkt_geometry = util.bbox2wktpolygon(tmp)
                    recobj.crs = 'urn:ogc:def:crs:EPSG:6.3:%s' % \
                    bbox[-1].split(':')[1]

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

        recobj.identifier = md.identifier
        recobj.typename = 'gmd:MD_Metadata'
        recobj.schema = config.NAMESPACES['gmd']
        recobj.mdsource = 'local'
        recobj.insert_date = util.get_today_and_now()
        recobj.xml = md.xml
        recobj.anytext = util.get_anytext(exml)
        recobj.language = md.language
        recobj.type = md.hierarchy
        recobj.parentidentifier = md.parentidentifier
        recobj.date = md.datestamp
        recobj.source = md.dataseturi
        recobj.crs = 'urn:ogc:def:crs:EPSG::%s' % md.referencesystem

        if hasattr(md, 'identification'):
            recobj.title = md.identification.title
            recobj.title_alternate = md.identification.alternatetitle
            recobj.abstract = md.identification.abstract
            recobj.relation = md.identification.aggregationinfo
            recobj.time_begin = md.identification.temporalextent_start
            recobj.time_end = md.identification.temporalextent_end

            if len(md.identification.topiccategory) > 0:
                recobj.topicategory = md.identification.topiccategory[0]

            if len(md.identification.resourcelanguage) > 0:
                recobj.resourcelanguage = md.identification.resourcelanguage[0]
 
            if hasattr(md.identification, 'bbox'):
                bbox = md.identification.bbox
            else:
                bbox = None

            if (hasattr(md.identification, 'keywords') and
            len(md.identification.keywords) > 0):
                recobj.keywords = ','.join(
                md.identification.keywords[0]['keywords'])
                recobj.keywordstype = md.identification.keywords[0]['type']

            if hasattr(md.identification, 'creator'):
                recobj.creator = md.identification.creator
            if hasattr(md.identification, 'publisher'):
                recobj.publisher = md.identification.publisher
            if hasattr(md.identification, 'contributor'):
                recobj.contributor = md.identification.contributor

            if (hasattr(md.identification, 'contact') and 
            hasattr(md.identification.contact, 'organization')):
                recobj.organization = md.identification.contact.organization

            if len(md.identification.securityconstraints) > 0:
                recobj.securityconstraints = \
                md.identification.securityconstraints[0]
            if len(md.identification.accessconstraints) > 0:
                recobj.accessconstraints = \
                md.identification.accessconstraints[0]
            if len(md.identification.otherconstraints) > 0:
                recobj.otherconstraints = md.identification.otherconstraints[0]

            if hasattr(md.identification, 'date'):
                for datenode in md.identification.date:
                    if datenode.type == 'revision':
                        recobj.date_revision = datenode.date
                    elif datenode.type == 'creation':
                        recobj.date_creation = datenode.date
                    elif datenode.type == 'publication':
                        recobj.date_publication = datenode.date

            recobj.geodescode = md.identification.bbox.description_code

            if len(md.identification.denominators) > 0:
                recobj.denominator = md.identification.denominators[0]
            if len(md.identification.distance) > 0:
                recobj.distancevalue = md.identification.distance[0]
            if len(md.identification.uom) > 0:
                recobj.distanceuom = md.identification.uom[0]

            if len(md.identification.classification) > 0:
                recobj.classification = md.identification.classification[0]
            if len(md.identification.uselimitation) > 0:
                recobj.conditionapplyingtoaccessanduse = \
                md.identification.uselimitation[0]

        if hasattr(md.identification, 'format'):
            recobj.format = md.distribution.format

        if md.serviceidentification is not None:
            recobj.servicetype = md.serviceidentification.type
            recobj.servicetypeversion = md.serviceidentification.version

            recobj.couplingtype = md.serviceidentification.couplingtype
       
            #if len(md.serviceidentification.operateson) > 0: 
            #    recobj.operateson = VARCHAR(32), 
            #recobj.operation VARCHAR(32), 
            #recobj.operatesonidentifier VARCHAR(32), 
            #recobj.operatesoname VARCHAR(32), 


        if hasattr(md.identification, 'dataquality'):     
            recobj.degree = md.dataquality.conformancedegree
            recobj.lineage = md.dataquality.lineage
            recobj.specificationtitle = md.dataquality.specificationtitle
            if hasattr(md.dataquality, 'specificationdate'):
                recobj.specificationdate = \
                md.dataquality.specificationdate[0].date
                recobj.specificationdatetype = \
                md.dataquality.specificationdate[0].datetype

        if hasattr(md, 'contact') and len(md.contact) > 0:
            recobj.responsiblepartyrole = md.contact[0].role

        if hasattr(md, 'distribution') and hasattr(md.distribution, 'online'):
            for link in md.distribution.online:
                linkstr = '%s,%s,%s,%s' % \
                (link.name, link.description, link.protocol, link.url)
                links.append(linkstr)

    elif root == 'metadata':  # FGDC
        pass

        md = Metadata(exml)

        if md.idinfo.datasetid is not None:  # we need an indentifier
            recobj.identifier = md.idinfo.datasetid
        else:  # generate one ourselves
            recobj.identifier = uuid.uuid1().get_urn()

        recobj.typename = 'fgdc:metadata'
        recobj.schema = config.NAMESPACES['fgdc']
        recobj.mdsource = 'local'
        recobj.insert_date = util.get_today_and_now()
        recobj.xml = md.xml
        recobj.anytext = util.get_anytext(exml)
        recobj.language = 'en-US'
        recobj.type = md.idinfo.citation.citeinfo['geoform']
        recobj.title = md.idinfo.citation.citeinfo['title']
        recobj.abstract = md.idinfo.descript.abstract
        recobj.keywords = ','.join(md.idinfo.keywords.theme[0]['themekey'])

        if hasattr(md.idinfo.timeperd, 'timeinfo'):
            recobj.time_begin = md.idinfo.timeperd.timeinfo.rngdates.begdate
            recobj.time_end = md.idinfo.timeperd.timeinfo.rngdates.enddate

        if hasattr(md.idinfo, 'origin'):
            recobj.creator = md.idinfo.origin
            recobj.publisher = md.idinfo.origin
            recobj.contributor = md.idinfo.origin

        recobj.organization = md.idinfo.ptcontac.cntorg
        recobj.accessconstraints = md.idinfo.accconst
        recobj.otherconstraints = md.idinfo.useconst
        recobj.date = md.metainfo.metd
        recobj.date_publication = md.idinfo.citation.citeinfo['pubdate']
        recobj.format = md.idinfo.citation.citeinfo['geoform']

        if md.idinfo.spdom.bbox is None:
            bbox = None
        else:
            bbox = md.idinfo.spdom.bbox

        if md.citation.citeinfo['onlink']:
            for link in md.citation.citeinfo['onlink']:
                tmp = '%s,%s,%s,%s' % \
                (uri['name'], uri['description'], uri['protocol'], uri['url'])
                links.append(tmp)

    else:  # default
        md = CswRecord(exml)

        if md.bbox is None:
            bbox = None
        else:
            bbox = md.bbox

	recobj.identifier = md.identifier
	recobj.typename = 'csw:Record'
	recobj.schema = config.NAMESPACES['csw']
	recobj.mdsource = 'local'
	recobj.insert_date = util.get_today_and_now()
	recobj.xml = md.xml
	recobj.anytext = util.get_anytext(exml)
	recobj.language = md.language
	recobj.type = md.type
	recobj.title = md.title
	recobj.title_alternate = md.alternative
	recobj.abstract = md.abstract
	recobj.keywords = ','.join(md.subjects)
	recobj.parentidentifier = md.ispartof
	recobj.relation = md.relation
	recobj.time_begin = md.temporal
	recobj.time_end = md.temporal
	recobj.resourcelanguage = md.language
	recobj.creator = md.creator
	recobj.publisher = md.publisher
	recobj.contributor = md.contributor
	recobj.organization = md.rightsholder
	recobj.accessconstraints = md.accessrights
	recobj.otherconstraints = md.license
	recobj.date = md.date
	recobj.date_creation = md.created
	recobj.date_publication = md.issued
	recobj.date_modified = md.modified
	recobj.format = md.format
	recobj.source = md.source

        for ref in md.references:
            tmp = ',,%s,%s' % (ref['scheme'], ref['url'])
            links.append(tmp)
        for uri in md.uris:
            tmp = '%s,%s,%s,%s' % \
            (uri['name'], uri['description'], uri['protocol'], uri['url'])
            links.append(tmp)

    if len(links) > 0:
        recobj.links = '^'.join(links)

    if bbox is not None:
        tmp = '%s,%s,%s,%s' % (bbox.minx, bbox.miny, bbox.maxx, bbox.maxy)
        recobj.wkt_geometry = util.bbox2wktpolygon(tmp)
    else:
        recobj.wkt_geometry = None

    return recobj
