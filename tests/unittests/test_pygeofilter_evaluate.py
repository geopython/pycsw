# =================================================================
#
# Authors: Ahmed Hassan
#
# Copyright (c) 2026 Ahmed Hassan
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
"""Unit tests for pycsw.core.pygeofilter_evaluate"""

import pytest
from pygeofilter.parsers.ecql import parse as parse_ecql
from sqlalchemy import Column, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import declarative_base

from pycsw.core.pygeofilter_evaluate import to_filter

pytestmark = pytest.mark.unit


class dataset(declarative_base()):
    __tablename__ = 'records'
    identifier = Column(Text, primary_key=True)
    anytext = Column(Text)


def test_postgresql_fts_anytext_like_binds_each_term():
    ast = parse_ecql("anytext LIKE 'soil' AND anytext LIKE 'water'")
    filters = to_filter(ast, 'postgresql', {'anytext': dataset.anytext})

    compiled = filters.compile(dialect=postgresql.dialect())
    sql = str(compiled)

    assert sql.count('plainto_tsquery') == 2
    assert ")s'" not in sql
    assert len(compiled.params) == 2
    assert sorted(compiled.params.values()) == ['soil', 'water']


@pytest.mark.parametrize('ecql', [
    "anytext NOT LIKE 'soil'",
    "anytext NOT ILIKE 'soil'"
])
def test_postgresql_fts_anytext_not_like_is_negated(ecql):
    filters = to_filter(parse_ecql(ecql), 'postgresql',
                        {'anytext': dataset.anytext})

    sql = str(filters.compile(dialect=postgresql.dialect()))

    assert sql.startswith('NOT plainto_tsquery')
