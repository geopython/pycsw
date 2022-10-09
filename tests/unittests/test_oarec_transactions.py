# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2022 Tom Kralidis
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
import os
from xml.etree import ElementTree as etree

import pytest

from pycsw.core.util import parse_ini_config
from pycsw.ogc.api.records import API

pytestmark = pytest.mark.unit


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
def test_data_json():
    with open(get_test_file_path('data/oarec/record-123.json')) as fh:
        return json.load(fh)


@pytest.fixture()
def test_data_xml():
    with open(get_test_file_path('data/oarec/record-456.xml'), 'rb') as fh:
        return fh.read()


@pytest.fixture()
def api(config):
    return API(config)


def test_json(api, test_data_json):

    request_headers = {
        'Content-Type': 'application/json'
    }

    # insert record
    headers, status, content = api.manage_collection_item(
        request_headers, 'create', data=test_data_json)

    assert status == 201

    # test that record is in repository
    content = json.loads(api.item({}, {}, 'metadata:main', 'record-123')[2])

    assert content['id'] == 'record-123'
    assert content['properties']['title'] == 'title in English'

    # test XML representation
    params = {'f': 'xml'}
    content = api.item({}, params, 'metadata:main', 'record-123')[2]

    e = etree.fromstring(content)

    element = e.find('{http://www.w3.org/2005/Atom}id').text
    assert element == 'record-123'

    element = e.find('{http://www.w3.org/2005/Atom}title').text
    assert element == 'title in English'

    # update record
    test_data_json['properties']['title'] = 'new title'

    headers, status, content = api.manage_collection_item(
        request_headers, 'update', item='record-123', data=test_data_json)

    assert status == 204

    # test that record is in repository
    content = json.loads(api.item({}, {}, 'metadata:main', 'record-123')[2])

    assert content['id'] == 'record-123'
    assert content['properties']['title'] == 'new title'

    # test XML representation
    params = {'f': 'xml'}
    content = api.item({}, params, 'metadata:main', 'record-123')[2]

    e = etree.fromstring(content)

    element = e.find('{http://www.w3.org/2005/Atom}id').text
    assert element == 'record-123'

    element = e.find('{http://www.w3.org/2005/Atom}title').text
    assert element == 'new title'

    # delete record
    headers, status, content = api.manage_collection_item(
        request_headers, 'delete', item='record-123')

    assert status == 200

    # test that record is not in repository
    headers, status, content = api.item({}, {}, 'metadata:main', 'record-123')

    assert status == 404


def test_xml(api, test_data_xml):

    request_headers = {
        'Content-Type': 'application/xml'
    }

    # insert record
    headers, status, content = api.manage_collection_item(
        request_headers, 'create', data=test_data_xml)

    assert status == 201

    # test that record is in repository
    content = json.loads(api.item({}, {}, 'metadata:main', 'record-456')[2])

    assert content['id'] == 'record-456'
    assert content['properties']['title'] == 'Ut facilisis justo ut lacus'

    # test XML representation
    params = {'f': 'xml'}
    content = api.item({}, params, 'metadata:main', 'record-456')[2]

    e = etree.fromstring(content)

    element = e.find('{http://purl.org/dc/elements/1.1/}identifier').text
    assert element == 'record-456'

    element = e.find('{http://purl.org/dc/elements/1.1/}title').text
    assert element == 'Ut facilisis justo ut lacus'

    # update record
    test_data_xml = test_data_xml.replace(
        b'Ut facilisis justo ut lacus', b'new title')

    headers, status, content = api.manage_collection_item(
        request_headers, 'update', item='record-456', data=test_data_xml)

    assert status == 204

    # test that record is in repository
    content = json.loads(api.item({}, {}, 'metadata:main', 'record-456')[2])

    assert content['id'] == 'record-456'
    assert content['properties']['title'] == 'new title'

    # test XML representation
    params = {'f': 'xml'}
    content = api.item({}, params, 'metadata:main', 'record-456')[2]

    e = etree.fromstring(content)

    element = e.find('{http://purl.org/dc/elements/1.1/}identifier').text
    assert element == 'record-456'

    element = e.find('{http://purl.org/dc/elements/1.1/}title').text
    assert element == 'new title'

    # delete record
    headers, status, content = api.manage_collection_item(
        request_headers, 'delete', item='record-456')

    assert status == 200

    # test that record is not in repository
    headers, status, content = api.item({}, {}, 'metadata:main', 'record-456')

    assert status == 404
