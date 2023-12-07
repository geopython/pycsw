# -*- coding: utf-8 -*-
# =================================================================
#
# - pycsw DataCite output plugin -
#
# Authors: Carl-Fredrik Enell <carl-fredrik.enell@eiscat.se>, Paul van Genuchten <genuchten@yahoo.com>
# Based on pycsw plugins by  Tom Kralidis <tomkralidis@gmail.com>
# DataCite schema follows:
# https://github.com/inveniosoftware/datacite/blob/master/datacite/schema42.py
# https://schema.datacite.org/meta/kernel-4.3/example/datacite-example-full-v4.xml
#
# This module intends to follow DataCite 4.3
#
# PyCSW  Copyright (C) 2015 Tom Kralidis
# Schema Copyright (C) 2016 CERN
# Schema Copyright (C) 2019 Caltech
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
from os.path import basename
from datetime import datetime
import json
import logging

"""
datacite.py
Output plugin for DataCite 4.3 schema output
Defines function write_record
Input:  result, esn, context, url  (pycsw query results)
Output: XML etree according to DataCite schema
"""

NAMESPACE = 'http://datacite.org/schema/kernel-4'
NAMESPACES = {'xml': 'http://www.w3.org/XML/1998/namespace', 
              'datacite': NAMESPACE, 
              'oai': 'http://www.openarchives.org/OAI/2.0/'}
LOGGER = logging.getLogger(__name__)

XPATH_MAPPINGS = {
     'pycsw:Identifier': 'identifier',
     'pycsw:Date': 'dates/date',
     'pycsw:Creator': 'creators/creator',
     'pycsw:Title': 'titles/title',
     'pycsw:Abstract': 'descriptions/description',
     'pycsw:Publisher': 'publisher',
     'pycsw:BoundingBox': 'geoLocations/geoLocation/geoLocationBox',
     'pycsw:Format': 'formats/format',
     'pycsw:Language': 'Language',
     'pycsw:Edition': 'version',
     'pycsw:PublicationDate': 'dates/date',
     'pycsw:Keywords': 'subjects/subject',
     'pycsw:TopicCategory': 'subjects/subject',
     'pycsw:Themes': 'subjects/subject',
     'pycsw:Lineage': 'lineage',
     'pycsw:TempExtent_begin': '',
     'pycsw:TempExtent_end': '',
     'pycsw:Contributor': '',
     'pycsw:AccessConstraints': '',
     'pycsw:Contacts': '',
     'pycsw:Links': ''
}


def write_record(result, esn, context, url=None):
    """
    Main function
    Return csw:SearchResults child as lxml.etree.Element
    """
    typename = util.getqattr(result, context.md_core_model['mappings']['pycsw:Typename'])
    # Check if we already have DataCite formatted metadata
    if esn == 'full' and typename == 'datacite':
        # dump record as is and exit
        return etree.fromstring(util.getqattr(result, context.md_core_model['mappings']['pycsw:XML']), context.parser)
    
    # Otherwise build XML tree from available metadata
    node = etree.Element(util.nspath_eval('resource', NAMESPACES))
    node.attrib[util.nspath_eval('xsi:schemaLocation', context.namespaces)] = \
        '%s http://schema.datacite.org/meta/kernel-4.3/metadata.xsd' % NAMESPACE
    # Type
    type = etree.SubElement(node, util.nspath_eval('resourceType', NAMESPACES))
    resTypeGeneral = basename(util.getqattr(result, context.md_core_model['mappings']['pycsw:Type']))
    type.text = resTypeGeneral

    if resTypeGeneral.lower() in ["dataset","nongeographicdataset","featuretype","transferaggregate","otheraggregate"]:
        resTypeGeneral = "Dataset"
    elif resTypeGeneral.lower() in ["software"]:
        resTypeGeneral = "Software"
    elif resTypeGeneral.lower() in ["collectionSession","fieldSession"]:
        resTypeGeneral = "Event"
    elif resTypeGeneral.lower() in ["service"]:
        resTypeGeneral = "Service"
    elif resTypeGeneral.lower() in ["model"]:
        resTypeGeneral = "Model"
    elif resTypeGeneral.lower() in ["series"]:
        resTypeGeneral = "Collection"
    elif resTypeGeneral.lower() in ["text","document","article"]:
        resTypeGeneral = "Text"
    elif resTypeGeneral.lower() in ["image"]:
        resTypeGeneral = "Image"
    else:
        resTypeGeneral = "Other"

    assert resTypeGeneral in  [
        "Audiovisual",
        "Book",
        "BookChapter",
        "Collection",
        "ComputationalNotebook",
        "ConferencePaper",
        "ConferenceProceeding",
        "DataPaper",
        "Dataset",
        "Dissertation",
        "Event",
        "Image",
        "InteractiveResource",
        "Journal",
        "JournalArticle",
        "Model",
        "OutputManagementPlan",
        "PeerReview",
        "PhysicalObject",
        "Preprint",
        "Report",
        "Service",
        "Software",
        "Sound",
        "Standard",
        "Text",
        "Workflow",
        "Other"
      ]
    type.attrib[util.nspath_eval('resourceTypeGeneral', NAMESPACES)] = resTypeGeneral
    
    # Identifier
    ident = etree.SubElement(node, util.nspath_eval('identifier', NAMESPACES))
    ival = util.getqattr(result, context.md_core_model['mappings']['pycsw:Identifier'])
    ident.text = ival
    #Identifier type:
    # NB DOI is mandatory for DataCite proper but we plan to use the schema with other IDs too. Modify as necessary.
    if ival.lower().startswith("doi"):
        idType = "DOI"
    elif ival.lower().startswith("handle"):
        idType = "Handle"
    elif ival.lower().startswith("urn"):
        idType = "URN"
    else:
        idType = "URL"
    ident.attrib[util.nspath_eval('identifierType', NAMESPACES)] = idType or "DOI"
    
    # modified
    mod = util.getqattr(result, context.md_core_model['mappings']['pycsw:Date'])
    if mod not in [None, '']:
        dates = etree.SubElement(node, util.nspath_eval('dates', NAMESPACES))
        date = etree.SubElement(dates, util.nspath_eval('date', NAMESPACES))
        date.attrib['dateType'] = 'Updated'
        date.text = mod

    # Title
    titles = etree.SubElement(node, util.nspath_eval('titles', NAMESPACES))
    tval = util.getqattr(result, context.md_core_model['mappings']['pycsw:Title'])
    title = etree.SubElement(titles, util.nspath_eval('title', NAMESPACES))
    title.attrib[util.nspath_eval("xml:lang", NAMESPACES)]= util.getqattr(result, context.md_core_model['mappings']['pycsw:Language']) or "eng"
    title.text = tval

    # keywords
    # <subjects><subject xml:lang="eng">example</subject></subjects>
    kwval = util.getqattr(result, context.md_core_model['mappings']['pycsw:Keywords'])
    tcval = util.getqattr(result, context.md_core_model['mappings']['pycsw:TopicCategory'])
    kws = etree.SubElement(node, util.nspath_eval('subjects', NAMESPACES))
    if kwval not in [None, '']:
        # todo: subject per kw
        kw = etree.SubElement(kws, util.nspath_eval('subject', NAMESPACES))
        kw.attrib[util.nspath_eval("xml:lang", NAMESPACES)]= util.getqattr(result, context.md_core_model['mappings']['pycsw:Language']) or "eng"
        kw.text = kwval
    if tcval not in  [None, '']:
        kw = etree.SubElement(kws, util.nspath_eval('subject', NAMESPACES))
        kw.attrib['schemaUri'] = 'https://schemas.opengis.net/iso/19139/20070417/resources/codelist/gmxCodelists.xml#MD_TopicCategoryCode' 
        kw.text = tcval   
    # themes
    # <subjects><subject schemeURI="https://example.com" xml:lang="eng">example</subject></subjects>
    themes = util.getqattr(result, context.md_core_model['mappings']['pycsw:Themes'])
    if themes not in [None, '']:
        try:
            for t in json.loads(themes):
                thesaurus = t.get('thesaurus',{}).get('url', t.get('thesaurus',{}).get('title', ''))
                for k in [c for c in t.get('keywords', []) if c['name'] not in [None, '']]:
                    kw = etree.SubElement(kws, util.nspath_eval('subject', NAMESPACES))
                    kw.attrib['schemaUri'] = thesaurus 
                    kw.text = k.get('name') 
        except Exception as err:
            LOGGER.exception(f"failed to parse themes json of {themes}: {err}")

    # publisher, creator, contributor, should have at least 1 creator (use originator else organization else ...)
    cval = util.getqattr(result, context.md_core_model['mappings']['pycsw:Contacts'])
    hasCreator = False # requires at least 1 creator
    creas = etree.SubElement(node, util.nspath_eval('creators', NAMESPACES)) 
    hasPublisher = False # 1 publisher at most
    if cval not in [None, '', 'null']:
        conts = etree.SubElement(node, util.nspath_eval('contributors', NAMESPACES))
        try:
            for cnt in json.loads(cval):
                try:
                    cont = etree.SubElement(conts, util.nspath_eval('contributor', NAMESPACES))
                    roleMapping = {
                        "resourceProvider": "Distributor",
                        "custodian": "DataCurator",
                        "owner": "RightsHolder",
                        "user": "Other",
                        "distributor": "Distributor",
                        "originator": "Producer",
                        "pointOfContact": "ContactPerson",
                        "principalInvestigator": "Supervisor",
                        "processor": "Other",
                        "publisher": "Distributor",
                        "author": "Researcher"
                    }                    

                    contnm = etree.SubElement(cont, util.nspath_eval('contributorName', NAMESPACES))
                    contnm.text = cnt.get('individualname',cnt.get('organization', ''))
                    cont.attrib['contributorType'] = roleMapping.get(cnt.get('role', ''),'Other')
                    if cont.get('url').startswith('http'):
                        contid = etree.SubElement(cont, util.nspath_eval('nameIdentifier', NAMESPACES))
                        contid.attrib['nameIdentifierScheme'] = "URL"
                        contid.text = cont['url']
                    if cont['organization']:
                        contaf = etree.SubElement(cont, util.nspath_eval('affiliation', NAMESPACES))
                        contaf.text = cont['organization']

                    if not hasPublisher and cnt.get('role', '').lower() in ['publisher','resourceProvider','distributor']:
                        hasPublisher = True
                        pb = etree.SubElement(node, util.nspath_eval('publisher', NAMESPACES))
                        pb.text = cnt.get('individualname',cnt.get('organization', ''))
                    elif cnt.get('role', '').lower() in ['originator','author','principalInvestigator']:
                        hasCreator = True
                        crea = etree.SubElement(creas, util.nspath_eval('creator', NAMESPACES))
                        creanm = etree.SubElement(crea, util.nspath_eval('creatorName', NAMESPACES))
                        creanm.text = cnt.get('individualname',cnt.get('organization', ''))
                        if cnt['url'] not in [None, '']:
                            creaid = etree.SubElement(crea, util.nspath_eval('nameIdentifier', NAMESPACES))
                            creaid.attrib['nameIdentifierScheme'] = "URL"
                            creaid.text = cnt['url']
                        if cnt['organization'] not in [None, '']:
                            creaff = etree.SubElement(crea, util.nspath_eval('affiliation', NAMESPACES))
                            creaff.text = cnt['organization']

                except Exception as err:
                    LOGGER.exception(f"failed to parse contact of {cnt}: {err}")
        except Exception as err:
            LOGGER.exception(f"failed to parse contacts json of {cval}: {err}")
    if not hasCreator:
        crea = etree.SubElement(creas, util.nspath_eval('creator', NAMESPACES))
        creanm = etree.SubElement(crea, util.nspath_eval('creatorName', NAMESPACES))
        cval = util.getqattr(result, context.md_core_model['mappings']['pycsw:OrganizationName'])
        creanm.text = cval

# <descriptions><description xml:lang="eng">foo</description></descriptions>
    descriptions = etree.SubElement(node, util.nspath_eval('descriptions', NAMESPACES))
    tval = util.getqattr(result, context.md_core_model['mappings']['pycsw:Abstract'])
    description = etree.SubElement(descriptions, util.nspath_eval('description', NAMESPACES))
    description.attrib[util.nspath_eval("xml:lang", NAMESPACES)]= util.getqattr(result, context.md_core_model['mappings']['pycsw:Language']) or "eng"
    description.text = tval

# https://guidelines.openaire.eu/en/latest/data/field_language.html
# <language>eng</language>
    tval = util.getqattr(result, context.md_core_model['mappings']['pycsw:Language'])
    if tval not in [None, '']:
        format = etree.SubElement(node, util.nspath_eval('Language', NAMESPACES))
        format.text = tval

# https://guidelines.openaire.eu/en/latest/data/field_version.html?highlight=version
# <version>1.0</version>
    tval = util.getqattr(result, context.md_core_model['mappings']['pycsw:Edition'])
    if tval not in [None, '']:
        format = etree.SubElement(node, util.nspath_eval('version', NAMESPACES))
        format.text = tval

# https://guidelines.openaire.eu/en/latest/data/field_format.html
# <formats> <format>PDF</format> </formats>
    tval = util.getqattr(result, context.md_core_model['mappings']['pycsw:Format'])
    if tval not in [None, '']:
        formats = etree.SubElement(node, util.nspath_eval('formats', NAMESPACES))
        format = etree.SubElement(formats, util.nspath_eval('format', NAMESPACES))
        format.text = tval

# <rightsList><rights rightsURI="https://example.com">example</rights></rightsList>
    rights = etree.SubElement(node, util.nspath_eval('rightsList', NAMESPACES))
    for r in ["AccessConstraints","OtherConstraints","Classification","ConditionApplyingToAccessAndUse"]:
        rval = util.getqattr(result, context.md_core_model['mappings']['pycsw:'+r])
        if rval not in [None, '']:
            right = etree.SubElement(rights, util.nspath_eval('rights', NAMESPACES))
            if rval.startswith('http'):
                right.attrib['rightsURI'] = rval
            right.text = r+':'+rval

# <sizes><size></size></sizes>

# "IsCitedBy","Cites","IsSupplementTo","IsSupplementedBy","IsContinuedBy","Continues","IsNewVersionOf","IsPreviousVersionOf","IsPartOf","HasPart","IsPublishedIn","IsReferencedBy","References","IsDocumentedBy","Documents","IsCompiledBy","Compiles","IsVariantFormOf","IsOriginalFormOf","IsIdenticalTo","HasMetadata","IsMetadataFor","Reviews","IsReviewedBy","IsDerivedFrom","IsSourceOf","Describes","IsDescribedBy","HasVersion","IsVersionOf","Requires","IsRequiredBy","Obsoletes","IsObsoletedBy"
# <relatedIdentifiers><relatedIdentifier relatedIdentifierType="URN" relationType="">doi:1234</relatedIdentifier></relatedIdentifiers>
# alternateIdentifiers/alternateIdentifier/@alternateIdentifierType

# Since Datacite is a metadata format related to the DOI to access a piece of content, the schema does not include a link to the actual file
# although internally Datacite uses a property `contentUrl`, suggestion to add links to content in the same way
    rval = util.getqattr(result, context.md_core_model['mappings']['pycsw:Links'])
    if rval not in [None, '', 'null']:
        try:
            for lnk in util.jsonify_links(rval):
                try:
                    if lnk.get('url', '').startswith('http'):
                        ct = etree.SubElement(node, util.nspath_eval('contentUrl', NAMESPACES))
                        ct.text = lnk.get('url')
                except Exception as err:
                    LOGGER.exception(f"failed to parse link of {rval}: {err}")
        except Exception as err:
            LOGGER.exception(f"failed to parse links json of {lnk}: {err}")

# <geoLocations><geoLocation><geoLocationBox><westBoundLongitude>41.090</...
    bbox = util.getqattr(result, context.md_core_model['mappings']['pycsw:BoundingBox'])
    if bbox not in [None, '']:
        try:
            bbox2 = util.wkt2geom(bbox)
        except:
            return None
        bounds = etree.SubElement(node, util.nspath_eval('geoLocations', NAMESPACES))
        bound = etree.SubElement(bounds, util.nspath_eval('geoLocation', NAMESPACES))
        box = etree.SubElement(bound, util.nspath_eval('geoLocationBox', NAMESPACES)) 
        wb = etree.SubElement(box, util.nspath_eval('westBoundLongitude', NAMESPACES))
        wb.text = str(bbox2[0])
        sb = etree.SubElement(box, util.nspath_eval('southBoundLatitude', NAMESPACES)) 
        sb.text = str(bbox2[1])
        eb = etree.SubElement(box, util.nspath_eval('eastBoundLongitude', NAMESPACES)) 
        eb.text = str(bbox2[2])
        nb = etree.SubElement(box, util.nspath_eval('northBoundLatitude', NAMESPACES))  
        nb.text = str(bbox2[3])

# Subtitle
    sval = util.getqattr(result, context.md_core_model['mappings']['pycsw:AlternateTitle'])
    if sval:
        subtitle = etree.SubElement(titles, util.nspath_eval('title', NAMESPACES))
        subtitle.attrib["titleType"] = "Subtitle"
        subtitle.text = sval

# PublicationYear
    dval = util.getqattr(result, context.md_core_model['mappings']['pycsw:PublicationDate'])
    if dval in [None, '']:
        dval = util.getqattr(result, context.md_core_model['mappings']['pycsw:Date']) 
        if dval not in [None, '']:
            dt = datetime.fromisoformat(dval)
            dt = dt.strftime("%Y")
            etree.SubElement(node, util.nspath_eval('publicationYear', NAMESPACES)).text = dt

    return node
