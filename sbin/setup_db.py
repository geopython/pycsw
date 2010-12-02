#!/usr/bin/python

import sys
import urllib2
import sqlite3

if len(sys.argv) < 2:
    print 'Usage: %s <filename.sqlite3>' % sys.argv[0]
    sys.exit(1)

conn = sqlite3.connect(sys.argv[1])
cursor = conn.cursor()

# get EPSG:4326 as WKT
wkt4326 = urllib2.urlopen('http://www.spatialreference.org/ref/epsg/4326/ogcwkt/').read().strip()

# create OGC SFSQL database
cursor.execute('''
    create table spatial_ref_sys (
        srid integer unique,
        auth_name text,
        auth_srid integer,
        srtext text)''')

cursor.execute('''
    insert into spatial_ref_sys values
        (4326, 'EPSG', 4326, '%s')''' % wkt4326)

cursor.execute('''
    create table geometry_columns (
        f_table_name text,
        f_geometry_column text,
        geometry_type integer,
        coord_dimension integer,
        srid integer, geometry_format text )''')

cursor.execute('''
    insert into geometry_columns values
        ('pycsw', 'wkt_geometry', 'POLYGON', 2, 4326, 'WKT')''')

cursor.execute('''
    create table pycsw (
        id integer primary key autoincrement,
        uuid text,
        type text,
        title text,
        abstract text,
        keywords text,
        schema text,
        metadata text,
        date text,
        wkt_geometry text)''')

conn.commit()
cursor.close()
