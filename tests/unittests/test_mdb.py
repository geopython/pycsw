# =================================================================
#
# Author: Vincent Fazio <vincent.fazio@csiro.au>
#
# Copyright (c) 2024 CSIRO Australia
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
""" Unit tests for pycsw.core.mdb
This tests its ability to parse ISO19115-3 XML
"""

from pathlib import Path
import pytest

from owslib.etree import etree

from pycsw.core.mdb import MD_Metadata

pytestmark = pytest.mark.unit

@pytest.fixture
def bmd():
    """ Create an MD_Metadata instance from Belgian ISO 19115-3 XML sample
    """
    BELGIAN_SAMPLE = str(Path(__file__).parent.parent / "functionaltests" / "suites" / "mdb" / "data" / "SAMPLE_ISO1915-3.xml")
    with open(BELGIAN_SAMPLE, "r") as fd:
        xml_list = fd.readlines()
        xml_str = ''.join(xml_list)
        xml_bytes = bytes(xml_str, encoding='utf-8')
        exml = etree.fromstring(xml_bytes)
        assert exml is not None
        return MD_Metadata(exml)
    return None

def test_metadata(bmd):
    """ Tests MD_Metadata class
    """
    assert bmd is not None
    assert(bmd.charset == 'utf8')
    assert(bmd.hierarchy == 'series')
    assert(bmd.identifier == '74f81503-8d39-4ec8-a49a-c76e0cd74946')
    assert(bmd.languagecode == 'fre')
    assert(bmd.locales[0].charset == 'utf8')
    assert(bmd.locales[0].id == 'FR')
    assert(bmd.locales[0].languagecode == 'fre')
    assert(bmd.referencesystem.code == 'EPSG:31370')
    assert(bmd.stdname == 'ISO 19115')
    assert(bmd.stdver == '2003/Cor 1:2006')
    assert(bytes(bmd.contentinfo[0].featurecatalogues[0], 'utf-8') == b'Mod\xc3\xa8le de donn\xc3\xa9es')
    assert(bmd.dataseturi == 'PROTECT_CAPT')
    assert(bmd.datestamp == '2023-08-08T07:34:11.366Z')
    assert(bmd.datestamp == '2023-08-08T07:34:11.366Z')

def test_responsibility(bmd):
    """ Tests CI_Responsibility class as 'pointOfContact'
    """
    ct0 = bmd.contact[0]
    assert(ct0.email == 'veronique.willame@spw.wallonie.be')
    assert(bytes(ct0.name, 'utf-8') == b'V\xc3\xa9ronique Willame')
    assert(bytes(ct0.organization, 'utf-8') == b"Direction des Eaux souterraines (SPW - Agriculture, Ressources naturelles et Environnement - D\xc3\xa9partement de l'Environnement et de l'Eau - Direction des Eaux souterraines)")
    assert(ct0.phone == '+32 (0)81/335923')
    assert(ct0.role == 'pointOfContact')

def test_distributor(bmd):
    """ Tests MD_Distributor class
    """
    distor = bmd.distribution.distributor[0]
    assert(distor.contact.email == 'helpdesk.carto@spw.wallonie.be')
    assert(distor.contact.organization == 'Service public de Wallonie (SPW)')
    assert(distor.contact.role == 'distributor')

def test_online_distribution(bmd):
    """ Tests MD_Distribution class
    """
    online = bmd.distribution.online[0]
    assert(online.description[:65] == 'Application cartographique du Geoportail (WalOnMap) qui permet de')
    assert(online.function == 'information')
    assert(bytes(online.name, 'utf=8') == b'Application WalOnMap - Toute la Wallonie \xc3\xa0 la carte')
    assert(online.protocol == 'WWW:LINK')
    assert(online.url == 'https://geoportail.wallonie.be/walonmap/#ADU=https://geoservices.wallonie.be/arcgis/rest/services/EAU/PROTECT_CAPT/MapServer')
    assert(len(bmd.distribution.online) == 5)
    assert(bmd.distribution.version == '-')

def test_identification(bmd):
    """ Tests MD_DataIdentification class
    """
    ident = bmd.identification[0]
    assert(bytes(ident.abstract[:62], 'utf-8') == b'Cette collection de donn\xc3\xa9es comprend les zones de surveillance')
    assert(ident.accessconstraints[0] == 'license')
    assert(ident.alternatetitle == 'PROTECT_CAPT')
    assert(ident.graphicoverview[0] == 'https://metawal.wallonie.be/geonetwork/srv/api/records/74f81503-8d39-4ec8-a49a-c76e0cd74946/attachments/PROTECT_CAPT.png')
    assert(ident.graphicoverview[1] == 'https://metawal.wallonie.be/geonetwork/srv/api/records/74f81503-8d39-4ec8-a49a-c76e0cd74946/attachments/PROTECT_CAPT_s.png')
    assert(ident.identtype =='dataset')
    assert(bytes(ident.otherconstraints[0], 'utf-8') == b"Les conditions g\xc3\xa9n\xc3\xa9rales d'acc\xc3\xa8s s\xe2\x80\x99appliquent.")
    assert(len(ident.otherconstraints) == 2)
    assert(ident.spatialrepresentationtype[0] == 'vector')
    assert(bytes(ident.title, 'utf-8') == b'Protection des captages - S\xc3\xa9rie')
    assert(ident.topiccategory == ['geoscientificInformation', 'inlandWaters'])
    assert(ident.uricode == ['PROTECT_CAPT', '74f81503-8d39-4ec8-a49a-c76e0cd74946'])
    assert(ident.uricodespace == ['BE.SPW.INFRASIG.GINET', 'http://geodata.wallonie.be/id/'])
    assert(ident.useconstraints[0] == 'license')

def test_identification_contact(bmd):
    """ Tests CI_Responsibility class in indentification section
    """
    contact = bmd.identification[0].contact

    assert(contact[0].email == 'helpdesk.carto@spw.wallonie.be')
    assert(contact[0].organization[:21] == 'Helpdesk carto du SPW')
    assert(contact[0].role == 'pointOfContact')

    assert(bytes(contact[1].name, 'utf-8') == b'V\xc3\xa9ronique Willame')
    assert(contact[1].organization[:31] == 'Direction des Eaux souterraines')
    assert(contact[1].phone == '+32 (0)81/335923')
    assert(contact[1].role == 'custodian')

    assert(bytes(contact[2].onlineresource.description, 'utf-8') == b'G\xc3\xa9oportail de la Wallonie')
    assert(contact[2].onlineresource.function == 'information')
    assert(bytes(contact[2].onlineresource.name, 'utf-8') == b'G\xc3\xa9oportail de la Wallonie')
    assert(contact[2].onlineresource.protocol == 'WWW:LINK')
    assert(contact[2].onlineresource.url == 'https://geoportail.wallonie.be')
    assert(contact[2].organization == 'Service public de Wallonie (SPW)')
    assert(contact[2].role == 'owner')

def test_identification_date(bmd):
    """ Tests CI_Date class
    """
    date = bmd.identification[0].date
    assert(date[0].date == '2000-01-01')
    assert(date[0].type == 'creation')
    assert(date[1].date == '2023-07-31')
    assert(date[1].type == 'revision')
    assert(date[2].date == '2022-11-08')
    assert(date[2].type == 'publication')

def test_identification_extent(bmd):
    """ Tests EX_GeographicBoundingBox class
    """
    ident = bmd.identification[0]
    assert(ident.denominators[0] == '10000')

    assert(ident.extent.boundingBox.maxx == '6.50')
    assert(ident.extent.boundingBox.maxy == '50.85')
    assert(ident.extent.boundingBox.minx == '2.75')
    assert(ident.extent.boundingBox.miny == '49.45')

    assert(ident.bbox.maxx == '6.50')
    assert(ident.bbox.maxy == '50.85')
    assert(ident.bbox.minx == '2.75')
    assert(ident.bbox.miny == '49.45')

def test_identification_keywords(bmd):
    """ Tests Keywords class
    """
    keyw = bmd.identification[0].keywords
    assert(keyw[0].keywords[0].name == 'Sol et sous-sol')
    assert(keyw[0].keywords[0].url == 'https://metawal.wallonie.be/thesaurus/theme-geoportail-wallon#SubThemesGeoportailWallon/1030')
    assert(keyw[0].type == 'theme')
    assert(len(keyw[0].keywords) == 2)
    assert(len(keyw) == 5)


@pytest.fixture
def amd():
    AUST_SAMPLE = str(Path(__file__).parent.parent / "functionaltests" / "suites" / "mdb" / "data" / "auscope-iso19115-3.xml")
    with open(AUST_SAMPLE, "r") as fd:
        xml_list = fd.readlines()
        xml_str = ''.join(xml_list)
        xml_bytes = bytes(xml_str, encoding='utf-8')
        exml = etree.fromstring(xml_bytes)
        assert exml is not None
        return MD_Metadata(exml)
    return None

def test_aust(amd):
    """ Tests elements that are mostly not present in Belgian sample
    """
    assert(amd is not None)
    ident = amd.identification[0]
    assert(ident.extent.vertExtMax == '300')
    assert(ident.extent.vertExtMin == '-400')
    assert(ident.securityconstraints[0] == 'unclassified')
    assert(ident.funder[0].organization == 'AuScope')
    assert(ident.uricode[0] == 'https://geology.data.vic.gov.au/searchAssistant/document.php?q=parent_id:107513')