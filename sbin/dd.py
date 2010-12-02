#!/usr/bin/python

import sys
import glob
import sqlite3
from lxml import etree

sys.path.append('/home/tkralidi/foss4g/OWSLib/trunk')

from owslib.csw import CswRecord



def bbox2wkt(bbox):
    if isinstance(bbox, tuple) is False:  # rogue value, set to global bbox
        return 'POLYGON((-180 -90, -180 90, 180 90, 180 -90, -180 -90))'
    else:
        return \
            'POLYGON((%.2f %.2f, %.2f %.2f, %.2f %.2f, %.2f %.2f, %.2f %.2f))' \
            % (bbox.minx, bbox.miny, bbox.minx, bbox.maxy, bbox.maxx, bbox.maxy, bbox.maxx, \
            bbox.miny, bbox.minx, bbox.miny)

conn = sqlite3.connect('../data/foo.db')
cursor = conn.cursor()

i = 0
for f in glob.glob('../data/ogc/cite/*.xml'):
    metadata = open(f).read()
    e = etree.fromstring(metadata)
    c = CswRecord(e)
    cursor.execute('''insert into pycsw values(%d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s') ''' % (i, c.identifier, c.type, c.title, c.abstract, ','.join(c.subjects), 'http://www.opengis.net/cat/csw/2.0.2', etree.tostring(e), c.modified, bbox2wkt(c.bbox)))
    i +=1

conn.commit()
cursor.close()
