# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
# Copyright (c) 2017 Ricardo Garcia Silva
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

import xmltodict


def xml2dict(xml_string, namespaces):
    """Convert an xml document to a dictionary.

    Parameters
    ----------
    xml_string: str
        XML representation to convert to a dictionary.
    namespaces: dict
        Namespaces used in the ``xml_string`` parameter

    Returns
    -------
    ordereddict
        An ordered dictionary with the contents of the xml data

    """

    namespaces_reverse = dict((v, k) for k, v in namespaces.items())
    return xmltodict.parse(xml_string, process_namespaces=True,
                           namespaces=namespaces_reverse)


def xml2json(xml_string, namespaces, pretty_print=False):
    """Convert an xml string to JSON"""

    separators = (',', ': ')

    if pretty_print:
        return json.dumps(xml2dict(xml_string, namespaces),
                          indent=4, separators=separators)

    return json.dumps(xml2dict(xml_string, namespaces), separators=separators)
