# =================================================================
#
# Authors: Tom Kralidis
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
"""Unit tests for pycsw.ogc.api.util"""

import pytest

from pycsw.ogc.api import util

pytestmark = pytest.mark.unit

TEMPLATE_USING_TO_JSON = "{{ data | to_json }}"


def test_render_j2_template_custom_templates_path(tmp_path, monkeypatch):
    default_templates = tmp_path / 'default'
    default_templates.mkdir()
    (default_templates / 'items.html').write_text(TEMPLATE_USING_TO_JSON)
    monkeypatch.setattr(util, 'TEMPLATES', str(default_templates))

    custom_templates = tmp_path / 'custom'
    custom_templates.mkdir()
    (custom_templates / 'items.html').write_text('custom')

    config = {'server': {'templates': {'path': str(custom_templates)}}}

    assert util.render_j2_template(config, 'items.html', {}) == 'custom'


def test_render_j2_template_fallback_keeps_filters(tmp_path, monkeypatch):
    """a template missing from templates.path falls back to the default
    templates, which must keep the to_json filter registered"""

    default_templates = tmp_path / 'default'
    default_templates.mkdir()
    (default_templates / 'items.html').write_text(TEMPLATE_USING_TO_JSON)
    monkeypatch.setattr(util, 'TEMPLATES', str(default_templates))

    custom_templates = tmp_path / 'custom'
    custom_templates.mkdir()
    (custom_templates / 'item.html').write_text('custom')

    config = {'server': {'templates': {'path': str(custom_templates)}}}

    assert util.render_j2_template(config, 'items.html', {}) == '{}'
