# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <gcpp.kalxas@gmail.com>
#
# Copyright (c) 2025 Tom Kralidis
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
    assert len(content['conformsTo']) == 21
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

    assert len(content['conformsTo']) == 21

    conformances = [
        'http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/simple-query',
        'https://api.stacspec.org/v1.0.0/core',
        'https://api.stacspec.org/v1.0.0/ogcapi-features',
        'https://api.stacspec.org/v1.0.0/item-search',
        'https://api.stacspec.org/v1.0.0/item-search#filter',
        'https://api.stacspec.org/v1.0.0/item-search#sort',
        'https://api.stacspec.org/v1.0.0-rc.1/collection-search',
        'https://api.stacspec.org/v1.0.0-rc.1/collection-search#free-text'
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

    assert len(content['collections']) == 4
    assert len(content['collections']) == content['numberMatched']
    assert len(content['collections']) == content['numberReturned']

    headers, status, content = api.collections({}, {'limit': 0, 'f': 'json'})
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/json'
    assert status == 200
    assert len(content['collections']) == 0


def test_collection(config):
    api = STACAPI(config)
    headers, status, content = api.collection({}, {'f': 'json'}, 'simple-collection')  # noqa
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/json'
    assert status == 200
    assert len(content['links']) == 4

    assert content['id'] == 'simple-collection'
    assert content['title'] == 'Simple Example Collection'
    assert 'summaries' in content
    assert 'statistics' in content['summaries']


def test_queryables(config):
    api = STACAPI(config)
    headers, status, content = api.queryables({}, {})
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/schema+json'
    assert content['type'] == 'object'
    assert content['title'] == 'pycsw Geospatial Catalogue'
    assert content['$id'] == 'http://localhost/pycsw/oarec/stac/collections/metadata:main/queryables'  # noqa
    assert content['$schema'] == 'http://json-schema.org/draft/2019-09/schema'

    assert len(content['properties']) == 14

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
    #assert record['collection'] == 'S2MSI2A'

    for feature in content['features']:
        if feature.get('geometry') is not None:
            assert 'bbox' in feature
            assert isinstance(feature['bbox'], list)

        for link in feature['links']:
            assert 'href' in link
            assert 'rel' in link

    for link in content['links']:
        assert 'href' in link
        assert 'rel' in link
        assert 'metadata:main' not in link['href']

    # test GET KVP requests
    content = json.loads(api.items({}, None, {'bbox': '-180,-90,180,90'})[2])
    assert len(content['features']) == 10

    content = json.loads(api.items({}, None, {'datetime': '2021-02-16'})[2])
    assert len(content['features']) == 2

    content = json.loads(api.items({}, None,
                                   {'bbox': '-180,-90,180,90',
                                   'datetime': '2021-02-16'})[2])
    assert len(content['features']) == 2

    content = json.loads(api.items({}, None, {'sortby': 'title'})[2])

    assert len(content['features']) == 10
    assert content['features'][6]['properties']['title'] == 'S2B_MSIL1C_20190910T095029_N0208_R079_T33UWQ_20190910T120910.SAFE'  # noqa

    content = json.loads(api.items({}, None, {'sortby': '-title'})[2])

    assert len(content['features']) == 10
    assert content['features'][5]['properties']['title'] == 'S2B_MSIL2A_20190910T095029_N0500_R079_T33UXQ_20230430T083712.SAFE'  # noqa

    content = json.loads(api.items({}, None, {'sortby': 'datetime'})[2])

    assert len(content['features']) == 10
    assert content['features'][5]['properties']['title'] == 'S2B_MSIL1C_20190910T095029_N0208_R079_T33UWP_20190910T120910.SAFE'  # noqa

    content = json.loads(api.items({}, None, {'sortby': '-datetime'})[2])

    assert len(content['features']) == 10
    assert content['features'][6]['properties']['title'] == 'S2B_MSIL2A_20190910T095029_N0500_R079_T33UXP_20230430T083712.SAFE'  # noqa

    params = {'filter': "title LIKE '%%sentinel%%'"}
    content = json.loads(api.items({}, None, params)[2])
    assert content['numberMatched'] == 3
    assert content['numberReturned'] == 3
    assert len(content['features']) == content['numberReturned']

    params = {'filter': "title LIKE '%%sentinel%%'", 'q': 'specTral'}
    content = json.loads(api.items({}, None, params)[2])
    assert content['numberMatched'] == 3
    assert content['numberReturned'] == 3
    assert len(content['features']) == content['numberReturned']

    # test POST JSON requests
    content = json.loads(api.items({}, {'bbox': [-180, -90, 180, 90]}, {})[2])
    assert len(content['features']) == 10

    content = json.loads(api.items({},
                                   {'bbox': [-180, -90, 180, 90], 'datetime': '2019-09-10T09:50:29.024000Z'},  # noqa
                                   {})[2])
    assert len(content['features']) == 10

    content = json.loads(api.items({}, {'datetime': '2024-11-28T09:23:31.024000Z'}, {})[2])  # noqa
    assert len(content['features']) == 2

    content = json.loads(api.items({},
                                   {'sortby': [{'field': 'title', 'direction': 'asc'}]},  # noqa
                                   {})[2])

    assert len(content['features']) == 10
    assert content['features'][6]['properties']['title'] == 'S2B_MSIL1C_20190910T095029_N0208_R079_T33UWQ_20190910T120910.SAFE'  # noqa

    content = json.loads(api.items({},
                                   {'sortby': [{'field': 'title', 'direction': 'desc'}]},  # noqa
                                   {})[2])
    assert len(content['features']) == 10
    assert content['features'][5]['properties']['title'] == 'S2B_MSIL2A_20190910T095029_N0500_R079_T33UXQ_20230430T083712.SAFE'  # noqa

    headers, status, content = api.items({}, None, {}, 'foo')
    assert status == 400

    # test items from a specific collection
    headers, status, content = api.items({}, None, {}, 'S2MSI2A')
    assert status == 200

    content = json.loads(content)

    assert content['numberMatched'] == 11
    for feature in content['features']:
        assert feature['collection'] == 'S2MSI2A'

    # test items from a specific collection with a temporal query predicate
    headers, status, content = api.items({}, None, {'datetime': '2018-10-09T21:00:00.000Z/2019-10-23T12:51:01.271Z'}, 'S2MSI1C')  # noqa
    assert status == 200

    content = json.loads(content)

    assert content['numberMatched'] == 12
    for feature in content['features']:
        assert feature['collection'] == 'S2MSI1C'

    # test limit
    content = json.loads(api.items({}, {'limit': 1}, {})[2])

    assert content['numberReturned'] == 1
    assert content['numberMatched'] == 31

    # test ids
    ids = [
        'S2B_MSIL2A_20190910T095029_N0213_R079_T33UXQ_20190910T124513.SAFE',
        'S2B_MSIL2A_20190910T095029_N0213_R079_T33UXP_20190910T124513.SAFE'
    ]
    content = json.loads(api.items({}, {'ids': ids}, {})[2])

    assert content['numberReturned'] == 2
    assert content['numberMatched'] == 2

    content = json.loads(api.items({}, None, {'off_nadir': '3.8'})[2])
    assert len(content['features']) == 1
    assert content['features'][0]['properties']['view:off_nadir'] == 3.8


def test_item(config):
    api = STACAPI(config)
    item = 'S2B_MSIL2A_20190910T095029_N0500_R079_T33TXN_20230430T083712.SAFE'
    headers, status, content = api.item({}, {}, 'metadata:main', item)
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/geo+json'
    assert status == 200

    assert content['id'] == item
    assert content['stac_version'] == '1.0.0'
    assert content['collection'] == 'S2MSI2A'

    assert content['geometry']['coordinates'][0][0][0] == 16.33660021997006

    assert 'assets' in content
    assert 'B02' in content['assets']
    assert 'product-metadata' in content['assets']

    for link in content['links']:
        assert 'href' in link
        assert 'rel' in link

    headers, status, content = api.item({}, {}, 'foo', item)
    assert status == 400


def test_json_transaction(config, sample_collection, sample_item,
                          sample_item_collection):
    api = STACAPI(config)
    request_headers = {
        'Content-Type': 'application/json'
    }

    # ensure an item insert is part of a collection
    headers, status, content = api.manage_collection_item(
        request_headers, 'create', data=sample_item,
        collection='non-existent-collection')

    assert status == 400

    # insert item
    headers, status, content = api.manage_collection_item(
        request_headers, 'create', data=sample_item,
        collection='metadata:main')

    assert status == 201

    # test that item is in repository
    content = json.loads(api.item({}, {}, 'metadata:main',
                         '20201211_223832_CS2')[2])

    assert content['id'] == '20201211_223832_CS2'
    assert content['geometry'] is None
    assert content['properties']['datetime'] == '2020-12-11T22:38:32.125000Z'
    assert content['collection'] == 'metadata:main'

    # update item
    sample_item['properties']['datetime'] = '2021-12-14T22:38:32Z'

    headers, status, content = api.manage_collection_item(
        request_headers, 'update', item='20201211_223832_CS2',
        data=sample_item, collection='metadata:main')

    assert status == 204

    # test that item is in repository
    content = json.loads(api.item({}, {}, 'metadata:main',
                         '20201211_223832_CS2')[2])

    assert content['id'] == '20201211_223832_CS2'
    assert content['properties']['datetime'] == sample_item['properties']['datetime']  # noqa
    assert content['collection'] == 'metadata:main'

    # delete item
    headers, status, content = api.manage_collection_item(
        request_headers, 'delete', item='20201211_223832_CS2')

    assert status == 200

    # test that item is not in repository
    headers, status, content = api.item({}, {}, 'metadata:main',
                                        '20201211_223832_CS2')

    assert status == 404

    content = api.items({}, None, {})[2]

    matched = json.loads(content)['numberMatched']

    assert matched == 31

    # insert item collection
    headers, status, content = api.manage_collection_item(
        request_headers, 'create', data=sample_item_collection,
        collection='metadata:main')

    assert status == 201

    content = api.items({}, None, {})[2]

    matched = json.loads(content)['numberMatched']

    assert matched == 33

    # delete items from item collection
    headers, status, content = api.manage_collection_item(
        request_headers, 'delete', item='20201211_223832_CS2')

    assert status == 200

    headers, status, content = api.manage_collection_item(
        request_headers, 'delete', item='20201212_223832_CS2')

    assert status == 200

    collection_id = '123e4567-e89b-12d3-a456-426614174000'

    # insert collection
    headers, status, content = api.manage_collection_item(
        request_headers, 'create', data=sample_collection)

    assert status == 201

    # test that collection is in repository
    headers, status, content = api.collections({}, {'f': 'json'})
    content = json.loads(content)

    collection_found = False

    for collection in content['collections']:
        if collection['id'] == collection_id:
            collection_found = True

    assert collection_found

    headers, status, content = api.collection(
        {}, {'f': 'json'}, collection=collection_id)

    content = json.loads(content)

    assert content['id'] == collection_id

    assert content['title'] == 'ORT_SPOT7_20190922_094920500_000'

    # ensure collection is empty

    headers, status, content = api.items({}, {}, {'collections': collection_id, 'f': 'json'})  # noqa

    content = json.loads(content)

    assert len(content['features']) == 0

    # update collection
    sample_collection['title'] = 'test title update'

    headers, status, content = api.manage_collection_item(
        request_headers, 'update', item=collection_id,
        data=sample_collection, collection='metadata:main')

    assert status == 204

    headers, status, content = api.collection(
        {}, {'f': 'json'}, collection=collection_id)

    content = json.loads(content)

    assert content['title'] == sample_collection['title']

    # test that item is in repository
    content = json.loads(api.item({}, {}, 'metadata:main',
                         '20201211_223832_CS2')[2])

    # delete collection
    headers, status, content = api.manage_collection_item(
        request_headers, 'delete', item=collection_id)

    content = json.loads(content)

    assert status == 200

    # test that collection is not in repository
    headers, status, content = api.collections({}, {'f': 'json'})
    content = json.loads(content)

    collection_found = False

    for collection in content['collections']:
        if collection['id'] == collection_id:
            collection_found = True

    assert not collection_found
