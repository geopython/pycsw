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

# generate an XML sitemap from all records in repository

from lxml import etree
from server import config, repository, util

# get configuration and init repo connection
cfg = config.get_config('default.cfg')
repo = repository.Repository(cfg['repository']['db'], cfg['repository']['records_table'])

# get all records
records = repo.query()

# write out sitemap document
urlset = etree.Element(util.nspath_eval('sitemap:urlset'), nsmap=config.namespaces)
urlset.attrib[util.nspath_eval('xsi:schemaLocation')] = '%s http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd' % config.namespaces['sitemap']

for rec in records:
    url = etree.SubElement(urlset,util.nspath_eval('sitemap:url'))
    uri = '%s?service=CSW&version=2.0.2&request=GetRecordById&id=%s&elementsetname=full' % (cfg['server']['url'], rec.identifier)
    etree.SubElement(url, util.nspath_eval('sitemap:loc')).text = uri

# to stdout
print etree.tostring(urlset, pretty_print=1, encoding=cfg['server']['encoding'], xml_declaration=1)
