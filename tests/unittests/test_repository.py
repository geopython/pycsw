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
"""Unit tests for pycsw.core.repository"""

import pytest

from pycsw.core import repository
from pycsw.core.config import StaticContext

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("data, input_, predicate, distance, expected", [
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "bbox", 0, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(2 2)", "bbox", 0, "false"),
    ("LINESTRING(0 0, 1 1)", "POINT(2 2)", "beyond", 1, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(2 2)", "beyond", 2, "false"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "beyond", "false", "false"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "contains", 0, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(2 2)", "contains", 0, "false"),
    ("LINESTRING(0 0, 1 1)", "LINESTRING(1 0, 0 1)", "crosses", 0, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "crosses", 0, "false"),
    ("POINT(1 1)", "POINT(1 1)", "equals", 0, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "equals", 0, "false"),
    ("LINESTRING(0 0, 1 1)", "POINT(0 0)", "touches", 0, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "touches", 0, "false"),
    ("POINT(0.5 0.5)", "LINESTRING(0 0, 1 1)", "within", 0, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "within", 0, "false"),
    (None, "POINT(0.5 0.5)", "within", 0, "false"),
    ("POINT(0.5 0.5)", None, "within", 0, "false"),
    (None, None, "within", 0, "false"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "dwithin", "false", "false"),
])
def test_query_spatial(data, input_, predicate, distance, expected):
    result = repository.query_spatial(
        bbox_data_wkt=data,
        bbox_input_wkt=input_,
        predicate=predicate,
        distance=distance
    )
    assert result == expected


@pytest.fixture
def multiprofile_repo(tmp_path):
    """Repository seeded with records of two different typenames, as happens
    when multiple CSW profiles share a single table."""
    database = 'sqlite:///%s' % (tmp_path / 'records.db')
    repository.setup(database, 'records')

    context = StaticContext()
    repo = repository.Repository(database, context, table='records')

    fixtures = [
        ('rec-generic', 'csw:Record'),
        ('rec-profile-a', 'foo:RecordA'),
        ('rec-profile-a-2', 'foo:RecordA'),
        ('rec-profile-b', 'foo:RecordB'),
    ]
    for identifier, typename in fixtures:
        record = repo.dataset(
            identifier=identifier,
            typename=typename,
            schema='http://www.opengis.net/cat/csw/2.0.2',
            mdsource='local',
            insert_date='2024-01-01',
            xml='<foo/>',
            anytext=identifier,
            metadata_type='application/xml',
        )
        repo.insert(record, 'local', '2024-01-01')

    return repo


def test_query_filters_by_typename(multiprofile_repo):
    """A GetRecords with a specific (non-generic) typeNames must only return
    rows whose typename column matches."""
    total, records = multiprofile_repo.query(
        constraint={}, typenames=['foo:RecordA'])

    assert total == '2'
    assert {r.identifier for r in records} == {'rec-profile-a',
                                               'rec-profile-a-2'}
    assert all(r.typename == 'foo:RecordA' for r in records)


def test_query_generic_typename_returns_all(multiprofile_repo):
    """The CSW wildcard type csw:Record must not filter by typename, i.e.
    single-profile / default behaviour is preserved."""
    total, records = multiprofile_repo.query(
        constraint={}, typenames=['csw:Record'])

    assert total == '4'
    assert len(records) == 4


def test_query_no_typename_returns_all(multiprofile_repo):
    """Omitting typenames entirely preserves the pre-existing behaviour."""
    total, records = multiprofile_repo.query(constraint={})

    assert total == '4'
    assert len(records) == 4
