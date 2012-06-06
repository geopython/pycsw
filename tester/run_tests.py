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

import csv, sys, os, urllib2, httplib, glob, urlparse, filecmp, re

def plural(num):
    ''' Determine plurality given an integer '''
    if num != 1:
        return 's'
    else:
        return ''

def http_req(method, url, request):
    ''' Perform HTTP request '''
    if method == 'POST':
        '''Send an XML document as a HTTP POST request'''
        u = urlparse.urlsplit(url)

        h = httplib.HTTP(u.netloc)
        h.putrequest('POST', '%s?%s' % (u.path, u.query))
        h.putheader('Content-type', 'text/xml')
        h.putheader('Content-length', '%d' % len(request))
        h.putheader('Accepts', 'text/xml')
        h.putheader('Host', u.netloc)
        h.putheader('User-Agent', 'pycsw unit tester')
        h.endheaders()
        h.send(request)
        reply, msg, hdrs = h.getreply()
        return h.getfile().read()
    else:  # GET
        req = urllib2.Request(url)
        return urllib2.urlopen(req).read()

def get_validity(expected, result, outfile):
    ''' Decipher whether the output passes, fails, or initializes '''
    if os.path.exists(expected) is False:  # create expected file
        expectedfile = open(expected, 'w')
        expectedfile.write(normalize(result))
        expectedfile.close()
        status = 0
    else:  # compare result with expected
        if os.path.exists('results') is False:
            os.mkdir('results')
        resultfile = open('results%s%s' % (os.sep, outfile), 'wb')
        resultfile.write(normalize(result))
        resultfile.close()
        if filecmp.cmp(expected, 'results%s%s' % (os.sep, outfile)):  # pass
            os.remove('results%s%s' % (os.sep, outfile))
            status = 1
        else:  # fail
            status = -1
    return status

def normalize(result):
    ''' Replace time, updateSequence and version specific values with generic
    values '''

    # XML responses
    version = re.search('<!-- (.*) -->', result)
    updatesequence = re.search('updateSequence="(\S+)"', result)
    timestamp = re.search('timestamp="(.*)"', result)
    timestamp2 = re.search('timeStamp="(.*)"', result)

    if version:
        result = result.replace(version.group(0),'<!-- PYCSW_VERSION -->')
    if updatesequence:
        result = result.replace(updatesequence.group(0),'updateSequence="PYCSW_UPDATESEQUENCE"')
    if timestamp:
        result = result.replace(timestamp.group(0),
        'timestamp="PYCSW_TIMESTAMP"')
    if timestamp2:
        result = result.replace(timestamp2.group(0),
        'timeStamp="PYCSW_TIMESTAMP"')

    # for csw:HarvestResponse documents, mask identifiers
    # which are dynamically generated for OWS endpoints
    if result.find('HarvestResponse') != -1:
        identifier = re.search('<dc:identifier>(\S+)</dc:identifier>', result)
        if identifier:
            result = result.replace(identifier.group(0), 'PYCSW_IDENTIFIER')

    # JSON responses
    timestamp = re.search('"timestamp": "(.*?)"', result)

    if timestamp:
        result = result.replace(timestamp.group(0),
        '"timestamp": "PYCSW_TIMESTAMP"')
    return result

# main

if len(sys.argv) < 2:
    print 'Usage: %s <url> [log]' % sys.argv[0]
    sys.exit(1)

url = sys.argv[1]

passed = 0
failed = 0
inited = 0

logwriter = False

print '\nRunning tests against %s' % url

if len(sys.argv) == 3:  # write detailed output to CSV
    logwriter = csv.writer(open(sys.argv[2], 'wb'))
    logwriter.writerow(['url','configuration','testname','result'])

for testsuite in glob.glob('suites%s*' % os.sep):
    # get configuration
    for cfg in glob.glob('%s%s*.cfg' % (testsuite, os.sep)):
        print '\nTesting configuration %s' % cfg

        for root, dirs, files in os.walk(testsuite):
            if files:
                for file in sorted(files):
                    if os.path.splitext(file)[1] not in ['.xml','.txt']:
                        break

                    if file == 'requests.txt':  # GET requests
                        gets = csv.reader(open('%s%s%s' % (root, os.sep, file)))
                        for row in gets:
                            testfile = '%s%s%s' % (root, os.sep, file)
                            request = row[1].replace('PYCSW_SERVER', url)
                            outfile = '%s%s' % (root.replace(os.sep, '_'),
                            '_%s.xml' % row[0])
                            expected = 'expected%s%s' % (os.sep, outfile)
                            print '\n test %s:%s' % (testfile, row[0])

                            result = http_req('GET', request, request)

                            status = get_validity(expected, result, outfile)

                            if status == 1:
                                print '  passed'
                                passed += 1
                            elif status == 0:
                                print '  initialized'
                                inited += 1
                            else:
                                print '  FAILED'
                                failed += 1

                            if logwriter:
                                logwriter.writerow([url, cfg, testfile,status])

                    else:  # POST requests
                        testfile = '%s%s%s' % (root, os.sep, file)
                        outfile = '%s%s' % (os.sep, testfile.replace(os.sep, '_'))
                        expected = 'expected%s%s' % (os.sep, outfile)
                        print '\n test %s' % testfile
        
                        # read test
                        f = open(testfile)
                        request = f.read()
                        f.close()

                        configkvp = 'config=tester%s%s' % (os.sep, cfg)
                        url2 = '%s?%s' % (url, configkvp)

                        # invoke request
                        result = http_req('POST', url2, request)

                        status = get_validity(expected, result, outfile)

                        if status == 1:
                            print '  passed'
                            passed += 1
                        elif status == 0:
                            print '  initialized'
                            inited += 1
                        else:
                            print '  FAILED'
                            failed += 1
        
                        if logwriter:
                            logwriter.writerow([url, cfg, testfile,status])
    
print '\nResults (%d/%d - %.2f%%)' % \
(passed, passed+failed,float(passed)/float(passed+failed)*100)
print '   %d test%s passed' % (passed, plural(passed))
print '   %d test%s failed' % (failed, plural(failed))
print '   %d test%s initialized' % (inited, plural(inited))
