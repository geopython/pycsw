# =================================================================
#
# Authors: Massimo Di Stefano
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
"""Unit tests for pycsw.ogc.api.records: sortby"""

import pytest
from sqlalchemy import column

from pycsw.ogc.api.records import sortby_to_order_by

pytestmark = pytest.mark.unit

# a repository without a database maps queryables to field names
FIELD_MAPPINGS = {'title': 'title_s', 'updated': 'insert_date'}


@pytest.mark.parametrize('sortby', [
    'title,-updated',
    [{'field': 'title', 'direction': 'asc'},
     {'field': 'updated', 'direction': 'desc'}],
])
def test_sortby_to_order_by_field_names(sortby):
    assert sortby_to_order_by(sortby, FIELD_MAPPINGS) == [
        {'field': 'title_s', 'direction': 'asc'},
        {'field': 'insert_date', 'direction': 'desc'},
    ]


def test_sortby_to_order_by_columns():
    mappings = {'title': column('title'), 'updated': column('insert_date')}
    order_by = sortby_to_order_by('title,-updated', mappings)
    assert [str(key) for key in order_by] == ['title ASC', 'insert_date DESC']


def test_sortby_to_order_by_unknown_property():
    with pytest.raises(ValueError, match='Invalid sortby property'):
        sortby_to_order_by('-nosuchproperty', FIELD_MAPPINGS)
