#!/usr/bin/python
# -*- coding: ISO-8859-15 -*-
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

import os
import sys
import glob

from lxml import etree
from server import repository, util
from owslib.csw import CswRecord
from owslib.iso import MD_Metadata

if len(sys.argv) < 3:
    print 'Usage: %s <xml directory path> <db_connection_string>' % sys.argv[0]
    sys.exit(1)

REPO = repository.Repository(sys.argv[2], 'records', {})

for r in glob.glob(os.path.join(sys.argv[1], '*.xml')):
    print 'Processing file %s' % r
    # read document

    try:
        e = etree.parse(r)
    except Exception, err:
        print 'XML document is not well-formed: %s' % str(err)
        continue

    value = e.getroot().tag

    if value == '{http://www.opengis.net/cat/csw/2.0.2}Record':
        typename = 'csw:Record'
        schema = 'http://www.opengis.net/cat/csw/2.0.2'
        c = CswRecord(e)

        if c.bbox is None:
            bbox = None
        else:
            bbox = c.bbox
    elif value == '{http://www.isotc211.org/2005/gmd}MD_Metadata':
        typename = 'gmd:MD_Metadata'
        schema = 'http://www.isotc211.org/2005/gmd'
        c = MD_Metadata(e)

        if hasattr(c.identification, 'bbox') and c.identification.bbox:
            bbox = c.identification.bbox
        else:
            bbox = None

    if bbox is not None:
        tmp = '%s,%s,%s,%s' % (bbox.miny, bbox.minx, bbox.maxy, bbox.maxx)
        bbox = util.bbox2wktpolygon(tmp) 

    RECORD = {}
    RECORD['identifier'] = c.identifier
    RECORD['typename'] = typename
    RECORD['schema'] = schema
    RECORD['bbox'] = bbox
    RECORD['xml'] = c.xml
    RECORD['source'] = 'local'
    RECORD['insert_date'] = util.get_today_and_now()

    print 'Inserting %s %s into database %s, table records....' % \
    (typename, c.identifier, sys.argv[2])

    try:
        REPO.insert(RECORD)
        print 'Inserted'
    except Exception, err:
        print 'ERROR: not inserted' % str(err)

print 'Done'
