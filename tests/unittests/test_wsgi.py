# =================================================================
#
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2017 Ricardo Garcia Silva
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
"""Unit tests for pycsw.wsgi"""

import mock
import pytest

from pycsw import wsgi

pytestmark = pytest.mark.unit

@pytest.mark.parametrize("process_env, wsgi_env, fake_dir, expected", [
    ({}, None, "dummy", "dummy"),
    ({"PYCSW_ROOT": "this"}, None, "dummy", "this"),
    ({"PYCSW_ROOT": "this"}, {"PYCSW_ROOT": "that"}, "dummy", "this"),
    ({}, {"PYCSW_ROOT": "that"}, "dummy", "that"),
])
def test_get_pycsw_root_path(process_env, wsgi_env, fake_dir, expected):
    with mock.patch("pycsw.wsgi.os", autospec=True) as mock_os:
        mock_os.path.dirname.return_value = fake_dir
        result = wsgi.get_pycsw_root_path(
            process_env,
            request_environment=wsgi_env
        )
        assert result == expected


@pytest.mark.parametrize("process_env, wsgi_env, pycsw_root, expected", [
    ({}, {}, "dummy", "dummy/"),
    ({"PYCSW_CONFIG": "default.cfg"}, {}, "dummy", "dummy/default.cfg"),
    (
        {"PYCSW_CONFIG": "/some/abs/path/default.cfg"},
        {},
        "dummy",
        "/some/abs/path/default.cfg"
    ),
    (
        {"PYCSW_CONFIG": "default.cfg"},
        {"QUERY_STRING": ""},
        "dummy",
        "dummy/default.cfg"
    ),
    (
        {"PYCSW_CONFIG": "default.cfg"},
        {"QUERY_STRING": "config=other.cfg"},
        "dummy",
        "dummy/other.cfg"
    ),
    (
        {"PYCSW_CONFIG": "default.cfg"},
        {"QUERY_STRING": "config=/other/path/other.cfg"},
        "dummy",
        "/other/path/other.cfg"
    ),
])
def test_get_configuration_path(process_env, wsgi_env, pycsw_root, expected):
    result = wsgi.get_configuration_path(process_env, wsgi_env, pycsw_root)
    assert result == expected


#@pytest.mark.parametrize("compression_level", [
#    1, 2, 3, 4, 5, 6, 7, 8, 9,
#])
#def test_compress_response(compression_level):
#    fake_response = "dummy"
#    with mock.patch("pycsw.wsgi.gzip", autospec=True) as mock_gzip:
#        compressed_response, headers = wsgi.compress_response(
#            fake_response, compression_level)
