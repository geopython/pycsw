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

sys.path.append('/home/tkralidi/foss4g/OWSLib/trunk')
from owslib.csw import CswRecord

if len(sys.argv) < 2:
    print 'Usage: %s <filename.sqlite3> <directory>' % sys.argv[0]
    sys.exit(1)

conn = sqlite3.connect(sys.argv[1])
cur = conn.cursor()

for r in glob.glob(os.path.join('..','data','cite','*.xml')):

    # read dc document
    e=etree.parse(r)
    c=CswRecord(e)

    if c.bbox is None:
        bbox = None
    else:
        #bbox = '%s,%s,%s,%s' % (c.bbox.minx,c.bbox.miny,c.bbox.maxx,c.bbox.maxy)
        bbox = '%s,%s,%s,%s' % (c.bbox.miny,c.bbox.minx,c.bbox.maxy,c.bbox.maxx)

    print 'Inserting csw:Record %s into database %s, table records....' % (c.identifier, sys.argv[1])

    sql = '''insert into records values(
'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')''' % (
    c.title,
    c.creator,
    ','.join(c.subjects),
    c.abstract,
    c.publisher,
    c.contributor,
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
    etree.tostring(e)
    )

    cur.execute(sql)

    conn.commit()

    print 'Done'
cur.close()

