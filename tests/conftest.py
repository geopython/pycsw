# =================================================================
#
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2016 Ricardo Garcia Silva
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
"""pytest configuration file"""

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "functional: Run only functional tests"
    )
    config.addinivalue_line(
        "markers",
        "unit: Run only unit tests"
    )


def pytest_addoption(parser):
    parser.addoption(
        "--database-backend",
        choices=["sqlite", "postgres"],
        default="sqlite",
        help="Database backend to use when performing functional tests"
    )
    parser.addoption(
        "--database-user-postgres",
        default="postgres",
        help="Username to use for creating and accessing local postgres "
             "databases used for functional tests."
    )
    parser.addoption(
        "--database-password-postgres",
        default="",
        help="Password to use for creating and accessing local postgres "
             "databases used for functional tests."
    )
    parser.addoption(
        "--pycsw-loglevel",
        default="warning",
        help="Log level for the pycsw server."
    )


@pytest.fixture(scope="session")
def log_level(request):
    return request.config.getoption("pycsw_loglevel").upper()
