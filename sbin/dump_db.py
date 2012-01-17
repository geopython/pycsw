#!/usr/bin/python
# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2012 Tom Kralidis
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

import os
import sys

from server import repository

if len(sys.argv) < 3:
    print 'Usage: %s <output_dir> <db_connection_string>' % sys.argv[0]
    sys.exit(1)

REPO = repository.Repository(sys.argv[2], 'records', {})

print 'Querying database %s, table records....' % sys.argv[2]

RECORDS = REPO.session.query(REPO.dataset)

print 'Found %d records\n' % RECORDS.count()

for record in RECORDS.all():
    print 'Processing %s' % record.identifier
    if record.identifier.find(':') != -1:  # it's a URN
        # sanitize identifier
        print ' Sanitizing identifier'
        identifier = record.identifier.split(':')[-1]
    else:
        identifier = record.identifier

    # write to XML document
    FILENAME = os.path.join(sys.argv[1], '%s.xml' % identifier)
    try:
        print ' Writing to file %s' % FILENAME
        with open(FILENAME, 'w') as XML:
            XML.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            XML.write(record.xml)
    except Exception, err:
        raise RuntimeError("Error writing to %s" % FILENAME, err)

print 'Done'
