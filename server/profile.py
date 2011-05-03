# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#                Angelos Tzotsos <tzotsos@gmail.com>
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

class Profile(object):
    ''' base Profile class '''
    def __init__(self, name, version, title, url,
    namespace, typename, outputschema):
        ''' Initialize profile '''
        self.name = name
        self.version = version
        self.title = title
        self.url = url
        self.namespace = namespace
        self.typename = typename
        self.outputschema = outputschema
        self.corequeryables = None

    def extend_core(self, model, namespaces):
        ''' Extend config.MODEL and config.NAMESPACES '''
        raise NotImplementedError

    def check_parameter(self):
        ''' Perform extra parameters checking.
            Return or dict with keys "locator", "code", "text" or None ''' 
        raise NotImplementedError

    def get_extendedcapabilities(self):
        ''' Return ExtendedCapabilities child as lxml.etree.Element '''
        raise NotImplementedError

    def get_schemacomponents(self):
        ''' Return schema components as lxml.etree.Element list '''
        raise NotImplementedError
    
    def check_getdomain(self, kvp):
        '''Perform extra profile specific checks in the GetDomain request'''
        raise NotImplementedError

    def write_record(self):
        ''' Return csw:SearchResults child as lxml.etree.Element '''
        raise NotImplementedError

def load_profiles(path, cls, profiles):
    ''' load CSW profiles, return dict by class name ''' 

    def look_for_subclass(modulename):
        module = __import__(modulename)
 
        dmod = module.__dict__
        for modname in modulename.split('.')[1:]:
            dmod = dmod[modname].__dict__
 
        for key, entry in dmod.items():
            if key == cls.__name__:
                continue
 
            try:
                if issubclass(entry, cls):
                    aps['plugins'][key] = entry
            except TypeError:
                continue
 
    aps = {}
    aps['plugins'] = {}
    aps['loaded'] = {}
 
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.endswith('.py') and not name.startswith('__') and \
                root.find('sbin') == -1 and name.split('.')[0] in profiles:
                path = os.path.join(root, name)
                modulename = path.rsplit('.', 1)[0].replace('/', '.')
                look_for_subclass(modulename)
 
    return aps
