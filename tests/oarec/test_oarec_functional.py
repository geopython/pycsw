import json
import os

import pytest

from pycsw.core.util import parse_ini_config
from pycsw.ogc.api.records import API

pytestmark = [
    pytest.mark.functional,
    pytest.mark.oarec
]


def get_test_file_path(filename):
    """helper function to open test file safely"""

    if os.path.isfile(filename):
        return filename
    else:
        return f'tests/oarec/{filename}'


def test_landing_page():

    api_ = API(parse_ini_config(get_test_file_path('oarec-default.cfg')))

    headers, status, content = api_.landing_page({}, {'f': 'json'})
    content = json.loads(content)

    assert headers['Content-Type'] == 'application/json'
    assert status == 200
    assert len(content['links']) == 10
