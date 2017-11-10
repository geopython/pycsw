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
    """Configure pytest.

    This function adds additional markers to pytest.

    """

    config.addinivalue_line(
        "markers",
        "functional: Run only functional tests"
    )
    config.addinivalue_line(
        "markers",
        "unit: Run only unit tests"
    )


def pytest_addoption(parser):
    """Add additional command-line parameters to pytest."""
    parser.addoption(
        "--database-backend",
        choices=["sqlite", "postgresql"],
        default="sqlite",
        help="Database backend to use when performing functional tests"
    )
    parser.addoption(
        "--database-user-postgresql",
        default="postgres",
        help="Username to use for creating and accessing local postgres "
             "databases used for functional tests."
    )
    parser.addoption(
        "--database-password-postgresql",
        default="",
        help="Password to use for creating and accessing local postgres "
             "databases used for functional tests."
    )
    parser.addoption(
        "--database-name-postgresql",
        default="test_pycsw",
        help="Name of the postgres database that is to be used for testing."
    )
    parser.addoption(
        "--database-host-postgresql",
        default="127.0.0.1",
        help="hostname or ip of the host that is running the postgres "
             "database server to use in testing."
    )
    parser.addoption(
        "--database-port-postgresql",
        default="5432",
        help="Port where the postgres server is listening for connections."
    )
    parser.addoption(
        "--pycsw-loglevel",
        default="warning",
        help="Log level for the pycsw server."
    )
    parser.addoption(
        "--functional-prefer-diffs",
        action="store_true",
        help="When running functional tests, compare results with their "
             "expected values by using diffs instead of XML canonicalisation "
             "(the default)."
    )
    parser.addoption(
        "--functional-save-results-directory",
        help="When running functional tests, save each test's result under "
             "the input directory path."
    )


@pytest.fixture(scope="session")
def log_level(request):
    """Log level to use when instantiating a new pycsw server.

    The value for this fixture is retrieved from the `--pycsw.loglevel`
    command-line parameter.

    """

    return request.config.getoption("pycsw_loglevel").upper()
