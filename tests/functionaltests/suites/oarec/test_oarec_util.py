# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2026 Tom Kralidis
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

from xml.sax.saxutils import unescape

import pytest

from pycsw.ogc.api.util import to_json

pytestmark = pytest.mark.functional


@pytest.mark.parametrize('data,minified,pretty_printed', [
    [{'foo': 'bar'}, '{"foo":"bar"}', '{\n    "foo":"bar"\n}'],
    [{'foo<script>alert("hi")</script>': 'bar'},
     '{"foo&lt;script&gt;alert(\\"hi\\")&lt;/script&gt;":"bar"}',
     '{\n    "foo&lt;script&gt;alert(\\"hi\\")&lt;/script&gt;":"bar"\n}']
])
def test_to_json(data, minified, pretty_printed):
    output = to_json(data)
    assert output == minified
    assert to_json(data, pretty=True) == pretty_printed

    unescaped_output = unescape(output)
    if '&lt;' in output:
        assert '<' in unescaped_output
    if '&gt;' in output:
        assert '>' in unescaped_output
