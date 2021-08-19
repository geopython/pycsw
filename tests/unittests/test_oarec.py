import json
import os
from xml.etree import ElementTree as etree

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

    for link in content['links']:
        assert link['href'].startswith(api.config['server']['url'])

    headers, status, content = api.landing_page({}, {'f': 'html'})
    assert status == 200
    assert headers['Content-Type'] == 'text/html'


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


def test_collections(api):
    content = json.loads(api.collections({}, {})[2])

    assert len(content['links']) == 2
    assert len(content['collections']) == 1

    content = json.loads(api.collections({}, {}, True)[2])
    assert len(content['links']) == 2
    assert content['id'] == 'metadata:main'
    assert content['title'] == 'pycsw Geospatial Catalogue'
    assert content['description'] == 'pycsw is an OARec and OGC CSW server implementation written in Python'  # noqa
    assert content['itemType'] == 'record'


def test_queryables(api):
    content = json.loads(api.queryables({}, {})[2])

    assert content['type'] == 'object'
    assert content['title'] == 'pycsw Geospatial Catalogue'
    assert content['$id'] == 'http://localhost/pycsw/oarec/collections/metadata:main/queryables'  # noqa
    assert content['$schema'] == 'http://json-schema.org/draft/2019-09/schema'

    assert len(content['properties']) == 60

    assert 'geometry' in content['properties']
    assert content['properties']['geometry']['$ref'] == 'https://geojson.org/schema/Polygon.json'  # noqa


def test_items(api):
    content = json.loads(api.items({}, {})[2])

    assert content['type'] == 'FeatureCollection'
    assert len(content['links']) == 4
    assert content['numberMatched'] == 12
    assert content['numberReturned'] == 10
    assert len(content['features']) == 10
    assert len(content['features']) == content['numberReturned']

    params = {'q': 'Lorem'}
    content = json.loads(api.items({}, params)[2])
    assert content['numberMatched'] == 5
    assert content['numberReturned'] == 5
    assert len(content['features']) == content['numberReturned']

    params = {'bbox': '-50,0,50,80'}
    content = json.loads(api.items({}, params)[2])
    assert content['numberMatched'] == 3
    assert content['numberReturned'] == 3
    assert len(content['features']) == content['numberReturned']

    params = {'bbox': '-50,0,50,80', 'q': 'Lorem'}
    content = json.loads(api.items({}, params)[2])
    assert content['numberMatched'] == 1
    assert content['numberReturned'] == 1
    assert len(content['features']) == content['numberReturned']

    params = {'filter': 'title LIKE "%%Lorem%%"'}
    content = json.loads(api.items({}, params)[2])
    assert content['numberMatched'] == 2
    assert content['numberReturned'] == 2
    assert len(content['features']) == content['numberReturned']

    params = {'filter': 'title LIKE "%%Lorem%%"', 'q': 'iPsUm'}
    content = json.loads(api.items({}, params)[2])
    assert content['numberMatched'] == 2
    assert content['numberReturned'] == 2
    assert len(content['features']) == content['numberReturned']

    params = {'limit': 4}
    content = json.loads(api.items({}, params)[2])
    assert content['numberMatched'] == 12
    assert content['numberReturned'] == 4
    assert len(content['features']) == content['numberReturned']

    params = {'limit': 4, 'startindex': 10}
    content = json.loads(api.items({}, params)[2])
    assert content['numberMatched'] == 12
    assert content['numberReturned'] == 2
    assert len(content['features']) == content['numberReturned']


def test_item(api):
    item = 'urn:uuid:19887a8a-f6b0-4a63-ae56-7fba0e17801f'
    content = json.loads(api.item({}, {}, item)[2])

    assert content['id'] == item
    assert content['type'] == 'Feature'
    assert content['properties']['title'] == 'Lorem ipsum'
    assert content['properties']['keywords'] == ['Tourism--Greece']

    item = 'urn:uuid:19887a8a-f6b0-4a63-ae56-7fba0e17801f'
    params = {'f': 'xml'}
    content = api.item({}, params, item)[2]

    e = etree.fromstring(content)

    element = e.find('{http://purl.org/dc/elements/1.1/}identifier').text
    assert element == item

    element = e.find('{http://purl.org/dc/elements/1.1/}type').text
    assert element == 'http://purl.org/dc/dcmitype/Image'

    element = e.find('{http://purl.org/dc/elements/1.1/}title').text
    assert element == 'Lorem ipsum'

    element = e.find('{http://purl.org/dc/elements/1.1/}subject').text
    assert element == 'Tourism--Greece'
