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

# generate internal database

import os
import sys
import sqlite3

if len(sys.argv) < 3:
    print 'Usage: %s <ddl file> <filename.sqlite3>' % sys.argv[0]
    sys.exit(1)

WKT4326 = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'

CONN = sqlite3.connect(sys.argv[2])
CURSOR = CONN.cursor()

# create OGC SFSQL database
CURSOR.execute('''
    create table spatial_ref_sys (
        srid integer unique,
        auth_name text,
        auth_srid integer,
        srtext text)''')

CURSOR.execute('''
    insert into spatial_ref_sys values
        (4326, 'EPSG', 4326, '%s')''' % WKT4326)

CURSOR.execute('''
    create table geometry_columns (
        f_table_name text,
        f_geometry_column text,
        geometry_type integer,
        coord_dimension integer,
        srid integer, geometry_format text )''')

CURSOR.execute('''
    insert into geometry_columns values
        ('records', 'bbox', 'POLYGON', 2, 4326, 'WKT')''')

CURSOR.execute('''
    insert into geometry_columns values
        ('md_metadata', 'bbox', 'POLYGON', 2, 4326, 'WKT')''')

CURSOR.executescript(open(sys.argv[1]).read())

CONN.commit()
CURSOR.close()
