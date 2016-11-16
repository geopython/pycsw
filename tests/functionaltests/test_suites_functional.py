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
"""Functional tests for several test suites"""

import codecs
from difflib import SequenceMatcher
from io import BytesIO
import json
import re
import wsgiref.util

from lxml import etree
from lxml import objectify
import pytest

from pycsw import server

pytestmark = pytest.mark.functional


def test_suites(configuration, request_method, request_data, expected_result,
                normalize_identifier_fields):
    """
    Test suites.

    Parameters
    ----------
    configuration: SafeConfigParser
        The configuration to use with the pycsw server instance under test
    request_method: str
        The HTTP method of the request. Either GET or POST.
    request_data: str
        Either the path to the request file, for POST requests or the request
        parameters for GET requests
    expected_result: str
        Path to the file that holds the expected result
    normalize_identifier_fields: bool
        Whether to normalize the identifier fields in responses. This
        parameter is used only in the 'harvesting' and 'manager' suites

    """

    request_environment = {
        "REQUEST_METHOD": request_method.upper(),
        "QUERY_STRING": "",
        "REMOTE_ADDR": "127.0.0.1"
    }
    if request_method == "POST":
        print("request_path: {0}".format(request_data))
        request_buffer = BytesIO()
        with open(request_data) as fh:
            contents = fh.read()
            print("Request contents: {}".format(contents))
            request_buffer.write(contents)
            request_environment["CONTENT_LENGTH"] = request_buffer.tell()
            request_buffer.seek(0)
            request_environment["wsgi.input"] = request_buffer
    else:
        print("Request contents: {0}".format(request_data))
        request_environment["QUERY_STRING"] = request_data
    wsgiref.util.setup_testing_defaults(request_environment)
    pycsw_server = server.Csw(rtconfig=configuration, env=request_environment)
    status, contents = pycsw_server.dispatch_wsgi()
    with codecs.open(expected_result, encoding="utf-8") as fh:
        expected = fh.read()
    _compare_response(contents, expected,
                      normalize_id_fields=normalize_identifier_fields)


def _compare_response(response, expected, normalize_id_fields):
    normalized_result = _normalize(response, force_id_mask=normalize_id_fields)
    try:
        matches_expected = _test_xml_result(normalized_result, expected)
    except etree.XMLSyntaxError:
        # the file is either not XML (perhaps JSON?) or malformed
        matches_expected = _test_json_result(normalized_result, expected)
    except etree.C14NError:
        print("XML canonicalization has failed. Trying to compare result "
              "with expected using difflib")
        matches_expected = _test_xml_diff(normalized_result, expected)
    if not matches_expected:
        print("expected: {0}".format(expected))
        print("response: {0}".format(normalized_result))
    assert matches_expected


def _test_xml_result(result, expected, encoding="utf-8"):
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

    result_element = etree.fromstring(result)
    expected_element = etree.fromstring(expected.encode(encoding))
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


def _test_json_result(result, expected, encoding="utf-8"):
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

    result_dict = json.loads(result, encoding=encoding)
    expected_dict = json.loads(expected, encoding=encoding)
    return result_dict == expected_dict


def _test_xml_diff(result, expected):
    sequence_matcher = SequenceMatcher(None, result, expected)
    ratio = sequence_matcher.ratio()
    return ratio == pytest.approx(1.0)


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
