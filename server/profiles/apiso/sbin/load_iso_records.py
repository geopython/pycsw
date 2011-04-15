#!/usr/bin/python
# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2011 Angelos Tzotsos
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
from owslib.iso import *

if len(sys.argv) < 3:
    print 'Usage: %s <xml directory path> <filename.sqlite3>' % sys.argv[0]
    sys.exit(1)

CONN = sqlite3.connect(sys.argv[2])
CUR = CONN.cursor()

for r in glob.glob(os.path.join(sys.argv[1], '*.xml')):
    # read iso document
    e = etree.parse(r)
    x = etree.parse(r)
    c = MD_Metadata(e)
    
    # prepare some elements for the db
    if c.identification.bbox is None:
        bbox = None
    else:
        bbox = '%s,%s,%s,%s' % \
        (c.identification.bbox.miny, c.identification.bbox.minx, 
        c.identification.bbox.maxy, c.identification.bbox.maxx)
    
    if c.serviceidentification is not None:
        service_type = c.serviceidentification.type
    else:
        service_type = None
    
    publication_date = []
    revision_date = []
    creation_date =[]
    k=0
    for i in c.identification.datetype:
        if i == 'publication':
            if k < len(c.identification.date):
                publication_date.append(c.identification.date[k])
            k = k + 1
        elif i == 'revision':
            if k < len(c.identification.date):
                revision_date.append(c.identification.date[k])
            k = k + 1
        elif i == 'creation':
            if k < len(c.identification.date):
                creation_date.append(c.identification.date[k])
            k = k + 1
        else:
            pass
    
    organization_name=[]
    role = []
    for i in c.contact:
        organization_name.append(i.organization)
        role.append(i.role)
    
    if c.languagecode is not None:
        language = c.languagecode
    else:
        language = c.language
    
    if c.distribution is not None:
        format = c.distribution.format
    else:
        format = None
    
    if c.referencesystem is not None:
        crs=c.referencesystem.code
    else:
        crs = None
    
    alt_title = None
    parent_id = None
    geo_desc_code = c.identification.bbox.description_code
    
    #insert metadata
    print 'Inserting file %s with GUID %s into database %s, table records....' % \
    (r,  c.identifier, sys.argv[2])
    
    values = (
    c.identification.title,
    c.identification.abstract, 
    c.identification.identtype, 
    c.identifier, 
    ','.join(c.identification.topiccategory), 
    service_type, 
    ','.join(c.identification.keywords['list']),
    bbox, 
    ','.join(publication_date), 
    ','.join(revision_date), 
    ','.join(creation_date), 
    ','.join(organization_name), 
    c.dataquality.lineage, 
    ','.join(c.identification.temporalextent_start),
    ','.join(c.identification.temporalextent_end),
    language, 
    ','.join(c.identification.distance),
    ','.join(c.identification.uom),
    ','.join(c.identification.denominators),
    ','.join(c.dataquality.conformancetitle),
    ','.join(c.dataquality.conformancedate),
    ','.join(c.dataquality.conformancedatetype),
    ','.join(c.dataquality.conformancedegree),
    ','.join(c.identification.uselimitation),
    ','.join(c.identification.accessconstraints),
    ','.join(c.identification.classification),
    ','.join(c.identification.otherconstraints),
    ','.join(role),
    'gmd:MD_Metadata', 
    lxml.etree.tostring(x), 
    format, 
    crs, 
    c.datestamp, 
    alt_title, 
    parent_id, 
    ','.join(c.identification.resourcelanguage),
    c.identification.keywords['type'],
    geo_desc_code
    )
    
    CUR.execute(
    'insert into md_metadata values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
    values)

    CONN.commit()

    print 'Done'

CUR.close()
