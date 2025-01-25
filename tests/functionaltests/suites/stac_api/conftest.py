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
            'database': 'sqlite:///tests/functionaltests/suites/stac_api/data/records.db',
            'table': 'records',
        }
    }


@pytest.fixture()
def sample_collection():
    yield {
        'assets': {
            '6072a0ee-0fff-4755-9cc7-660711de9b35': {
                'href': 'https://api.up42.com/v2/assets/6072a0ee-0fff-4755-9cc7-660711de9b35',
                'title': 'Original Delivery',
                'roles': [
                    'data',
                    'original'
                ],
                'type': 'application/zip'
            }
        },
        'links': [
            {
                'rel': 'self',
                'href': 'https://api.up42.dev/catalog/hosts/oneatlas/stac/search'
            }
        ],
        'stac_extensions': [
            'https://api.up42.com/stac-extensions/up42-order/v1.0.0/schema.json'
        ],
        'title': 'ORT_SPOT7_20190922_094920500_000',
        'description': 'High-resolution 1.5m SPOT images acquired daily on a global basis. The datasets are available starting from 2012.',
        'keywords': [
            'berlin',
            'optical'
        ],
        'license': 'proprietary',
        'providers': [
            {
                'name': 'Airbus',
                'roles': [
                    'producer'
                ],
                'url': 'https://www.airbus.com'
            }
        ],
        'extent': {
            'spatial': {
                'bbox': [
                    [
                        -86.07022916666666,
                        11.900145833333333,
                        -86.05072916666667,
                        11.942270833333334
                    ]
                ]
            },
            'temporal': {
                'interval': [
                    [
                        '2017-01-01T00:00:00Z',
                        '2021-12-31T00:00:00Z'
                    ]
                ]
            }
        },
        'stac_version': '1.0.0',
        'type': 'Collection',
        'id': '123e4567-e89b-12d3-a456-426614174000'
    }


@pytest.fixture()
def sample_item():
    yield {
        'id': '20201211_223832_CS2',
        'stac_version': '1.0.0',
        'type': 'Feature',
        'geometry': None,
        'properties': {
            'datetime': '2020-12-11T22:38:32.125000Z'
        },
        'collection': 'simple-collection',
        'links': [{
            'rel': 'collection',
            'href': './collection.json',
            'type': 'application/json',
            'title': 'Simple Example Collection'
        }, {
            'rel': 'root',
            'href': './collection.json',
            'type': 'application/json',
            'title': 'Simple Example Collection'
        }, {
            'rel': 'parent',
            'href': './collection.json',
            'type': 'application/json',
            'title': 'Simple Example Collection'
        }],
        'assets': {
            'visual': {
                'href': 'https://storage.googleapis.com/open-cogs/stac-examples/20201211_223832_CS2.tif',
                'type': 'image/tiff; application=geotiff; profile=cloud-optimized',
                'title': '3-Band Visual',
                'roles': [
                    'visual'
                ]
            },
            'thumbnail': {
                'href': 'https://storage.googleapis.com/open-cogs/stac-examples/20201211_223832_CS2.jpg',
                'title': 'Thumbnail',
                'type': 'image/jpeg',
                'roles': [
                    'thumbnail'
                ]
            }
        }
    }


@pytest.fixture()
def sample_item_collection():
    yield {
        'type': 'FeatureCollection',
        'features': [{
            'id': '20201211_223832_CS2',
            'stac_version': '1.0.0',
            'type': 'Feature',
            'geometry': None,
            'properties': {
                'datetime': '2020-12-11T22:38:32.125000Z'
            },
            'collection': 'simple-collection',
            'links': [{
                'rel': 'collection',
                'href': './collection.json',
                'type': 'application/json',
                'title': 'Simple Example Collection'
            }, {
                'rel': 'root',
                'href': './collection.json',
                'type': 'application/json',
                'title': 'Simple Example Collection'
            }, {
                'rel': 'parent',
                'href': './collection.json',
                'type': 'application/json',
                'title': 'Simple Example Collection'
            }],
            'assets': {
                'visual': {
                    'href': 'https://storage.googleapis.com/open-cogs/stac-examples/20201211_223832_CS2.tif',
                    'type': 'image/tiff; application=geotiff; profile=cloud-optimized',
                    'title': '3-Band Visual',
                    'roles': [
                        'visual'
                    ]
                },
                'thumbnail': {
                    'href': 'https://storage.googleapis.com/open-cogs/stac-examples/20201211_223832_CS2.jpg',
                    'title': 'Thumbnail',
                    'type': 'image/jpeg',
                    'roles': [
                        'thumbnail'
                    ]
                }
            }
        }, {
            'id': '20201212_223832_CS2',
            'stac_version': '1.0.0',
            'type': 'Feature',
            'geometry': None,
            'properties': {
                'datetime': '2020-12-12T22:38:32.125000Z'
            },
            'collection': 'simple-collection',
            'links': [{
                'rel': 'collection',
                'href': './collection.json',
                'type': 'application/json',
                'title': 'Simple Example Collection'
            }, {
                'rel': 'root',
                'href': './collection.json',
                'type': 'application/json',
                'title': 'Simple Example Collection'
            }, {
                'rel': 'parent',
                'href': './collection.json',
                'type': 'application/json',
                'title': 'Simple Example Collection'
            }],
            'assets': {
                'visual': {
                    'href': 'https://storage.googleapis.com/open-cogs/stac-examples/20201211_223832_CS2.tif',
                    'type': 'image/tiff; application=geotiff; profile=cloud-optimized',
                    'title': '3-Band Visual',
                    'roles': [
                        'visual'
                    ]
                },
                'thumbnail': {
                    'href': 'https://storage.googleapis.com/open-cogs/stac-examples/20201211_223832_CS2.jpg',
                    'title': 'Thumbnail',
                    'type': 'image/jpeg',
                    'roles': [
                        'thumbnail'
                    ]
                }
            }
        }]
    }
