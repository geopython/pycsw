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

version = '0.0.1'

namespaces = {
    #None : 'http://www.opengis.net/cat/csw/2.0.2',
    'csw': 'http://www.opengis.net/cat/csw/2.0.2',
    'dc' : 'http://purl.org/dc/elements/1.1/',
    'dct': 'http://purl.org/dc/terms/',
    'gml': 'http://www.opengis.net/gml',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'ogc': 'http://www.opengis.net/ogc',
    'ows': 'http://www.opengis.net/ows',
    'xlink': 'http://www.w3.org/1999/xlink',
    'xs': 'http://www.w3.org/2001/XMLSchema',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

model =  {
    'operations': {
        'GetCapabilities': {
            'parameters': {
                'sections': {
                    'values': ['ServiceIdentification', 'ServiceProvider', 'OperationsMetadata', 'FilterCapabilities']
                }
            }
        },
        'DescribeRecord': {
            'parameters': {
                'schemaLanguage': {
                    #'values': ['XMLSCHEMA']
                    'values': ['http://www.w3.org/XML/Schema']
                }
            }
        },
        'GetRecords': {
            'parameters': {
                'resultType': {
                    'values': ['hits', 'results', 'validate']
                }
            }
        },
        'GetRecordById': {
            'parameters': {
            }
        }
    },
    'parameters': {
        'version': { 
            'values': ['2.0.2']
        },
        'service': {
            'values': ['CSW']
        }
    },
    'constraints': {
        'PostEncoding': {
            'values': ['XML']
        },
        'outputFormat': {
            'values': ['application/xml']
        },
        'outputSchema': {
            'values': ['http://www.opengis.net/cat/csw/2.0.2', 'http://www.isotc211.org/2005/gmd']
        },
        'TypeNames': {
            'values': ['csw:Record','gmd:MD_Metadata']
        },
        'ElementSetName': {
            'values': ['brief', 'summary', 'full']
        }
    }
}

mappings = {
    'dc:identifier': 'dataset_identifier',
    'dc:title': 'dataset_title',
    'dc:format': 'dataset_format',
    'dc:relation': 'dataset_relation',
    'dc:date': 'dataset_date',
    'dc:subject': 'dataset_subject_list',
    'dct:abstract': 'dataset_abstract',
    'dc:type': 'dataset_type',
    'csw:AnyText': 'dataset_metadata',
    '/ows:BoundingBox': 'dataset_bbox',
    'ows:BoundingBox': 'dataset_bbox'
}

def get_config(file):
    import ConfigParser
    if file is not None:
        cp = ConfigParser.SafeConfigParser()
        cp.readfp(open(file))

    config = {}
    for i in cp.sections():
        s = i.lower()
        config[s] = {}
        for j in cp.options(i):
            k = j.lower()
            config[s][k] = unicode(cp.get(i,j).decode('latin-1')).strip()
    return config
