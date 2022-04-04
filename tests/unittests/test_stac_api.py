import json
import os

import pytest

from pycsw.core.util import parse_ini_config
from pycsw.ogc.api.records import API


def get_test_file_path(filename):
    """helper function to open test file safely"""

    if os.path.isfile(filename):
        return filename
    else:
        return f'tests/unittests/{filename}'


@pytest.fixture()
def config():
    return parse_ini_config(get_test_file_path('oarec-default.cfg'))


@pytest.fixture()
def api(config):
    return API(config)


def test_landing_page(api):
    headers, status, content = api.landing_page({}, {'f': 'json'})
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/json'
    assert status == 200
    assert len(content['links']) == 14

    assert content['stac_version'] == '1.0.0'
    assert content['type'] == 'Catalog'
    assert len(content['conformsTo']) == 12
    assert len(content['keywords']) == 3


def test_openapi(api):
    headers, status, content = api.openapi({}, {'f': 'json'})
    assert status == 200
    content = json.loads(content)
    assert headers['Content-Type'] == 'application/vnd.oai.openapi+json;version=3.0'  # noqa

    headers, status, content = api.openapi({}, {'f': 'html'})
    assert status == 200
    assert headers['Content-Type'] == 'text/html'


def test_conformance(api):
    content = json.loads(api.conformance({}, {})[2])

    assert len(content['conformsTo']) == 12

    assert 'https://api.stacspec.org/v1.0.0/core' in content['conformsTo']  # noqa
    assert 'https://api.stacspec.org/v1.0.0/item-search' in content['conformsTo']  # noqa


def test_items(api):
    content = json.loads(api.items({}, None, {}, stac_item=True)[2])

    assert content['type'] == 'FeatureCollection'

    record = content['features'][0]

    assert record['stac_version'] == '1.0.0'
    assert record['collection'] == 'metadata:main'

    assert 'associations' not in record['properties']

    # test GET KVP requests
    content = json.loads(api.items({}, None, {'bbox': '-180,-90,180,90'},
                         stac_item=True)[2])
    assert len(content['features']) == 3

    content = json.loads(api.items({}, None, {'datetime': '2006-03-26'},
                         stac_item=True)[2])
    assert len(content['features']) == 1

    content = json.loads(api.items({}, None,
                         {'bbox': '-180,-90,180,90', 'datetime': '2006-03-26'},
                         stac_item=True)[2])
    assert len(content['features']) == 1

    content = json.loads(api.items({}, None, {'sortby': 'title'}, stac_item=True)[2])
    assert len(content['features']) == 10
    assert content['features'][5]['properties']['title'] == 'Lorem ipsum'

    content = json.loads(api.items({}, None, {'sortby': '-title'}, stac_item=True)[2])
    assert len(content['features']) == 10
    assert content['features'][5]['properties']['title'] == 'Lorem ipsum dolor sit amet'  # noqa

    params = {'filter': "title LIKE '%%Lorem%%'"}
    content = json.loads(api.items({}, None, params, stac_item=True)[2])
    assert content['numberMatched'] == 2
    assert content['numberReturned'] == 2
    assert len(content['features']) == content['numberReturned']

    params = {'filter': "title LIKE '%%Lorem%%'", 'q': 'iPsUm'}
    content = json.loads(api.items({}, None, params, stac_item=True)[2])
    assert content['numberMatched'] == 2
    assert content['numberReturned'] == 2
    assert len(content['features']) == content['numberReturned']

    # test POST JSON requests
    content = json.loads(api.items({}, {'bbox': [-180, -90, 180, 90]}, {},
                         stac_item=True)[2])
    assert len(content['features']) == 3

    content = json.loads(api.items({},
                         {'bbox': [-180, -90, 180, 90], 'datetime': '2006-03-26'},  # noqa
                         {}, stac_item=True)[2])
    assert len(content['features']) == 1

    content = json.loads(api.items({}, {'datetime': '2006-03-26'}, {},
                         stac_item=True)[2])
    assert len(content['features']) == 1

    content = json.loads(api.items({},
                         {'sortby': [{'field': 'title', 'direction': 'asc'}]},
                         {}, stac_item=True)[2])
    assert len(content['features']) == 10
    assert content['features'][5]['properties']['title'] == 'Lorem ipsum'

    content = json.loads(api.items({},
                         {'sortby': [{'field': 'title', 'direction': 'desc'}]},
                         {}, stac_item=True)[2])
    assert len(content['features']) == 10
    assert content['features'][5]['properties']['title'] == 'Lorem ipsum dolor sit amet'  # noqa


def test_item(api):
    item = 'urn:uuid:19887a8a-f6b0-4a63-ae56-7fba0e17801f'
    content = json.loads(api.item({}, {}, 'metadata:main', item, True)[2])

    assert content['id'] == item
    assert content['stac_version'] == '1.0.0'
    assert content['collection'] == 'metadata:main'
