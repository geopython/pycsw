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
import configparser

import pytest

from pycsw import wsgi_flask


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
    config.addinivalue_line(
        "markers",
        "oarec: Run only tests pertaining to OGC API Records support"
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


@pytest.fixture
def oarec_config():
    config = configparser.ConfigParser()
    config["server"] = {
        "home": ".",
        "url": "http://localhost",
        "mimetype": "application/xml;",
        "charset": "UTF-8",
        "encoding": "UTF-8",
        "language": "en-US",
        "maxrecords": 10,
        "federatedcatalogues": "http://geo.data.gov/geoportal/csw/discovery",
        "pretty_print": True,
    }
    config["manager"] = {
        "transactions": False,
        "allowed_ips": "127.0.0.1",
    }
    config["metadata:main"] = {
        "identification_title": "pycsw Geospatial Catalogue",
        "identification_abstract": "pycsw is an OGC CSW server implementation written in Python",
        "identification_keywords": "catalogue,discovery",
        "identification_keywords_type": "theme",
        "identification_fees": "None",
        "identification_accessconstraints": "None",
        "provider_name": "pycsw",
        "provider_url": "https://pycsw.org/",
        "contact_name": "Kralidis, Tom",
        "contact_position": "Senior Systems Scientist",
        "contact_address": "TBA",
        "contact_city": "Toronto",
        "contact_stateorprovince": "Ontario",
        "contact_postalcode": "M9C 3Z9",
        "contact_country": "Canada",
        "contact_phone": "+01-416-xxx-xxxx",
        "contact_fax": "+01-416-xxx-xxxx",
        "contact_email": "tomkralidis@gmail.com",
        "contact_url": "http://kralidis.ca/",
        "contact_hours": "0800h - 1600h EST",
        "contact_instructions": "During hours of service.  Off on weekends.",
        "contact_role": "pointOfContact",
    }
    config["repository"] = {
        "database": "sqlite:///tests/functionaltests/suites/cite/data/cite.db",
        "table": "records",
    }
    config["metadata:inspire"] = {
        "enabled": False,
        "languages_supported": "eng,gre",
        "default_language": "eng",
        "date": "2011-03-29",
        "gemet_keywords": "Utility and governmental services",
        "conformity_service": "notEvaluated",
        "contact_name": "National Technical University of Athens",
        "contact_email": "tzotsos@gmail.com",
        "temp_extent": "2011-02-01/2011-03-30",
    }
    return config


@pytest.fixture
def flask_client():
    wsgi_flask.APP.config['TESTING'] = True
    with wsgi_flask.APP.test_client() as client:
        yield client


@pytest.fixture
def oarec_client(oarec_config):
    previous_config = wsgi_flask.APP.config.copy()
    wsgi_flask.APP.config['TESTING'] = True
    wsgi_flask.APP.config['PYCSW_CONFIG'] = oarec_config
    with wsgi_flask.APP.test_client() as client:
        yield client
    wsgi_flask.APP.config = previous_config