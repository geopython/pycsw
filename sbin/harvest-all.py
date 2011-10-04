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

# harvest all non-local records in repository

import ConfigParser
from lxml import etree
from server import config, repository, util
from owslib.csw import CatalogueServiceWeb

# get configuration and init repo connection
CFG = ConfigParser.SafeConfigParser()
CFG.readfp(open('default.cfg'))
REPOS = repository.Repository(CFG.get('repository', 'database'), 'records',
config.MODEL['typenames'])

# get all harvested records
COUNT, RECORDS = REPOS.query(constraint={'where': 'source != "local"'})

CSW = CatalogueServiceWeb(CFG.get('server', 'url'))

for rec in RECORDS:
    print 'Harvesting %s (identifier = %s) ...' % (rec.source, rec.identifier)
    # TODO: find a smarter way of catching this
    schema = rec.schema
    if schema == 'http://www.isotc211.org/2005/gmd':
        schema = 'http://www.isotc211.org/schemas/2005/gmd/'
    CSW.harvest(rec.source, schema)
    print CSW.response

print 'Done'
