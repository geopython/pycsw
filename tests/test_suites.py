# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2016 Tom Kralidis
# Copyright (c) 2016 Ricardo Garcia Silva
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
"""Functional tests for pycsw.

These tests are based on the execution of the requests defined in the suites
under the `suites` directory.

"""

from io import BytesIO
import json
from lxml import etree
from lxml import objectify
import re
from urllib.parse import parse_qs
from urllib.parse import unquote

import pytest
import requests

ENCODING = "utf-8"

pytestmark = pytest.mark.functional


class TestApisoSuite(object):

    def test_post_requests(self,
                           server_apiso_suite,
                           apiso_test_request,
                           apiso_expected_post_result):
        _test_post_request(server_apiso_suite,
                           apiso_test_request,
                           apiso_expected_post_result)


class TestApisoInspireSuite(object):

    def test_get_requests(self,
                          server_apiso_inspire_suite,
                          apiso_inspire_test_request_parameters,
                          apiso_inspire_expected_get_result):
        _test_get_request(server_apiso_inspire_suite,
                          apiso_inspire_test_request_parameters,
                          apiso_inspire_expected_get_result)


class TestAtomSuite(object):

    def test_post_requests(self,
                           server_atom_suite,
                           atom_test_request,
                           atom_expected_post_result):
        _test_post_request(server_atom_suite,
                           atom_test_request,
                           atom_expected_post_result)

    def test_get_requests(self, server_atom_suite,
                          atom_test_request_parameters,
                          atom_expected_get_result):
        _test_get_request(server_atom_suite,
                          atom_test_request_parameters,
                          atom_expected_get_result)


class TestCiteSuite(object):

    def test_post_requests(self, server_cite_suite, cite_test_request,
                           cite_expected_post_result):
        _test_post_request(server_cite_suite, cite_test_request,
                           cite_expected_post_result)

    def test_get_requests(self, server_cite_suite,
                          cite_test_request_parameters,
                          cite_expected_get_result):
        print("locals: {0}".format(locals()))
        _test_get_request(server_cite_suite, cite_test_request_parameters,
                          cite_expected_get_result)


class TestCsw30Suite(object):

    def test_post_requests(self,
                           server_csw30_suite,
                           csw30_test_request,
                           csw30_expected_post_result):
        _test_post_request(server_csw30_suite,
                           csw30_test_request,
                           csw30_expected_post_result)

    def test_get_requests(self, server_csw30_suite,
                          csw30_test_request_parameters,
                          csw30_expected_get_result):
        _test_get_request(server_csw30_suite,
                          csw30_test_request_parameters,
                          csw30_expected_get_result)


class TestDefaultSuite(object):

    def test_post_requests(self,
                           server_default_suite,
                           default_test_request,
                           default_expected_post_result):
        _test_post_request(server_default_suite,
                           default_test_request,
                           default_expected_post_result)

    def test_get_requests(self,
                          server_default_suite,
                          default_test_request_parameters,
                          default_expected_get_result):
        _test_get_request(server_default_suite,
                          default_test_request_parameters,
                          default_expected_get_result)


class TestDifSuite(object):

    def test_post_requests(self,
                           server_dif_suite,
                           dif_test_request,
                           dif_expected_post_result):
        _test_post_request(server_dif_suite,
                           dif_test_request,
                           dif_expected_post_result)


class TestEbrimSuite(object):

    def test_post_requests(self, server_ebrim_suite,
                           ebrim_test_request,
                           ebrim_expected_post_result):
        _test_post_request(server_ebrim_suite,
                           ebrim_test_request,
                           ebrim_expected_post_result)


class TestFgdcSuite(object):

    def test_post_requests(self,
                           server_fgdc_suite,
                           fgdc_test_request,
                           fgdc_expected_post_result):
        _test_post_request(server_fgdc_suite,
                           fgdc_test_request,
                           fgdc_expected_post_result)


class TestGm03Suite(object):

    def test_post_requests(self,
                           server_gm03_suite,
                           gm03_test_request,
                           gm03_expected_post_result):
        _test_post_request(server_gm03_suite,
                           gm03_test_request,
                           gm03_expected_post_result)


class TestHarvestingSuite(object):

    def test_post_requests(self,
                           server_harvesting_suite,
                           harvesting_test_request,
                           harvesting_expected_post_result):
        _test_post_request(server_harvesting_suite,
                           harvesting_test_request,
                           harvesting_expected_post_result)

    def test_get_requests(self,
                          server_harvesting_suite,
                          harvesting_test_request_parameters,
                          harvesting_expected_get_result):
        _test_get_request(server_harvesting_suite,
                          harvesting_test_request_parameters,
                          harvesting_expected_get_result)


class TestManagerSuite(object):

    def test_post_requests(self,
                           server_manager_suite,
                           manager_test_request,
                           manager_expected_post_result):
        _test_post_request(server_manager_suite,
                           manager_test_request,
                           manager_expected_post_result)


class TestOaipmhSuite(object):

    def test_get_requests(self, server_oaipmh_suite,
                          oaipmh_test_request_parameters,
                          oaipmh_expected_get_result):
        _test_get_request(server_oaipmh_suite,
                          oaipmh_test_request_parameters,
                          oaipmh_expected_get_result)


class TestRepofilterSuite(object):

    def test_post_requests(self,
                           server_repofilter_suite,
                           repofilter_test_request,
                           repofilter_expected_post_result):
        _test_post_request(server_repofilter_suite,
                           repofilter_test_request,
                           repofilter_expected_post_result)


class TestSruSuite(object):

    def test_get_requests(self,
                          server_sru_suite,
                          sru_test_request_parameters,
                          sru_expected_get_result):
        _test_get_request(server_sru_suite,
                          sru_test_request_parameters,
                          sru_expected_get_result)

class TestUtf8Suite(object):

    def test_post_requests(self,
                           server_utf_8_suite,
                           utf_8_test_request,
                           utf_8_expected_post_result):
        _test_post_request(server_utf_8_suite,
                           utf_8_test_request,
                           utf_8_expected_post_result)


def _test_post_request(pycsw_server_url, test_request, expected_result):
    with open(test_request, encoding=ENCODING) as request_fh:
        request_data = request_fh.read()
    response = requests.post(pycsw_server_url,
                             data=bytes(request_data, ENCODING))
    with open(expected_result, encoding=ENCODING) as expected_fh:
        expected = expected_fh.read()
    _compare_response(response, expected)


def _test_get_request(pycsw_server_url, parameters, expected_result):
    print("**********************")
    print("EXPECTED_RESULT: {0}".format(expected_result))
    print("PARAMETERS: {0}".format(parameters))
    print("**********************")
    with open(expected_result, encoding=ENCODING) as expected_fh:
        expected = expected_fh.read()
    #payload = parse_qs(bytes(parameters, ENCODING))
    #payload = parse_qs(parameters)
    payload = {}
    for kvp in parameters.split("&"):
        print("kvp: {}".format(kvp))
        parts = kvp.split("=")
        payload[parts[0].lower()] = unquote(parts[1]) if len(parts) > 1 else ""
        #payload[parts[0].lower()] = parts[1] if len(parts) > 1 else ""
    print("payload: {0}".format(payload))
    request_headers = {}
    if "outputformat" in payload.keys():
        request_headers.setdefault("Accept", payload["outputformat"])
    response = requests.get(pycsw_server_url, params=payload,
                            headers=request_headers)
    _compare_response(response, expected)


def _compare_response(response, expected):
    response.encoding = ENCODING
    response_data = response.text
    normalized_result = _normalize(response_data, force_id_mask=False)
    try:
        matches_expected = _test_xml_result(normalized_result, expected)
    except etree.XMLSyntaxError:
        # the file is either not XML (perhaps JSON?) or malformed
        matches_expected = _test_json_result(normalized_result, expected)
    if not matches_expected:
        print("expected: {0}".format(expected))
        print("response: {0}".format(normalized_result))
    assert matches_expected


def _test_xml_result(result, expected):
    """Compare the XML test results with an expected value.

    This function compares the test result with the expected values by
    performing XML canonicalization (c14n)[1]_.

    Parameters
    ----------
    result: str
        The result of running the test.
    expected: str
        The expected outcome.

    Returns
    -------
    bool
        Whether the result matches the expectations or not.

    Raises
    ------
    etree.XMLSyntaxError
        If any of the input parameters is not a valid XMl.
    etree.C14NError
        If any of the input parameters cannot be canonicalized. This may
        happen if there are relative namespace URIs in any of the XML
        documents, as they are explicitly not allowed when doing XML c14n

    References
    ----------
    .. [1] http://www.w3.org/TR/xml-c14n

    """

    result_element = etree.fromstring(result.encode(ENCODING))
    expected_element = etree.fromstring(expected.encode(ENCODING))
    result_buffer = BytesIO()
    result_tree = result_element.getroottree()
    objectify.deannotate(result_tree, cleanup_namespaces=True)
    result_tree.write_c14n(result_buffer)
    expected_buffer = BytesIO()
    expected_tree = expected_element.getroottree()
    objectify.deannotate(expected_tree, cleanup_namespaces=True)
    expected_tree.write_c14n(expected_buffer)
    matches = result_buffer.getvalue() == expected_buffer.getvalue()
    return matches


def _test_json_result(result, expected):
    """Compare the JSON test results with an expected value.

    Parameters
    ----------
    result: str
        The result of running the test.
    expected: str
        The expected outcome.

    Returns
    -------
    bool
        Whether the result matches the expectations or not.

    """

    result_dict = json.loads(result, encoding=ENCODING)
    expected_dict = json.loads(expected, encoding=ENCODING)
    return result_dict == expected_dict


def _normalize(sresult, force_id_mask=False):
    """Replace time, updateSequence and version specific values with generic
    values"""

    # XML responses
    version = re.search(r'<!-- (.*) -->', sresult)
    updatesequence = re.search(r'updateSequence="(\S+)"', sresult)
    timestamp = re.search(r'timestamp="(.*)"', sresult)
    timestamp2 = re.search(r'timeStamp="(.*)"', sresult)
    timestamp3 = re.search(r'<oai:responseDate>(.*)</oai:responseDate>', sresult)
    timestamp4 = re.search(r'<oai:earliestDatestamp>(.*)</oai:earliestDatestamp>', sresult)
    zrhost = re.search(r'<zr:host>(.*)</zr:host>', sresult)
    zrport = re.search(r'<zr:port>(.*)</zr:port>', sresult)
    elapsed_time = re.search(r'elapsedTime="(.*)"', sresult)
    expires = re.search(r'expires="(.*?)"', sresult)
    atom_updated = re.findall(r'<atom:updated>(.*)</atom:updated>', sresult)

    if version:
        sresult = sresult.replace(version.group(0), r'<!-- PYCSW_VERSION -->')
    if updatesequence:
        sresult = sresult.replace(updatesequence.group(0),
                                  r'updateSequence="PYCSW_UPDATESEQUENCE"')
    if timestamp:
        sresult = sresult.replace(timestamp.group(0),
                                  r'timestamp="PYCSW_TIMESTAMP"')
    if timestamp2:
        sresult = sresult.replace(timestamp2.group(0),
                                  r'timeStamp="PYCSW_TIMESTAMP"')
    if timestamp3:
        sresult = sresult.replace(timestamp3.group(0),
                                  r'<oai:responseDate>PYCSW_TIMESTAMP</oai:responseDate>')
    if timestamp4:
        sresult = sresult.replace(timestamp4.group(0),
                                  r'<oai:earliestDatestamp>PYCSW_TIMESTAMP</oai:earliestDatestamp>')
    if zrport:
        sresult = sresult.replace(zrport.group(0),
                                  r'<zr:port>PYCSW_PORT</zr:port>')
    if zrhost:
        sresult = sresult.replace(zrhost.group(0),
                                  r'<zr:host>PYCSW_HOST</zr:host>')
    if elapsed_time:
        sresult = sresult.replace(elapsed_time.group(0),
                                  r'elapsedTime="PYCSW_ELAPSED_TIME"')
    if expires:
        sresult = sresult.replace(expires.group(0),
                                  r'expires="PYCSW_EXPIRES"')
    for au in atom_updated:
        sresult = sresult.replace(au, r'PYCSW_TIMESTAMP')

    # for csw:HarvestResponse documents, mask identifiers
    # which are dynamically generated for OWS endpoints
    if sresult.find(r'HarvestResponse') != -1:
        identifier = re.findall(r'<dc:identifier>(\S+)</dc:identifier>',
                                sresult)
        for i in identifier:
            sresult = sresult.replace(i, r'PYCSW_IDENTIFIER')

    # JSON responses
    timestamp = re.search(r'"@timestamp": "(.*?)"', sresult)

    if timestamp:
        sresult = sresult.replace(timestamp.group(0),
                                  r'"@timestamp": "PYCSW_TIMESTAMP"')

    # harvesting-based GetRecords/GetRecordById responses
    if force_id_mask:
        dcid = re.findall(r'<dc:identifier>(urn:uuid.*)</dc:identifier>', sresult)
        isoid = re.findall(r'id="(urn:uuid.*)"', sresult)
        isoid2 = re.findall(r'<gco:CharacterString>(urn:uuid.*)</gco', sresult)

        for d in dcid:
            sresult = sresult.replace(d, r'PYCSW_IDENTIFIER')
        for i in isoid:
            sresult = sresult.replace(i, r'PYCSW_IDENTIFIER')
        for i2 in isoid2:
            sresult = sresult.replace(i2, r'PYCSW_IDENTIFIER')

    return sresult
