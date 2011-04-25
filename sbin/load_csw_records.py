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
import sqlite3

from lxml import etree
from server import util
from owslib.csw import CswRecord

if len(sys.argv) < 3:
    print 'Usage: %s <xml directory path> <filename.sqlite3>' % sys.argv[0]
    sys.exit(1)

CONN = sqlite3.connect(sys.argv[2])
CUR = CONN.cursor()

for r in glob.glob(os.path.join(sys.argv[1], '*.xml')):

    # read dc document
    e = etree.parse(r)
    c = CswRecord(e)

    if c.bbox is None:
        bbox = None
    else:
        tmp = '%s,%s,%s,%s' % \
        (c.bbox.miny, c.bbox.minx, c.bbox.maxy, c.bbox.maxx)
        bbox = util.bbox2wktpolygon(tmp) 

    print 'Inserting csw:Record %s into database %s, table records....' % \
    (c.identifier, sys.argv[2])

    values = (
    c.title,
    c.creator,
    ','.join(c.subjects),
    c.abstract,
    c.publisher,
    c.contributor,
    c.modified,
    c.date,
    c.type,
    c.format,
    c.identifier,
    c.source,
    c.language,
    c.relation,
    bbox,
    ','.join(c.rights),
    'csw:Record',
    c.xml
    )

    CUR.execute(
    'insert into records values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,null,null)',
    values)

    CONN.commit()

    print 'Done'
CUR.close()
