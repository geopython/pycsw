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
"""Unit tests for pycsw.core.util"""

import datetime as dt
import os
import time

import mock
import pytest
from shapely.wkt import loads

from pycsw.core import util

pytestmark = pytest.mark.unit


def test_get_today_and_now():
    fake_now = "2017-01-01T00:00:00Z"
    with mock.patch.object(util.time, "localtime") as mock_localtime:
        mock_localtime.return_value = time.strptime(
            fake_now,
            "%Y-%m-%dT%H:%M:%SZ"
        )
        result = util.get_today_and_now()
        assert result == fake_now


@pytest.mark.parametrize("value, expected", [
    (dt.date(2017, 1, 23), "2017-01-23"),
    (dt.datetime(2017, 1, 23), "2017-01-23"),
    (dt.datetime(2017, 1, 23, 20, 32, 10), "2017-01-23T20:32:10Z"),
    (dt.datetime(2017, 1, 23, 10), "2017-01-23T10:00:00Z"),
    (dt.datetime(2017, 1, 23, 10, 20), "2017-01-23T10:20:00Z"),
])
def test_datetime2iso8601(value, expected):
    result = util.datetime2iso8601(value)
    assert result == expected


@pytest.mark.parametrize("version, expected", [
    ("2", -1),
    ("1.2", -1),
    ("5.4.3.2", -1),
    ("This is a regular string, not a version", -1),
    ("3.4.1", 30401),
])
def test_get_version_integer(version, expected):
    result = util.get_version_integer(version)
    assert result == expected


@pytest.mark.parametrize("invalid_version", [
    2,
    2.2,
    None,
])
def test_get_version_integer_invalid_version(invalid_version):
    with pytest.raises(RuntimeError):
        util.get_version_integer(invalid_version)

@pytest.mark.parametrize("xpath_expression, expected", [
    ("ns1:first", "{something}first"),
    ("ns1:first/ns2:second", "{something}first/{other}second"),
    ("ns1:first/ns2:second[1]", "{something}first/{other}second[1]"),
    ("ns1:first/*/ns3:third", "{something}first/*/{another}third"),
    ("", ""),
])
def test_nspath_eval(xpath_expression, expected):
    nsmap = {
        "ns1": "something",
        "ns2": "other",
        "ns3": "another",
    }
    result = util.nspath_eval(xpath_expression, nsmap)
    assert result == expected


def test_nspath_eval_invalid_element():
    with pytest.raises(RuntimeError):
        util.nspath_eval(
            xpath="ns1:tag1/ns2:ns3:tag2",
            nsmap={
                "ns1": "something",
                "ns2": "other",
                "ns3": "another",
            }
        )

@pytest.mark.parametrize("envelope, expected", [
    ("ENVELOPE (-180,180,90,-90)", "-180,-90,180,90"),
    (" ENVELOPE(-180,180,90,-90)", "-180,-90,180,90"),
    (" ENVELOPE( -180, 180, 90, -90) ", "-180,-90,180,90"),
])
def test_wktenvelope2bbox(envelope, expected):
    result = util.wktenvelope2bbox(envelope)
    assert result == expected

# TODO - Add more WKT cases for other geometry types
@pytest.mark.parametrize("wkt, bounds, expected", [
    ("POINT (10 10)", True, (10.0, 10.0, 10.0, 10.0)),
    ("SRID=4326;POINT (10 10)", True, (10.0, 10.0, 10.0, 10.0)),
    ("POINT (10 10)", False, loads("POINT (10 10)")),
    ("SRID=4326;POINT (10 10)", False, loads("POINT (10 10)")),
])
def test_wkt2geom(wkt, bounds, expected):
    result = util.wkt2geom(wkt, bounds=bounds)
    assert result == expected


@pytest.mark.parametrize("bbox, expected", [
    (
        "0.0, 10.0, 30.0, 15.0",
        "POLYGON((0.00 10.00, 0.00 15.00, 30.00 15.00, "
        "30.00 10.00, 0.00 10.00))"
    ),
    (
        "-10.0, 10.0, 30.0, 15.0",
        "POLYGON((-10.00 10.00, -10.00 15.00, 30.00 15.00, "
        "30.00 10.00, -10.00 10.00))"
    ),
])
def test_bbox2wktpolygon(bbox, expected):
    result = util.bbox2wktpolygon(bbox)
    assert result == expected


def test_transform_mappings():
    queryables = {
        "q1": {"xpath": "p1", "dbcol": "col1"},
        "q2": {"xpath": "p2", "dbcol": "col2"},
    }
    typename = {"q2": "q1"}
    duplicate_queryables = queryables.copy()
    duplicate_typename = typename.copy()
    util.transform_mappings(duplicate_queryables, duplicate_typename)
    assert duplicate_queryables["q1"]["xpath"] == queryables["q2"]["xpath"]
    assert duplicate_queryables["q1"]["dbcol"] == queryables["q2"]["dbcol"]


@pytest.mark.parametrize("name, value, expected", [
    ("name", "john", "john"),
    ("date", dt.date(2017, 1, 1), "2017-01-01"),
    ("datetime", dt.datetime(2017, 1, 1, 10, 5), "2017-01-01T10:05:00Z"),
    ("some_callable", os.getcwd, os.getcwd()),
])
def test_getqattr_no_link(name, value, expected):
    class Phony(object):
        pass

    instance = Phony()
    setattr(instance, name, value)
    result = util.getqattr(instance, name)
    assert result == expected


def test_getqattr_link():
    some_object = mock.MagicMock()
    some_object.some_link.return_value = [
        ["one", "two"],
        ["three", "four"],
    ]
    result = util.getqattr(some_object, "some_link")
    assert result == "one,two^three,four"


def test_getqattr_invalid():
        result = util.getqattr(dt.date(2017, 1, 1), "name")
        assert result is None


def test_http_request_post():
    # here we replace owslib.util.http_post with a mock object
    # because we are not interested in testing owslib
    method = "POST"
    url = "some_phony_url"
    request = "some_phony_request"
    timeout = 40
    with mock.patch("pycsw.core.util.http_post",
                    autospec=True) as mock_http_post:
        util.http_request(
            method=method,
            url=url,
            request=request,
            timeout=timeout
        )
        mock_http_post.assert_called_with(url, request, timeout=timeout)


@pytest.mark.parametrize("url, expected", [
    ("http://host/wms", "http://host/wms?"),
    ("http://host/wms?foo=bar&", "http://host/wms?foo=bar&"),
    ("http://host/wms?foo=bar", "http://host/wms?foo=bar&"),
    ("http://host/wms?", "http://host/wms?"),
    ("http://host/wms?foo", "http://host/wms?foo&"),
])
def test_bind_url(url, expected):
    result = util.bind_url(url)
    assert result == expected


@pytest.mark.parametrize("ip, netmask, expected", [
    ("192.168.100.14", "192.168.100.0/24", True),
    ("192.168.100.14", "192.168.0.0/24", False),
    ("192.168.100.14", "192.168.0.0/16", True),
])
def test_ip_in_network_cidr(ip, netmask, expected):
    result = util.ip_in_network_cidr(ip, netmask)
    assert result == expected


@pytest.mark.parametrize("ip, whitelist, expected", [
    ("192.168.100.14", [], False),
    ("192.168.100.14", ["192.168.100.15"], False),
    ("192.168.100.14", ["192.168.100.15", "192.168.100.14"], True),
    ("192.168.100.14", ["192.168.100.*"], True),
    ("192.168.100.14", ["192.168.100.15", "192.168.100.*"], True),
    ("192.168.100.14", ["192.168.100.0/24"], True),
    ("192.168.100.14", ["192.168.100.15", "192.168.100.0/24"], True),
    ("192.168.10.14", ["192.168.100.15", "192.168.0.0/16"], True),
])
def test_ipaddress_in_whitelist(ip, whitelist, expected):
    result = util.ipaddress_in_whitelist(ip, whitelist)
    assert result == expected


