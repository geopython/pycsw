#!/usr/bin/python
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
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

# simple testing framework inspired by MapServer msautotest

import csv
import sys
import os
import getopt
import glob
import filecmp
import re
import codecs
from io import BytesIO
import json
import logging

from lxml import etree
from lxml import objectify

from pycsw.core.util import http_request

logger = logging.getLogger(__name__)


def plural(num):
    """Determine plurality given an integer"""
    if num != 1:
        return 's'
    else:
        return ''


def test_xml_result(result, expected, encoding="utf-8"):
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
        happen if there are relative namespace URIs in any of the XML documents,
        as they are explicitly not allowed when doing XML c14n

    References
    ----------
    .. [1] http://www.w3.org/TR/xml-c14n

    """

    try:
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
        if not matches:
            print("result:")
            print(result_buffer.getvalue())
            print("+++++++++++++++++++++++")
            print("expected:")
            print(expected_buffer.getvalue())

    except etree.XMLSyntaxError:
        matches = None
    return matches


def test_json_result(result, expected, encoding="utf-8"):
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

    try:
        result_dict = json.loads(result.decode(encoding), encoding=encoding)
        expected_dict = json.loads(expected, encoding=encoding)
    except ValueError:
        matches = None
    else:
        matches = result_dict == expected_dict
    return matches


def get_validity(expected_path, result, output_file_name, force_id_mask=False):
    """Test whether the test result matches the expected outcome.

    This function deals with both XML and JSON results. It first tries to
    parse the result and the expected outcome as XML and evaluates them using
    XML canonicalization (c14n). If the result cannot be parsed as XML, it then
    tries to load it as JSON and does a sorted comparison.

    Parameters
    ----------
    expected_path: str
        The path to the file that has the expected test outcome
    result: str
        The actual result that was generated by running the test code
    output_file_name: str
        Name of the file that will be written to disk with the contents of
        the result
    force_id_mask: bool, optional
        Whether to apply result normalization to id fields

    Returns
    -------
    int
        One of three possible values:

        * If the input `expected_path` could not be found, the results will
          be used to generate a new expected file. In this case the return
          value will be 0;
        * If the result matches the expected outcome, the return value is 1;
        * If the result does not match the expected outcome the return value is
          -1.

    """

    encoding = "utf-8"
    normalized_result = normalize(result, force_id_mask=force_id_mask)
    if not os.path.exists(expected_path):  # create expected file
        with codecs.open(expected_path, 'w', encoding=encoding) as f:
            f.write(normalized_result)
        status = 0
    else:  # compare result with expected
        with codecs.open(expected_path, encoding=encoding) as expected_fh:
            expected = expected_fh.read()
            matches_expected = test_xml_result(normalized_result, expected)
            if matches_expected is None:
                # the file is either not XML (perhaps JSON?) or malformed
                matches_expected = test_json_result(
                    normalized_result, expected, encoding=encoding)
        if matches_expected:  # pass
            status = 1
        else:  # failed
            status = -1
            if not os.path.exists('results'):
                os.mkdir('results')
            with open('results%s%s' % (os.sep, output_file_name), 'wb') as f:
                f.write(normalized_result)
    return status


def pedantic_get_validity(sexpected, sresult, soutfile, force_id_mask=False):
    """Decipher whether the output passes, fails, or initializes"""
    if not os.path.exists(sexpected):  # create expected file
        with open(sexpected, 'w') as f:
            f.write(normalize(sresult, force_id_mask))
        sstatus = 0
    else:  # compare result with expected
        if not os.path.exists('results'):
            os.mkdir('results')
        with open('results%s%s' % (os.sep, soutfile), 'wb') as f:
            f.write(normalize(sresult, force_id_mask))
        if filecmp.cmp(sexpected, 'results%s%s' % (os.sep, soutfile)):  # pass
            os.remove('results%s%s' % (os.sep, soutfile))
            sstatus = 1
        else:  # fail
            import difflib
            encoding = "utf-8"
            with codecs.open(sexpected, encoding=encoding) as a:
                with codecs.open('results%s%s' % (os.sep, soutfile),
                                 encoding=encoding) as b:
                    a2 = a.readlines()
                    b2 = b.readlines()
                    diff = difflib.unified_diff(a2, b2)
            print('\n'.join(list(diff)))
            if len(a2) != len(b2):
                print('LINE COUNT: expected: %d, result: %d' % (len(a2), len(b2)))
            sstatus = -1
    return sstatus


def normalize(sresult, force_id_mask=False):
    """Replace time, updateSequence and version specific values with generic
    values"""

    # XML responses
    version = re.search(b'<!-- (.*) -->', sresult)
    updatesequence = re.search(b'updateSequence="(\S+)"', sresult)
    timestamp = re.search(b'timestamp="(.*)"', sresult)
    timestamp2 = re.search(b'timeStamp="(.*)"', sresult)
    timestamp3 = re.search(b'<oai:responseDate>(.*)</oai:responseDate>', sresult)
    timestamp4 = re.search(b'<oai:earliestDatestamp>(.*)</oai:earliestDatestamp>', sresult)
    zrhost = re.search(b'<zr:host>(.*)</zr:host>', sresult)
    zrport = re.search(b'<zr:port>(.*)</zr:port>', sresult)
    elapsed_time = re.search(b'elapsedTime="(.*)"', sresult)
    expires = re.search(b'expires="(.*?)"', sresult)
    atom_updated = re.findall(b'<atom:updated>(.*)</atom:updated>', sresult)

    if version:
        sresult = sresult.replace(version.group(0), b'<!-- PYCSW_VERSION -->')
    if updatesequence:
        sresult = sresult.replace(updatesequence.group(0),
                                  b'updateSequence="PYCSW_UPDATESEQUENCE"')
    if timestamp:
        sresult = sresult.replace(timestamp.group(0),
                                  b'timestamp="PYCSW_TIMESTAMP"')
    if timestamp2:
        sresult = sresult.replace(timestamp2.group(0),
                                  b'timeStamp="PYCSW_TIMESTAMP"')
    if timestamp3:
        sresult = sresult.replace(timestamp3.group(0),
                                  b'<oai:responseDate>PYCSW_TIMESTAMP</oai:responseDate>')
    if timestamp4:
        sresult = sresult.replace(timestamp4.group(0),
                                  b'<oai:earliestDatestamp>PYCSW_TIMESTAMP</oai:earliestDatestamp>')
    if zrport:
        sresult = sresult.replace(zrport.group(0),
                                  b'<zr:port>PYCSW_PORT</zr:port>')
    if zrhost:
        sresult = sresult.replace(zrhost.group(0),
                                  b'<zr:host>PYCSW_HOST</zr:host>')
    if elapsed_time:
        sresult = sresult.replace(elapsed_time.group(0),
                                  b'elapsedTime="PYCSW_ELAPSED_TIME"')
    if expires:
        sresult = sresult.replace(expires.group(0),
                                  b'expires="PYCSW_EXPIRES"')
    for au in atom_updated:
        sresult = sresult.replace(au, b'PYCSW_TIMESTAMP')

    # for csw:HarvestResponse documents, mask identifiers
    # which are dynamically generated for OWS endpoints
    if sresult.find(b'HarvestResponse') != -1:
        identifier = re.findall(b'<dc:identifier>(\S+)</dc:identifier>',
                                sresult)
        for i in identifier:
            sresult = sresult.replace(i, b'PYCSW_IDENTIFIER')

    # JSON responses
    timestamp = re.search(b'"@timestamp": "(.*?)"', sresult)

    if timestamp:
        sresult = sresult.replace(timestamp.group(0),
                                  b'"@timestamp": "PYCSW_TIMESTAMP"')

    # harvesting-based GetRecords/GetRecordById responses
    if force_id_mask:
        dcid = re.findall(b'<dc:identifier>(urn:uuid.*)</dc:identifier>', sresult)
        isoid = re.findall(b'id="(urn:uuid.*)"', sresult)
        isoid2 = re.findall(b'<gco:CharacterString>(urn:uuid.*)</gco', sresult)

        for d in dcid:
            sresult = sresult.replace(d, b'PYCSW_IDENTIFIER')
        for i in isoid:
            sresult = sresult.replace(i, b'PYCSW_IDENTIFIER')
        for i2 in isoid2:
            sresult = sresult.replace(i2, b'PYCSW_IDENTIFIER')

    return sresult

def usage():
    """Provide usage instructions"""
    return '''
NAME
    run_tests.py - pycsw unit test testrunner

SYNOPSIS
    run_tests.py -u <url> [-l logfile] [-s suite1[,suite2]]

    Available options:

    -u    URL to test

    -l    log results to file

    -s    testsuites to run (comma-seperated list)

    -d    database (SQLite3 [default], PostgreSQL, MySQL)

    -r    run tests which harvest remote resources (default off)

EXAMPLES

    1.) default test example

        run_tests.py -u http://localhost:8000/

    2.) log results to logfile

        run_tests.py -u http://localhost:8000/ -l /path/to/results.log

    3.) run only specified testsuites

        run_tests.py -u http://localhost:8000/ -s default,apiso

    3.) run tests including remote harvest tests

        run_tests.py -u http://localhost:8000/ -s default,apiso -r


'''

# main

if len(sys.argv) < 2:
    print(usage())
    sys.exit(1)

URL = sys.argv[1]

URL = None
LOGFILE = None
TESTSUITES = []

PASSED = 0
FAILED = 0
WARNING = 0
INITED = 0

LOGWRITER = None
DATABASE = 'SQLite3'
REMOTE = False
PEDANTIC = False

try:
    OPTS, ARGS = getopt.getopt(sys.argv[1:], 'u:l:s:d:rhp')
except getopt.GetoptError as err:
    print('\nERROR: %s' % err)
    print(usage())
    sys.exit(2)

for o, a in OPTS:
    if o == '-u':
        URL = a
    if o == '-l':
        LOGFILE = a
    if o == '-d':
        DATABASE = a
    if o == '-r':
        REMOTE = True
    if o == '-p':
        PEDANTIC = True
    if o == '-s':
        TESTSUITES = a.split(',')
    if o == '-h':  # dump help and exit
        print(usage())
        sys.exit(3)

print('\nRunning tests against %s' % URL)

if LOGFILE is not None:  # write detailed output to CSV
    LOGWRITER = csv.writer(open(LOGFILE, 'wb'))
    LOGWRITER.writerow(['url', 'configuration', 'testname', 'result'])

if TESTSUITES:
    if 'harvesting' in TESTSUITES:
        REMOTE = True
    TESTSUITES_LIST = ['suites%s%s' % (os.sep, x) for x in TESTSUITES]
else:
    TESTSUITES_LIST = glob.glob('suites%s*' % os.sep)

for testsuite in TESTSUITES_LIST:
    if not os.path.exists(testsuite):
        raise RuntimeError('Testsuite %s not found' % testsuite)

    if testsuite == 'suites%sharvesting' % os.sep and not REMOTE:
        continue

    force_id_mask = False
    if testsuite in ['suites%smanager' % os.sep, 'suites%sharvesting' % os.sep]:
        force_id_mask = True

    # get configuration
    for cfg in glob.glob('%s%s*.cfg' % (testsuite, os.sep)):
        print('\nTesting configuration %s' % cfg)

        for root, dirs, files in os.walk(testsuite):
            if files:
                for sfile in sorted(files):
                    if os.path.splitext(sfile)[1] not in ['.xml', '.txt']:
                        break

                    if sfile == 'requests.txt':  # GET requests
                        filename = '%s%s%s' % (root, os.sep, sfile)
                        with open(filename) as f:
                            gets = csv.reader(f)
                            for row in gets:
                                testfile = '%s%s%s' % (root, os.sep, sfile)
                                request = ','.join(row[1:]).replace('PYCSW_SERVER',
                                                                    URL)
                                outfile = '%s%s' % (root.replace(os.sep, '_'),
                                                    '_%s.xml' % row[0])
                                expected = 'expected%s%s' % (os.sep, outfile)
                                print('\n test %s:%s' % (testfile, row[0]))

                                try:
                                    result = http_request('GET', request)
                                except Exception as err:
                                    result = err.read()
                                if PEDANTIC:
                                    status = pedantic_get_validity(
                                        expected, result, outfile,
                                        force_id_mask
                                    )
                                else:
                                    try:
                                        status = get_validity(expected, result,
                                                              outfile,
                                                              force_id_mask)
                                    except etree.C14NError:
                                        logger.info("Could not canonicalize "
                                                    "{}. Using pedantic "
                                                    "mode".format(sfile))
                                        status = pedantic_get_validity(
                                            expected, result, outfile,
                                            force_id_mask
                                        )

                                if status == 1:
                                    print('  passed')
                                    PASSED += 1
                                elif status == 0:
                                    print('  initialized')
                                    INITED += 1
                                elif status == -1 and DATABASE == 'PostgreSQL':
                                    print('  warning: possible collation issue')
                                    WARNING += 1
                                else:
                                    print('  FAILED')
                                    FAILED += 1

                                if LOGWRITER is not None:
                                    LOGWRITER.writerow([URL, cfg,
                                                        testfile, status])

                    else:  # POST requests
                        testfile = '%s%s%s' % (root, os.sep, sfile)
                        if '%sdata' % os.sep in testfile:  # sample data
                            break
                        outfile = '%s%s' % (os.sep,
                                            testfile.replace(os.sep, '_'))
                        expected = 'expected%s%s' % (os.sep, outfile)
                        print('\n test %s' % testfile)

                        # read test
                        encoding = "utf-8"
                        with codecs.open(testfile, encoding=encoding) as fh:
                            request = fh.read().encode(encoding)

                        configkvp = 'config=tests%s%s' % (os.sep, cfg)
                        url2 = '%s?%s' % (URL, configkvp)

                        # invoke request
                        try:
                            result = http_request('POST', url2, request)
                        except Exception as err:
                            result = err.read()
                        if PEDANTIC:
                            status = pedantic_get_validity(
                                expected, result, outfile, force_id_mask)
                        else:
                            try:
                                status = get_validity(expected, result, outfile,
                                                      force_id_mask)
                            except etree.C14NError:
                                logger.info("Could not canonicalize {}. Using "
                                            "pedantic mode".format(sfile))
                                status = pedantic_get_validity(
                                    expected, result, outfile, force_id_mask)

                        if status == 1:
                            print('  passed')
                            PASSED += 1
                        elif status == 0:
                            print('  initialized')
                            INITED += 1
                        elif status == -1 and DATABASE == 'PostgreSQL':
                            print('  warning: possible sorting collation issue')
                            WARNING += 1
                        else:
                            print('  FAILED')
                            FAILED += 1

                        if LOGWRITER is not None:
                            LOGWRITER.writerow([URL, cfg, testfile, status])

if LOGWRITER is not None:
    LOGWRITER.close()

print('\nResults (%d/%d - %.2f%%)' %
      (PASSED, PASSED + FAILED, float(PASSED) / float(PASSED + FAILED) * 100))
print('   %d test%s passed' % (PASSED, plural(PASSED)))
print('   %d test%s warnings' % (WARNING, plural(WARNING)))
print('   %d test%s failed' % (FAILED, plural(FAILED)))
print('   %d test%s initialized' % (INITED, plural(INITED)))

sys.exit(FAILED)
