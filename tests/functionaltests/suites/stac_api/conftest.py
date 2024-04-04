# =================================================================
#
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#          Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2023 Ricardo Garcia Silva
# Copyright (c) 2024 Tom Kralidis
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

import pytest


@pytest.fixture()
def config():
    yield {
        'server': {
            'url': 'http://localhost/pycsw/oarec',
            'mimetype': 'application/xml;',
            'charset': 'UTF-8',
            'encoding': 'UTF-8',
            'language': 'en-US',
            'maxrecords': '10',
            'gzip_compresslevel': '9',
            'profiles': [
                'apiso'
            ]
        },
        'logging': {
            'level': 'ERROR',
        },
        'manager': {
            'transactions': True,
            'allowed_ips': '127.0.0.1'
        },
        'metadata': {
            'identification': {
                'title': 'pycsw Geospatial Catalogue',
                'description': 'pycsw is an OARec and OGC CSW server implementation written in Python',
                'keywords': [
                    'catalogue',
                    'discovery',
                    'metadata'
                ],
                'keywords_type': 'theme',
                'fees': 'None',
                'accessconstraints': 'None'
            },
            'provider': {
                'name': 'Organization Name',
                'url': 'https://pycsw.org/',
            },
            'contact': {
                'name': 'Lastname, Firstname',
                'position': 'Position Title',
                'address': 'Mailing Address',
                'city': 'City',
                'stateorprovince': 'Administrative Area',
                'postalcode': 'Zip or Postal Code',
                'country': 'Country',
                'phone': '+xx-xxx-xxx-xxxx',
                'fax': '+xx-xxx-xxx-xxxx',
                'email': 'you@example.org',
                'url': 'Contact URL',
                'hours': 'Hours of Service',
                'instructions': 'During hours of service.  Off on weekends.',
                'role': 'pointOfContact',
            },
            'inspire': {
                'enabled': True,
                'languages_supported': [
                    'eng',
                    'gre'
                ],
                'default_language': 'eng',
                'date': 'YYYY-MM-DD',
                'gemet_keywords': 'Utility and governmental services',
                'conformity_service': 'notEvaluated',
                'contact_name': 'Organization Name',
                'contact_email': 'you@example.org',
                'temp_extent': {
                    'begin': 'YYYY-MM-DD/YYYY-MM-DD',
                    'end': 'YYYY-MM-DD/YYYY-MM-DD'
                }
            }
        },
        'repository': {
            'database': 'sqlite:///tests/functionaltests/suites/cite/data/cite.db',
            'table': 'records',
        }
    }
