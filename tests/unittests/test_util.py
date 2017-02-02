"""Unit tests for pycsw.util"""

import datetime as dt

import pytest

from pycsw.core import util

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("value, expected", [
    (None, None),
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
    (None, -1),
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
])
def test_get_version_integer_invalid_version(invalid_version):
    with pytest.raises(RuntimeError):
        util.get_version_integer(invalid_version)
