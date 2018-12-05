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

from wsgiref.util import setup_testing_defaults

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
    ({}, {}, "dummy", "dummy/default.cfg"),
    ({"PYCSW_CONFIG": "default.cfg"}, {}, "dummy", "default.cfg"),
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
        "default.cfg"
    ),
    (
        {"PYCSW_CONFIG": "default.cfg"},
        {"QUERY_STRING": "config=other.cfg"},
        "dummy",
        "other.cfg"
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


@pytest.mark.parametrize("compression_level", [
    1, 2, 3, 4, 5, 6, 7, 8, 9,
])
def test_compress_response(compression_level):
    fake_response = "dummy"
    with mock.patch("pycsw.wsgi.gzip", autospec=True) as mock_gzip:
        compressed_response, headers = wsgi.compress_response(
            fake_response, compression_level)
        creation_kwargs = mock_gzip.GzipFile.call_args[1]
        assert creation_kwargs["compresslevel"] == compression_level
        assert headers["Content-Encoding"] == "gzip"


def test_application_no_gzip():
    fake_config_path = "fake_config_path"
    fake_status = "fake_status"
    fake_response = "fake_response"
    fake_content_type = "fake_content_type"
    request_env = {}
    setup_testing_defaults(request_env)
    mock_start_response = mock.MagicMock()
    with mock.patch("pycsw.wsgi.server", autospec=True) as mock_server, \
            mock.patch.object(
                wsgi, "get_configuration_path") as mock_get_config_path:
        mock_get_config_path.return_value = fake_config_path
        mock_csw_class = mock_server.Csw
        mock_pycsw = mock_csw_class.return_value
        mock_pycsw.dispatch_wsgi.return_value = (fake_status, fake_response)
        mock_pycsw.contenttype = fake_content_type
        result = wsgi.application(request_env, mock_start_response)
        mock_csw_class.assert_called_with(fake_config_path, request_env)
        start_response_args = mock_start_response.call_args[0]
        assert fake_status in start_response_args
        assert result == [fake_response]


def test_application_gzip():
    fake_config_path = "fake_config_path"
    fake_status = "fake_status"
    fake_response = "fake_response"
    fake_content_type = "fake_content_type"
    fake_compression_level = 5
    fake_compressed_contents = "fake compressed contents"
    fake_compression_headers = {"phony": "dummy"}
    request_env = {"HTTP_ACCEPT_ENCODING": "gzip"}
    setup_testing_defaults(request_env)
    mock_start_response = mock.MagicMock()
    with mock.patch("pycsw.wsgi.server", autospec=True) as mock_server, \
            mock.patch.object(
                wsgi, "get_configuration_path") as mock_get_config_path, \
            mock.patch.object(wsgi, "compress_response") as mock_compress:

        mock_compress.return_value = (fake_compressed_contents,
                                      fake_compression_headers)
        mock_get_config_path.return_value = fake_config_path
        mock_csw_class = mock_server.Csw
        mock_pycsw = mock_csw_class.return_value
        mock_pycsw.config = mock.MagicMock()
        mock_pycsw.config.get.return_value = fake_compression_level
        mock_pycsw.dispatch_wsgi.return_value = (fake_status, fake_response)
        mock_pycsw.contenttype = fake_content_type
        wsgi.application(request_env, mock_start_response)
        mock_pycsw.config.get.assert_called_with("server",
                                                 "gzip_compresslevel")
        mock_compress.assert_called_with(fake_response, fake_compression_level)
