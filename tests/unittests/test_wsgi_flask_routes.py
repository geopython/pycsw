# =================================================================
#
# Authors: Massimo Di Stefano <epiesasha@me.com>
#
# Copyright (c) 2026 Massimo Di Stefano
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

"""Regression tests for Flask routes that accept path-containing IDs."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


ROOT = Path(__file__).parents[2]
CONFIG = ROOT / "tests" / "functionaltests" / "suites" / "cite" / "default.yml"


def test_stac_routes_accept_path_containing_collection_and_item_ids():
    script = """
from pycsw import wsgi_flask

adapter = wsgi_flask.APP.url_map.bind('localhost')
# use-case where collection's name has path-like expression
collection = 'doi:10.1594/PANGAEA.912516'
item = 'doi:10.1594/PANGAEA.912516/record-1'

assert adapter.match('/stac/collections/' + collection)[0] == 'pycsw.collection'
assert adapter.match('/stac/collections/' + collection + '/items')[0] == 'pycsw.items'
assert (
    adapter.match('/stac/collections/' + collection + '/items/' + item)[0]
    == 'pycsw.item'
)
"""
    environment = os.environ.copy()
    environment["PYCSW_CONFIG"] = str(CONFIG)
    environment["PYTHONPATH"] = str(ROOT)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_trailing_slash_routes_like_no_slash_and_unknown_collection_is_404():
    script = """
import json
from pycsw import wsgi_flask

client = wsgi_flask.APP.test_client()

def get(path):
    response = client.get(path, query_string={'f': 'json'})
    content = response.get_json()
    if isinstance(content, dict):
        content.pop('timeStamp', None)  # differs between any two requests
    return response.status_code, content

# a trailing slash must not turn into part of a path-converter identifier
for path in ['/collections/metadata:main/items', '/collections/metadata:main/queryables',
             '/collections/metadata:main', '/collections', '/stac/collections', '/']:
    status, content = get(path)
    status_slash, content_slash = get(path.rstrip('/') + '/')
    assert status == 200, (path, status)
    assert (status_slash, content_slash) == (status, content), path

status, content = get('/collections/does-not-exist')
assert status == 404, status
assert content['description'] == 'collection not found', content
"""
    environment = os.environ.copy()
    environment["PYCSW_CONFIG"] = str(CONFIG)
    environment["PYTHONPATH"] = str(ROOT)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
