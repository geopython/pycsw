# =================================================================
#
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#          Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2017 Ricardo Garcia Silva
# Copyright (c) 2017 Tom Kralidis
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
from difflib import unified_diff
from io import BytesIO
import json
import os
import re
import wsgiref.util

from lxml import etree
from lxml import objectify
import pytest

from pycsw import server

pytestmark = pytest.mark.functional


def test_suites(test_identifier, use_xml_canonicalisation,
                save_results_directory, configuration, request_method,
                request_data, expected_result, normalize_identifier_fields):
    """Test suites.

    This function is automatically parametrized by pytest as a result of the
    ``conftest:pytest_generate_tests`` function. The input parameters are thus
    supplied by pytest as a result of discovering and parsing the existing
    test suites located under ``tests/functionaltests/suites``.

    Parameters
    ----------
    configuration: SafeConfigParser
        The configuration to use with the pycsw server instance under test
    request_method: str
        The HTTP method of the request. Either GET or POST.
    request_data: str
        Either the path to the request file, for POST requests, or the request
        parameters, for GET requests
    expected_result: str
        Path to the file that holds the expected result
    normalize_identifier_fields: bool
        Whether to normalize the identifier fields in responses. This
        parameter is used only in the 'harvesting' and 'manager' suites
    use_xml_canonicalisation: bool
        Whether to compare results with their expected values by using xml
        canonicalisation or simply by doing a diff.
    save_results_directory: str
        Path to a directory where to test results should be saved to. A value
        of ``None`` (the default) means that results will not get saved to
        disk.

    """

    request_environment = _prepare_wsgi_test_environment(request_method,
                                                         request_data)
    pycsw_server = server.Csw(rtconfig=configuration, env=request_environment)
    encoding = "utf-8"
    status, raw_contents = pycsw_server.dispatch_wsgi()
    contents = raw_contents.decode(encoding)
    with codecs.open(expected_result, encoding=encoding) as fh:
        expected = fh.read()
    normalized_result = _normalize(
        contents,
        normalize_identifiers=normalize_identifier_fields
    )
    if use_xml_canonicalisation:
        print("Comparing results using XML canonicalization...")
        matches_expected = _compare_with_xml_canonicalisation(
            normalized_result, expected)
    else:
        print("Comparing results using diffs...")
        matches_expected = _compare_without_xml_canonicalisation(
            normalized_result, expected)
    if not matches_expected and use_xml_canonicalisation:
        print("expected: {0}".format(expected))
        print("response: {0}".format(normalized_result))
    if save_results_directory is not None:
        _save_test_result(save_results_directory, normalized_result,
                          test_identifier, encoding)
    assert matches_expected


def _compare_with_xml_canonicalisation(normalized_result, expected):
    try:
        matches_expected = _test_xml_result(normalized_result, expected)
    except etree.XMLSyntaxError:
        # the file is either not XML (perhaps JSON?) or malformed
        matches_expected = _test_json_result(normalized_result, expected)
    except etree.C14NError:
        print("XML canonicalisation has failed. Trying to compare result "
              "with expected using difflib")
        matches_expected = _test_xml_diff(normalized_result, expected)
    return matches_expected


def _compare_without_xml_canonicalisation(normalized_result, expected):
    return _test_xml_diff(normalized_result, expected)


def _prepare_wsgi_test_environment(request_method, request_data):
    """Set up a testing environment for tests.

    Parameters
    ----------
    request_method: str
        The HTTP method of the request. Sould be either GET or POST.
    request_data: str
        Either the path to the request file, for POST requests or the request
        parameters, for GET requests.

    Returns
    -------
    request_environment: dict
        A mapping with the environment variables to use in the test

    """

    request_environment = {
        "REQUEST_METHOD": request_method.upper(),
        "QUERY_STRING": "",
        "REMOTE_ADDR": "127.0.0.1"
    }
    if request_method == "POST":
        print("request_path: {0}".format(request_data))
        request_buffer = BytesIO()
        encoding = "utf-8"
        with codecs.open(request_data, encoding=encoding) as fh:
            contents = fh.read()
            request_buffer.write(contents.encode(encoding))
            request_environment["CONTENT_LENGTH"] = request_buffer.tell()
            request_buffer.seek(0)
            request_environment["wsgi.input"] = request_buffer
    else:
        print("Request contents: {0}".format(request_data))
        request_environment["QUERY_STRING"] = request_data
    wsgiref.util.setup_testing_defaults(request_environment)
    return request_environment


def _test_xml_result(result, expected, encoding="utf-8"):
    """Compare the XML test results with an expected value.

    This function compares the test result with the expected values by
    performing XML canonicalization (c14n)[1]_, which compares the semantic
    meanings of both XML files.

    Parameters
    ----------
    result: str
        The result of running the test as a unicode string
    expected: str
        The expected outcome as a unicode string.

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

    result_element = etree.fromstring(result.encode(encoding))
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
    """Compare two XML strings by using python's ``difflib.SequenceMatcher``.

    This is a character-by-character comparison and does not take into account
    the semantic meaning of XML elements and attributes.

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

    sequence_matcher = SequenceMatcher(None, result, expected)
    ratio = sequence_matcher.ratio()
    matches = ratio == pytest.approx(1.0)
    if not matches:
        print("Result does not match expected.")
        diff = unified_diff(result.splitlines(), expected.splitlines())
        print("\n".join(list(diff)))
    return matches


def _normalize(sresult, normalize_identifiers=False):
    """Normalize test output so it can be compared with the expected result.

    Several dynamic elements of a pycsw response (such as time,
    updateSequence, etc) are replaced with static constants to ease comparison.

    Parameters
    ----------
    sresult: str
        The test result as a unicode string.
    normalize_identifiers: bool, optional
        Whether identifier fields should be normalized.

    Returns
    -------
    str
        The normalized response.

    """

    # XML responses
    version = re.search(r'<!-- (.*) -->', sresult)
    updatesequence = re.search(r'updateSequence="(\S+)"', sresult)
    timestamp = re.search(r'timestamp="(.*)"', sresult)
    timestamp2 = re.search(r'timeStamp="(.*)"', sresult)
    timestamp3 = re.search(
        r'<oai:responseDate>(.*)</oai:responseDate>',
        sresult
    )
    timestamp4 = re.search(
        r'<oai:earliestDatestamp>(.*)</oai:earliestDatestamp>',
        sresult
    )
    zrhost = re.search(r'<zr:host>(.*)</zr:host>', sresult)
    zrport = re.search(r'<zr:port>(.*)</zr:port>', sresult)
    elapsed_time = re.search(r'elapsedTime="(.*)"', sresult)
    expires = re.search(r'expires="(.*?)"', sresult)
    atom_updated = re.findall(r'<atom:updated>(.*)</atom:updated>',
                              sresult)
    if version:
        sresult = sresult.replace(version.group(0),
                                  r'<!-- PYCSW_VERSION -->')
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
        sresult = sresult.replace(
            timestamp3.group(0),
            r'<oai:responseDate>PYCSW_TIMESTAMP</oai:responseDate>'
        )
    if timestamp4:
        sresult = sresult.replace(
            timestamp4.group(0),
            r'<oai:earliestDatestamp>PYCSW_TIMESTAMP</oai:earliestDatestamp>'
        )
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
        identifier = re.findall(
            r'<dc:identifier>(\S+)</dc:identifier>',
            sresult
        )
        for i in identifier:
            sresult = sresult.replace(i, r'PYCSW_IDENTIFIER')
    # JSON responses
    timestamp = re.search(r'"@timestamp": "(.*?)"', sresult)

    if timestamp:
        sresult = sresult.replace(timestamp.group(0),
                                  r'"@timestamp": "PYCSW_TIMESTAMP"')
    # harvesting-based GetRecords/GetRecordById responses
    if normalize_identifiers:
        dcid = re.findall(
            r'<dc:identifier>(urn:uuid.*)</dc:identifier>',
            sresult
        )
        isoid = re.findall(r'id="(urn:uuid.*)"', sresult)
        isoid2 = re.findall(
            r'<gco:CharacterString>(urn:uuid.*)</gco',
            sresult
        )
        for d in dcid:
            sresult = sresult.replace(d, r'PYCSW_IDENTIFIER')
        for i in isoid:
            sresult = sresult.replace(i, r'PYCSW_IDENTIFIER')
        for i2 in isoid2:
            sresult = sresult.replace(i2, r'PYCSW_IDENTIFIER')
    return sresult


def _save_test_result(target_directory_path, test_result, filename, encoding):
    """Save the input test result to disk"""
    full_directory_path = os.path.abspath(
        os.path.expanduser(os.path.expandvars(target_directory_path)))
    try:
        os.makedirs(full_directory_path)
    except OSError as exc:
        if exc.errno == 17:  # directory already exists
            pass
        else:
            raise
    target_path = os.path.join(full_directory_path, filename)
    with codecs.open(target_path, "w", encoding=encoding) as fh:
        fh.write(test_result)
    return target_path
