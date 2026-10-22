# =================================================================
#
# Authors: Armin Arndt
#
# Copyright (c) 2026 Armin Arndt
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
"""Unit tests for server.record_transform hook"""

import textwrap

import pytest

from pycsw.core.util import load_record_transform


class FakeRecord:
    """Minimal stand-in for a pycsw ORM record object."""
    def __init__(self, keywords=''):
        self.keywords = keywords
        self.identifier = 'test-id'
        self.title = 'Test Record'


# ---------------------------------------------------------------------------
# load_record_transform tests
# ---------------------------------------------------------------------------

def test_load_record_transform_none():
    assert load_record_transform(None) is None
    assert load_record_transform('') is None


def test_load_record_transform_from_file(tmp_path):
    transform_file = tmp_path / 'mytransform.py'
    transform_file.write_text(textwrap.dedent("""
        def record_transform(record):
            if record.keywords:
                record.keywords = ','.join(
                    kw for kw in record.keywords.split(',')
                    if not kw.startswith('_internal_')
                )
            return record
    """))
    func = load_record_transform(str(transform_file))
    assert callable(func)


def test_load_record_transform_missing_callable(tmp_path):
    bad_file = tmp_path / 'bad.py'
    bad_file.write_text("x = 1\n")
    with pytest.raises(ValueError, match="must define a callable named 'record_transform'"):
        load_record_transform(str(bad_file))


def test_load_record_transform_missing_module():
    with pytest.raises(ValueError, match='Could not load record transform module'):
        load_record_transform('nonexistent.module.that.does.not.exist')


# ---------------------------------------------------------------------------
# Functional behaviour tests
# ---------------------------------------------------------------------------

def test_transform_filters_keywords(tmp_path):
    transform_file = tmp_path / 'transform.py'
    transform_file.write_text(textwrap.dedent("""
        def record_transform(record):
            if record.keywords:
                record.keywords = ','.join(
                    kw for kw in record.keywords.split(',')
                    if not kw.startswith('_internal_')
                )
            return record
    """))
    func = load_record_transform(str(transform_file))
    record = FakeRecord(keywords='climate,_internal_tag,ocean,_internal_private')
    result = func(record)
    assert result.keywords == 'climate,ocean'


def test_transform_no_keywords(tmp_path):
    transform_file = tmp_path / 'transform.py'
    transform_file.write_text(textwrap.dedent("""
        def record_transform(record):
            if record.keywords:
                record.keywords = ','.join(
                    kw for kw in record.keywords.split(',')
                    if not kw.startswith('_internal_')
                )
            return record
    """))
    func = load_record_transform(str(transform_file))
    record = FakeRecord(keywords=None)
    result = func(record)
    assert result.keywords is None


def test_transform_returns_record(tmp_path):
    transform_file = tmp_path / 'transform.py'
    transform_file.write_text(textwrap.dedent("""
        def record_transform(record):
            return record
    """))
    func = load_record_transform(str(transform_file))
    record = FakeRecord(keywords='topic1,topic2')
    result = func(record)
    assert result is record
