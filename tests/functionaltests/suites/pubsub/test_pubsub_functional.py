# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2025 Tom Kralidis
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

from pycsw.ogc.api.records import API

pytestmark = pytest.mark.functional


def test_landing_page(config):
    api = API(config)
    headers, status, content = api.landing_page({}, {'f': 'json'})
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/json'
    assert status == 200
    assert len(content['links']) == 16

    links = (
        api.config['server']['url'],
        api.config['pubsub']['broker']['url']
    )

    for link in content['links']:
        assert link['href'].startswith(links)

    headers, status, content = api.landing_page({}, {'f': 'html'})
    assert status == 200
    assert headers['Content-Type'] == 'text/html'


def test_conformance(config):
    api = API(config)
    headers, status, content = api.conformance({}, {})
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/json'
    assert len(content['conformsTo']) == 16
