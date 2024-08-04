# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <gcpp.kalxas@gmail.com>
#
# Copyright (c) 2023 Tom Kralidis
# Copyright (c) 2022 Angelos Tzotsos
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

import pytest

from pycsw.stac.api import STACAPI

pytestmark = pytest.mark.functional


def test_landing_page(config):
    api = STACAPI(config)
    headers, status, content = api.landing_page({}, {'f': 'json'})
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/json'
    assert status == 200
    assert len(content['links']) == 8

    assert content['stac_version'] == '1.0.0'
    assert content['type'] == 'Catalog'
    assert len(content['conformsTo']) == 15
    assert len(content['keywords']) == 3


def test_openapi(config):
    api = STACAPI(config)
    headers, status, content = api.openapi({}, {'f': 'json'})
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/vnd.oai.openapi+json;version=3.0'  # noqa
    assert status == 200


def test_conformance(config):
    api = STACAPI(config)
    headers, status, content = api.conformance({}, {})
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/json'
    assert status == 200

    assert len(content['conformsTo']) == 15

    conformances = [
        'https://api.stacspec.org/v1.0.0/core',
        'https://api.stacspec.org/v1.0.0/ogcapi-features',
        'https://api.stacspec.org/v1.0.0/item-search',
        'https://api.stacspec.org/v1.0.0/item-search#filter'
    ]

    for conformance in conformances:
        assert conformance in content['conformsTo']


def test_collections(config):
    api = STACAPI(config)
    headers, status, content = api.collections({}, {'f': 'json'})
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/json'
    assert status == 200
    assert len(content['links']) == 3

    assert len(content['collections']) == 1
    assert len(content['collections']) == content['numberMatched']
    assert len(content['collections']) == content['numberReturned']

def test_queryables(config):
    api = STACAPI(config)
    headers, status, content = api.queryables({}, {})
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/schema+json'
    assert content['type'] == 'object'
    assert content['title'] == 'pycsw Geospatial Catalogue'
    assert content['$id'] == 'http://localhost/pycsw/oarec/stac/collections/metadata:main/queryables'  # noqa
    assert content['$schema'] == 'http://json-schema.org/draft/2019-09/schema'

    assert len(content['properties']) == 13

    assert 'geometry' in content['properties']
    assert content['properties']['geometry']['$ref'] == 'https://geojson.org/schema/Polygon.json'  # noqa

    headers, status, content = api.queryables({}, {}, collection='foo')
    assert status == 400


def test_items(config):
    api = STACAPI(config)
    headers, status, content = api.items({}, None, {})
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/json'
    assert status == 200

    assert content['type'] == 'FeatureCollection'

    record = content['features'][0]

    assert record['stac_version'] == '1.0.0'
    assert record['collection'] == 'metadata:main'

    # test GET KVP requests
    content = json.loads(api.items({}, None, {'bbox': '-180,-90,180,90'})[2])
    assert len(content['features']) == 3

    content = json.loads(api.items({}, None, {'datetime': '2006-03-26'})[2])
    assert len(content['features']) == 1

    content = json.loads(api.items({}, None,
                                   {'bbox': '-180,-90,180,90',
                                   'datetime': '2006-03-26'})[2])
    assert len(content['features']) == 1

    content = json.loads(api.items({}, None, {'sortby': 'title'})[2])

    assert len(content['features']) == 10
    assert content['features'][5]['properties']['title'] == 'Lorem ipsum'

    content = json.loads(api.items({}, None, {'sortby': '-title'})[2])

    assert len(content['features']) == 10
    assert content['features'][5]['properties']['title'] == 'Lorem ipsum dolor sit amet'  # noqa

    params = {'filter': "title LIKE '%%Lorem%%'"}
    content = json.loads(api.items({}, None, params)[2])
    assert content['numberMatched'] == 2
    assert content['numberReturned'] == 2
    assert len(content['features']) == content['numberReturned']

    params = {'filter': "title LIKE '%%Lorem%%'", 'q': 'iPsUm'}
    content = json.loads(api.items({}, None, params)[2])
    assert content['numberMatched'] == 2
    assert content['numberReturned'] == 2
    assert len(content['features']) == content['numberReturned']

    # test POST JSON requests
    content = json.loads(api.items({}, {'bbox': [-180, -90, 180, 90]}, {})[2])
    assert len(content['features']) == 3

    content = json.loads(api.items({},
                                   {'bbox': [-180, -90, 180, 90], 'datetime': '2006-03-26'},  # noqa
                                   {})[2])
    assert len(content['features']) == 1

    content = json.loads(api.items({}, {'datetime': '2006-03-26'}, {})[2])
    assert len(content['features']) == 1

    content = json.loads(api.items({},
                                   {'sortby': [{'field': 'title', 'direction': 'asc'}]},  # noqa
                                   {})[2])

    assert len(content['features']) == 10
    assert content['features'][5]['properties']['title'] == 'Lorem ipsum'

    content = json.loads(api.items({},
                                   {'sortby': [{'field': 'title', 'direction': 'desc'}]},  # noqa
                                   {})[2])
    assert len(content['features']) == 10
    assert content['features'][5]['properties']['title'] == 'Lorem ipsum dolor sit amet'  # noqa

    headers, status, content = api.items({}, None, {}, 'foo')
    assert status == 400


def test_item(config):
    api = STACAPI(config)
    item = 'urn:uuid:19887a8a-f6b0-4a63-ae56-7fba0e17801f'
    headers, status, content = api.item({}, {}, 'metadata:main', item)
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/geo+json'
    assert status == 200

    assert content['id'] == item
    assert content['stac_version'] == '1.0.0'
    assert content['collection'] == 'metadata:main'

    headers, status, content = api.item({}, {}, 'foo', item)
    assert status == 400
