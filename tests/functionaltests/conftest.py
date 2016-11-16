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
"""pytest configuration file for functional tests"""

import codecs
from collections import namedtuple
import os
from six.moves import configparser

import pytest

from pycsw.core import admin
from pycsw.core.config import StaticContext

TESTS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SuiteDirs = namedtuple("SuiteDirs", [
    "get_tests_dir",
    "post_tests_dir",
    "data_tests_dir",
    "expected_results_dir",
])



def pytest_generate_tests(metafunc):
    """Parametrize tests programatically.

    Check pytest's documentation for information on this function:

    http://pytest.org/latest/parametrize.html#basic-pytest-generate-tests-example

    """

    global TESTS_ROOT
    if metafunc.function.__name__ == "test_suites":
        suites_root_dir = os.path.join(TESTS_ROOT, "functionaltests", "suites")
        suite_names = os.listdir(suites_root_dir)
        arg_values = []
        test_ids = []
        for suite in suite_names:
            normalize_ids = True if suite in ("harvesting",
                                              "manager") else False
            suite_dir = os.path.join(suites_root_dir, suite)
            config_path = os.path.join(suite_dir, "default.cfg")
            if not os.path.isfile(config_path):
                print("Directory {0!r} does not have a suite "
                      "configuration file".format(suite_dir))
                continue
            else:
                print("Generating tests for suite {0!r}".format(suite))
                suite_dirs = _get_suite_dirs(suite)
                if suite_dirs.post_tests_dir is not None:
                    post_argvalues, post_ids = _get_post_parameters(
                        post_tests_dir=suite_dirs.post_tests_dir,
                        expected_tests_dir=suite_dirs.expected_results_dir,
                        config_path=config_path,
                        suite_name=suite,
                        normalize_ids=normalize_ids
                    )
                    arg_values.extend(post_argvalues)
                    test_ids.extend(post_ids)
                if suite_dirs.get_tests_dir is not None:
                    get_argvalues, get_ids = _get_get_parameters(
                        get_tests_dir=suite_dirs.get_tests_dir,
                        expected_tests_dir=suite_dirs.expected_results_dir,
                        config_path=config_path,
                        suite_name=suite,
                        normalize_ids=normalize_ids
                    )
                    arg_values.extend(get_argvalues)
                    test_ids.extend(get_ids)
        metafunc.parametrize(
            argnames=["configuration", "request_method", "request_data",
                      "expected_result", "normalize_identifier_fields"],
            argvalues=arg_values,
            indirect=["configuration"],
            ids=test_ids,
        )


def _get_get_parameters(get_tests_dir, expected_tests_dir, config_path,
                        suite_name, normalize_ids):
    method = "GET"
    test_argvalues = []
    test_ids = []
    requests_file_path = os.path.join(get_tests_dir, "requests.txt")
    with open(requests_file_path) as fh:
        for line in fh:
            test_name, test_params = [i.strip() for i in
                                      line.partition(",")[::2]]
            expected_result_path = os.path.join(
                expected_tests_dir,
                "{method}_{name}.xml".format(method=method.lower(),
                                             name=test_name)
            )
            test_argvalues.append(
                (config_path, method, test_params, expected_result_path,
                 normalize_ids)
            )
            test_ids.append(
                "{suite}_{http_method}_{name}".format(suite=suite_name,
                    http_method=method.lower(), name=test_name)
            )
    return test_argvalues, test_ids


def _get_post_parameters(post_tests_dir, expected_tests_dir, config_path,
                         suite_name, normalize_ids):
    method = "POST"
    test_argvalues = []
    test_ids = []
    # we are sorting the directory contents because the
    # `harvesting` suite requires tests to be executed in alphabetical order
    directory_contents = sorted(os.listdir(post_tests_dir))
    for request_file_name in directory_contents:
        request_path = os.path.join(post_tests_dir,
                                    request_file_name)
        expected_result_path = os.path.join(
            expected_tests_dir,
            "{method}_{filename}".format(
                method=method.lower(),
                filename=request_file_name
            )
        )
        # TODO - make sure the expected result path exists
        test_argvalues.append(
            (config_path, method, request_path,
             expected_result_path, normalize_ids)
        )
        test_ids.append(
            "{suite}_{http_method}_{file_name}".format(
                suite=suite_name,
                http_method=method.lower(),
                file_name=os.path.splitext(
                    request_file_name)[0])
        )
    return test_argvalues, test_ids


@pytest.fixture()
def configuration(request, tests_directory, log_level):
    """Return a SafeConfigParser with the configuration for use in tests.

    The config_parser is read from the ordiginal location and then adjusted
    to match the test's temporary directory. The repository will also be
    created and populated if it is not already present in the tests_directory.

    """

    config_path = request.param
    config = configparser.SafeConfigParser()
    with codecs.open(config_path, encoding="utf-8") as fh:
        config.readfp(fh)
    suite_name = config_path.split(os.path.sep)[-2]
    suite_dirs = _get_suite_dirs(suite_name)
    data_dir = suite_dirs.data_tests_dir
    if data_dir is not None:  # suite has its own database
        repository_url = _get_repository_url(request, suite_name,
                                             tests_directory)
    else:  # suite uses the CITE database
        data_dir = _get_cite_suite_data_dir()
        repository_url = _get_repository_url(request, "cite", tests_directory)
    if not _repository_exists(repository_url):
        _initialize_database(repository_url=repository_url,
                             table_name=config.get("repository", "table"),
                             data_dir=data_dir,
                             test_dir=tests_directory)
    config.set("server", "loglevel", log_level)
    config.set("server", "logfile", "")
    config.set("repository", "database", repository_url)
    return config


@pytest.fixture(scope="session", name="tests_directory")
def fixture_tests_directory(tmpdir_factory):
    tests_dir = tmpdir_factory.mktemp("functional_tests")
    return tests_dir


def _get_suite_dirs(suite_name):
    """Return a tuple with suite dirs: get, post, data, expected"""
    global TESTS_ROOT
    suites_root_dir = os.path.join(TESTS_ROOT, "functionaltests", "suites")
    suite_dir = os.path.join(suites_root_dir, suite_name)
    data_tests_dir = os.path.join(suite_dir, "data")
    post_tests_dir = os.path.join(suite_dir, "post")
    get_tests_dir = os.path.join(suite_dir, "get")
    expected_results_dir = os.path.join(suite_dir, "expected")
    data_dir = data_tests_dir if os.path.isdir(data_tests_dir) else None
    posts_dir = post_tests_dir if os.path.isdir(post_tests_dir) else None
    gets_dir = get_tests_dir if os.path.isdir(get_tests_dir) else None
    expected_dir = (expected_results_dir if os.path.isdir(
        expected_results_dir) else None)
    return SuiteDirs(get_tests_dir=gets_dir,
                     post_tests_dir=posts_dir,
                     data_tests_dir=data_dir,
                     expected_results_dir=expected_dir)


def _get_cite_suite_data_dir():
    global TESTS_ROOT
    suites_root_dir = os.path.join(TESTS_ROOT, "functionaltests", "suites")
    suite_dir = os.path.join(suites_root_dir, "cite")
    data_tests_dir = os.path.join(suite_dir, "data")
    data_dir = data_tests_dir if os.path.isdir(data_tests_dir) else None
    return data_dir


def _repository_exists(repository_url):
    """Test if the database already exists"""
    if repository_url.startswith("sqlite"):
        repository_path = repository_url.replace("sqlite:///", "")
        result = os.path.isfile(repository_path)
    else:
        raise NotImplementedError
    return result


def _get_repository_url(request, suite_name, test_dir):
    db_type = request.config.getoption("--database-backend")
    if db_type == "sqlite":
        repository_url = "sqlite:///{test_dir}/{suite}.db".format(
            test_dir=test_dir, suite=suite_name)
    elif db_type == "postgres":
        user = request.config.getoption("--database-user-postgres")
        password = request.config.getoption("--database-password-postgres")
        repository_url = ("postgres://{user}:{password}@localhost/"
                          "pycsw_test_{suite}".format(user=user,
                                                      password=password,
                                                      suite=suite_name))
    else:
        raise NotImplementedError
    return repository_url


def _initialize_database(repository_url, table_name, data_dir, test_dir):
    """Initialize local database for tests.

    This function will create the database and load any test data that
    the suite may require.

    """

    print("Setting up {0!r} repository...".format(repository_url))
    admin.setup_db(repository_url, table_name, test_dir)
    if len(os.listdir(data_dir)) > 0:
        print("Loading database data...")
        admin.load_records(StaticContext(), repository_url, table_name,
                           data_dir)
