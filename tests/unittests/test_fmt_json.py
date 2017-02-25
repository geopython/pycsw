# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
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
"""Unit tests for pycsw.core.formats.fmt_json"""

import pytest

from pycsw.core.formats import fmt_json

pytestmark = pytest.mark.unit


def test_xml2dict():
    identifier = "ac522ef2-89a6-11db-91b1-7eea55d89593"
    xml = """
        <?xml version="1.0" encoding="UTF-8"?>
        <GetRecordsResponse
           xmlns="http://www.opengis.net/cat/csw/3.0"
           xmlns:csw="http://www.opengis.net/cat/csw/3.0"
           xmlns:ows="http://www.opengis.net/ows/2.0"
           xmlns:xsi="http://www.w3.org/2001/xmlschema-instance"
           xsi:schemalocation="http://www.opengis.net/cat/csw/3.0
                               http://schemas.opengis.net/cat/csw/3.0/cswall.xsd">
           <RequestId>http://www.altova.com</RequestId>
           <SearchStatus timestamp="2009-12-17T09:30:47-05:00"/>
           <SearchResults resultSetId="someId" elementSet="summary"
              recordSchema="http://www.opengis.net/cat/csw/3.0"
              numberOfRecordsMatched="1" numberOfRecordsReturned="1" nextRecord="1">
              <csw:Record xmlns:dc="http://purl.org/dc/elements/1.1/"
                 xmlns:dct="http://purl.org/dc/terms/"
                 xmlns:ows="http://www.opengis.net/ows/2.0">
                 <dc:creator>U.S. Geological Survey</dc:creator>
                 <dc:contributor>State of Texas</dc:contributor>
                 <dc:publisher>U.S. Geological Survey</dc:publisher>
                 <dc:subject>Elevation, Hypsography, and Contours</dc:subject>
                 <dc:subject>elevation</dc:subject>
                 <dct:abstract>Elevation data.</dct:abstract>
                 <dc:identifier>{identifier}</dc:identifier>
                 <dc:relation>OfferedBy</dc:relation>
                 <dc:source>dd1b2ce7-0722-4642-8cd4-6f885f132777</dc:source>
                 <dc:rights>Copyright © 2004, State of Texas</dc:rights>
                 <dc:type>Service</dc:type>
                 <dc:title>National Elevation Mapping Service for Texas</dc:title>
                 <dct:modified>2004-03-01</dct:modified>
                 <dc:language>en</dc:language>
                 <ows:BoundingBox>
                    <ows:LowerCorner>-108.44 28.229</ows:LowerCorner>
                    <ows:UpperCorner>-96.223 34.353</ows:UpperCorner>
                 </ows:BoundingBox>
                 <csw:TemporalExtent>
                    <csw:begin>2001-12-01T09:30:47Z</csw:begin>
                    <csw:end>2001-12-17T09:30:47Z</csw:end>
                 </csw:TemporalExtent>
              </csw:Record>
           </SearchResults>
        </GetRecordsResponse>
    """.strip().format(identifier=identifier)
    namespaces = {
        "csw": "http://www.opengis.net/cat/csw/3.0",
        "ows": "http://www.opengis.net/ows/2.0",
        "xsi": "http://www.w3.org/2001/xmlschema-instance",
        "dc": "http://purl.org/dc/elements/1.1/",
        "dct":"http://purl.org/dc/terms/",
    }
    result = fmt_json.xml2dict(xml_string=xml, namespaces=namespaces)
    assert result["csw:GetRecordsResponse"]["csw:SearchResults"][
        "csw:Record"]["dc:identifier"] == identifier
