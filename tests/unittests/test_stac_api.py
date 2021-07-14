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
    assert len(content['links']) == 12

    assert content['stac_version'] == '1.0.0'
    assert content['type'] == 'Catalog'
    assert len(content['conformsTo']) == 8
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

    assert len(content['conformsTo']) == 8

    print(content['conformsTo'])
    assert 'https://api.stacspec.org/v1.0.0-beta.2/core' in content['conformsTo']  # noqa
    assert 'https://api.stacspec.org/v1.0.0-beta.2/item-search' in content['conformsTo']  # noqa


def test_items(api):
    content = json.loads(api.items({}, {}, True)[2])

    assert content['type'] == 'FeatureCollection'

    record = content['features'][0]

    assert record['stac_version'] == '1.0.0'
    assert record['collection'] == 'metadata:main'

    assert 'associations' not in record['properties']


def test_item(api):
    item = 'urn:uuid:19887a8a-f6b0-4a63-ae56-7fba0e17801f'
    content = json.loads(api.item({}, {}, item, True)[2])

    assert content['id'] == item
    assert content['stac_version'] == '1.0.0'
    assert content['collection'] == 'metadata:main'
