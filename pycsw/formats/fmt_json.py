# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2012 Tom Kralidis
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

import json
from pycsw.util import xmltag_split, xmltag_split2

def _exml2dict(element, namespaces):
    ''' Convert an lxml object to a dict
        From:
        https://bitbucket.org/smulloni/pesterfish/src/1578db946d74/pesterfish.py
    '''
   
    d = dict(tag='%s%s' % \
    (xmltag_split2(element.tag, namespaces, True), xmltag_split(element.tag)))
    if element.text:
        if element.text.find('\n') == -1:
            d['text'] = element.text
    if element.attrib:
        d['attributes'] = dict(('%s%s' %(xmltag_split2(k, namespaces, True), \
        xmltag_split(k)),f(v) if hasattr(v, 'keys') else v) \
        for k,v in element.attrib.items())
    children = element.getchildren()
    if children:
        d['children'] = map(lambda x: _exml2dict(x, namespaces), children)
    return d

def exml2json(response, namespaces, pretty_print=False):
    ''' Convert an lxml object to JSON '''
    if pretty_print:
        return json.dumps(_exml2dict(response, namespaces), indent=4)
    return json.dumps(_exml2dict(response, namespaces))
