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
"""Unit tests for pycsw.opensearch"""

import pytest

from pycsw import opensearch

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("bbox, expected", [
    ([10, 30, -10, -30], True),
    ([10.0, 30.0, -10.0, -30.0], True),
    (["10", "30", "-10", "-30"], True),
    ([-180, 30, -10, -30], True),
    ([180, 30, -10, -30], True),
    ([0, -90, -10, -30], True),
    ([0, 90, -10, -30], True),
    ([10, 30, -180, -30], True),
    ([10, 30, 180, -30], True),
    ([10, 30, -10, -90], True),
    ([10, 30, -10, 90], True),
    ([-190, 30, -10, -30], False),
    ([190, 30, -10, -30], False),
    ([10, 100, -10, -30], False),
    ([10, -100, -10, -30], False),
    ([10, 30, -190, -30], False),
    ([10, 30, 190, -30], False),
    ([10, 30, -10, -190], False),
    ([10, 30, -10, 190], False),
])
def test_validate_4326(bbox, expected):
    result = opensearch.validate_4326(bbox)
    assert result == expected