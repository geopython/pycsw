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

version = open('VERSION.txt').read().strip()

ogc_schemas_base = 'http://schemas.opengis.net'

namespaces = {
    'csw': 'http://www.opengis.net/cat/csw/2.0.2',
    'dc' : 'http://purl.org/dc/elements/1.1/',
    'dct': 'http://purl.org/dc/terms/',
    'gml': 'http://www.opengis.net/gml',
    'ogc': 'http://www.opengis.net/ogc',
    'ows': 'http://www.opengis.net/ows',
    'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
    'soapenv': 'http://www.w3.org/2003/05/soap-envelope',
    'xlink': 'http://www.w3.org/1999/xlink',
    'xs': 'http://www.w3.org/2001/XMLSchema',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

model =  {
    'operations': {
        'GetCapabilities': {
            'methods': {
                'get': True,
                'post': True,
            },
            'parameters': {
                'sections': {
                    'values': ['ServiceIdentification', 'ServiceProvider', 'OperationsMetadata', 'Filter_Capabilities']
                }
            }
        },
        'DescribeRecord': {
            'methods': {
                'get': True,
                'post': True,
            },
            'parameters': {
                'schemaLanguage': {
                    #'values': ['XMLSCHEMA']
                    #'values': ['http://www.w3.org/XML/Schema']
                    'values': ['http://www.w3.org/XML/Schema', 'http://www.w3.org/TR/xmlschema-1/']
                },
                'typeName': {
                    'values': ['csw:Record']
                },
                'outputFormat': {
                    'values': ['application/xml']
                }
            }
        },
        'GetRecords': {
            'methods': {
                'get': True,
                'post': True,
            },
            'parameters': {
                'resultType': {
                    'values': ['hits', 'results', 'validate']
                },
                'typeNames': {
                    'values': ['csw:Record']
                },
                'outputSchema': {
                    'values': ['http://www.opengis.net/cat/csw/2.0.2']
                },
                'outputFormat': {
                    'values': ['application/xml']
                },
                'CONSTRAINTLANGUAGE': {
                    'values': ['FILTER', 'CQL_TEXT']
                },
                'ElementSetName': {
                    'values': ['brief','summary','full']
                }
            }
        },
        'GetRecordById': {
            'methods': {
                'get': True,
                'post': True,
            },
            'parameters': {
                'resultType': {
                    'values': ['hits', 'results', 'validate']
                },
                'typeNames': {
                    'values': ['csw:Record']
                },
                'outputSchema': {
                    'values': ['http://www.opengis.net/cat/csw/2.0.2']
                },
                'outputFormat': {
                    'values': ['application/xml']
                },
                'ElementSetName': {
                    'values': ['brief','summary','full']
                }
            }
        }
    },
    'parameters': {
        'version': { 
            'values': ['2.0.2']
        },
        'service': {
            'values': ['http://www.opengis.net/cat/csw/2.0.2']
        }
    },
    'constraints': {
        'PostEncoding': {
            'values': ['XML', 'SOAP']
        }
    }
}

def gen_domains():
    d = {}
    d['methods'] = {}
    d['methods']['get'] = True
    d['methods']['post'] = True
    d['parameters'] = {}
    d['parameters']['ParameterName'] = {}
    d['parameters']['ParameterName']['values'] = []
    for o in model['operations'].keys():
        for p in model['operations'][o]['parameters']:
            d['parameters']['ParameterName']['values'].append('%s.%s' % (o, p))
    return d

def get_config(file):
    import ConfigParser
    if file is not None:
        cp = ConfigParser.SafeConfigParser()
        cp.optionxform = str
        cp.readfp(open(file))

    config = {}
    for i in cp.sections():
        s = i.lower()
        config[s] = {}
        for j in cp.options(i):
            config[s][j] = unicode(cp.get(i,j).decode('latin-1')).strip()
    return config
