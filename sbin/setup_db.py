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

import sys
from server import config
from sqlalchemy import Column, create_engine, Integer, String, MetaData, Table, text

if len(sys.argv) < 2:
    print 'Usage: %s <db_connection_string>' % sys.argv[0]
    sys.exit(1)

DB = create_engine(sys.argv[1])

METADATA = MetaData(DB)

SRS = Table('spatial_ref_sys', METADATA,
    Column('srid', Integer, nullable=False, primary_key=True),
    Column('auth_name', String(256)),
    Column('auth_srid', Integer),
    Column('srtext', String(2048)),
)
SRS.create()

GEOM = Table('geometry_columns', METADATA,
    Column('f_table_name', String(256), nullable=False),
    Column('f_geometry_column', String(256), nullable=False),
    Column('geometry_type', String(30), nullable=False),
    Column('coord_dimension', Integer, nullable=False),
    Column('srid', Integer, nullable=False),
    Column('geometry_format', String),
)
GEOM.create()

RECORDS = Table('records', METADATA,
    Column('identifier', String(256), nullable=False, primary_key=True),
    Column('typename', String(32), default='csw:Record', nullable=False),
    Column('schema', String(256),
    default='http://www.opengis.net/cat/csw/2.0.2', nullable=False),
    Column('bbox', String),
    Column('xml', String, nullable=False),
    Column('source', String, default='local', nullable=False),
    Column('insert_date', String, nullable=False),
)
RECORDS.create()

i = SRS.insert()
i.execute(srid=4326, auth_name='EPSG', auth_srid=4326, srtext='GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]')

i = GEOM.insert()
i.execute(f_table_name='records', f_geometry_column='bbox', 
geometry_type='POLYGON', coord_dimension=2, srid=4326, geometry_format='WKT')

if DB.name == 'postgresql':  # create plpythonu functions within db

    CFG = config.get_config('default.cfg')
    CONN = DB.connect()
    FUNCTION_QUERY_XPATH = '''
CREATE OR REPLACE FUNCTION query_xpath(xml text, xpath text)
RETURNS text
AS $$
    import sys
    sys.path.append('%s')
    from server import util
    return util.query_xpath(xml, xpath)
    $$ LANGUAGE plpythonu;
''' % CFG['server']['home']

    FUNCTION_QUERY_SPATIAL = '''
CREATE OR REPLACE FUNCTION query_spatial(bbox_data_wkt text, bbox_input_wkt text, predicate text, distance text)
RETURNS text
AS $$
    import sys
    sys.path.append('%s')
    from server import util
    return util.query_spatial(bbox_data_wkt, bbox_input_wkt, predicate, distance)
    $$ LANGUAGE plpythonu;
''' % CFG['server']['home']

    FUNCTION_QUERY_ANYTEXT = '''
CREATE OR REPLACE FUNCTION query_anytext(xml text, searchterm text)
RETURNS text
AS $$
    import sys
    sys.path.append('%s')
    from server import util
    return util.query_anytext(xml, searchterm)
    $$ LANGUAGE plpythonu;
''' % CFG['server']['home']

    FUNCTION_UPDATE_XPATH = '''
CREATE OR REPLACE FUNCTION update_xpath(xml text, recprops text)
RETURNS text
AS $$
    import sys
    sys.path.append('%s')
    from server import util
    return util.update_xpath(xml, recprops)
    $$ LANGUAGE plpythonu;
''' % CFG['server']['home']

    CONN.execute(FUNCTION_QUERY_XPATH)
    CONN.execute(FUNCTION_QUERY_SPATIAL)
    CONN.execute(FUNCTION_QUERY_ANYTEXT)
    CONN.execute(FUNCTION_UPDATE_XPATH)

