#!/usr/bin/python
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

# simple testing framework inspired by MapServer msautotest

import csv
import sys
import os
import urllib2
import httplib
import glob
import urlparse
import filecmp
import re


def plural(num):
    """Determine plurality given an integer"""
    if num != 1:
        return 's'
    else:
        return ''


def http_req(method, surl, srequest):
    """Perform HTTP request"""
    if method == 'POST':
        # send an XML document as a HTTP POST request
        ups = urlparse.urlsplit(surl)

        htl = httplib.HTTP(ups.netloc)
        htl.putrequest('POST', '%s?%s' % (ups.path, ups.query))
        htl.putheader('Content-type', 'text/xml')
        htl.putheader('Content-length', '%d' % len(srequest))
        htl.putheader('Accepts', 'text/xml')
        htl.putheader('Host', ups.netloc)
        htl.putheader('User-Agent', 'pycsw unit tests')
        htl.endheaders()
        htl.send(srequest)
        reply, msg, hdrs = htl.getreply()
        return htl.getfile().read()
    else:  # GET
        req = urllib2.Request(surl)
        return urllib2.urlopen(req).read()


def get_validity(sexpected, sresult, soutfile):
    """Decipher whether the output passes, fails, or initializes"""
    if not os.path.exists(sexpected):  # create expected file
        expectedfile = open(sexpected, 'w')
        expectedfile.write(normalize(sresult))
        expectedfile.close()
        sstatus = 0
    else:  # compare result with expected
        if not os.path.exists('results'):
            os.mkdir('results')
        resultfile = open('results%s%s' % (os.sep, soutfile), 'wb')
        resultfile.write(normalize(sresult))
        resultfile.close()
        if filecmp.cmp(sexpected, 'results%s%s' % (os.sep, soutfile)):  # pass
            os.remove('results%s%s' % (os.sep, soutfile))
            sstatus = 1
        else:  # fail
            import difflib
            diff = difflib.unified_diff(
                open(sexpected).readlines(),
                open('results%s%s' % (os.sep, soutfile)).readlines())
            print '\n'.join(list(diff))
            sstatus = -1
    return sstatus


def normalize(sresult):
    """Replace time, updateSequence and version specific values with generic
    values"""

    # XML responses
    version = re.search('<!-- (.*) -->', sresult)
    updatesequence = re.search('updateSequence="(\S+)"', sresult)
    timestamp = re.search('timestamp="(.*)"', sresult)
    timestamp2 = re.search('timeStamp="(.*)"', sresult)
    zrhost = re.search('<zr:host>(.*)</zr:host>', sresult)
    zrport = re.search('<zr:port>(.*)</zr:port>', sresult)

    if version:
        sresult = sresult.replace(version.group(0), '<!-- PYCSW_VERSION -->')
    if updatesequence:
        sresult = sresult.replace(updatesequence.group(0),
                                  'updateSequence="PYCSW_UPDATESEQUENCE"')
    if timestamp:
        sresult = sresult.replace(timestamp.group(0),
                                  'timestamp="PYCSW_TIMESTAMP"')
    if timestamp2:
        sresult = sresult.replace(timestamp2.group(0),
                                  'timeStamp="PYCSW_TIMESTAMP"')
    if zrport:
        sresult = sresult.replace(zrport.group(0),
                                  '<zr:port>PYCSW_PORT</zr:port>')
    if zrhost:
        sresult = sresult.replace(zrhost.group(0),
                                  '<zr:host>PYCSW_HOST</zr:host>')

    # for csw:HarvestResponse documents, mask identifiers
    # which are dynamically generated for OWS endpoints
    if sresult.find('HarvestResponse') != -1:
        identifier = re.findall('<dc:identifier>(\S+)</dc:identifier>',
                                sresult)
        for i in identifier:
            sresult = sresult.replace(i, 'PYCSW_IDENTIFIER')

    # JSON responses
    timestamp = re.search('"timestamp": "(.*?)"', sresult)

    if timestamp:
        sresult = sresult.replace(timestamp.group(0),
                                  '"timestamp": "PYCSW_TIMESTAMP"')
    return sresult

# main

if len(sys.argv) < 2:
    print 'Usage: %s <url> [log]' % sys.argv[0]
    sys.exit(1)

URL = sys.argv[1]

PASSED = 0
FAILED = 0
INITED = 0

LOGWRITER = None

print '\nRunning tests against %s' % URL

if len(sys.argv) == 3:  # write detailed output to CSV
    LOGWRITER = csv.writer(open(sys.argv[2], 'wb'))
    LOGWRITER.writerow(['url', 'configuration', 'testname', 'result'])

for testsuite in glob.glob('suites%s*' % os.sep):

    # get configuration
    for cfg in glob.glob('%s%s*.cfg' % (testsuite, os.sep)):
        print '\nTesting configuration %s' % cfg

        for root, dirs, files in os.walk(testsuite):
            if files:
                for sfile in sorted(files):
                    if os.path.splitext(sfile)[1] not in ['.xml', '.txt']:
                        break

                    if sfile == 'requests.txt':  # GET requests
                        filename = '%s%s%s' % (root, os.sep, sfile)
                        gets = csv.reader(open(filename))
                        for row in gets:
                            testfile = '%s%s%s' % (root, os.sep, sfile)
                            request = ','.join(row[1:]).replace('PYCSW_SERVER',
                                                                URL)
                            outfile = '%s%s' % (root.replace(os.sep, '_'),
                                                '_%s.xml' % row[0])
                            expected = 'expected%s%s' % (os.sep, outfile)
                            print '\n test %s:%s' % (testfile, row[0])

                            result = http_req('GET', request, request)

                            status = get_validity(expected, result, outfile)

                            if status == 1:
                                print '  passed'
                                PASSED += 1
                            elif status == 0:
                                print '  initialized'
                                INITED += 1
                            else:
                                print '  FAILED'
                                FAILED += 1

                            if LOGWRITER is not None:
                                LOGWRITER.writerow([URL, cfg,
                                                    testfile, status])

                    else:  # POST requests
                        testfile = '%s%s%s' % (root, os.sep, sfile)
                        outfile = '%s%s' % (os.sep,
                                            testfile.replace(os.sep, '_'))
                        expected = 'expected%s%s' % (os.sep, outfile)
                        print '\n test %s' % testfile

                        # read test
                        f = open(testfile)
                        request = f.read()
                        f.close()

                        configkvp = 'config=tests%s%s' % (os.sep, cfg)
                        url2 = '%s?%s' % (URL, configkvp)

                        # invoke request
                        result = http_req('POST', url2, request)

                        status = get_validity(expected, result, outfile)

                        if status == 1:
                            print '  passed'
                            PASSED += 1
                        elif status == 0:
                            print '  initialized'
                            INITED += 1
                        else:
                            print '  FAILED'
                            FAILED += 1

                        if LOGWRITER is not None:
                            LOGWRITER.writerow([URL, cfg, testfile, status])

print '\nResults (%d/%d - %.2f%%)' % \
    (PASSED, PASSED + FAILED, float(PASSED) / float(PASSED + FAILED) * 100)
print '   %d test%s passed' % (PASSED, plural(PASSED))
print '   %d test%s failed' % (FAILED, plural(FAILED))
print '   %d test%s initialized' % (INITED, plural(INITED))

sys.exit(FAILED)
