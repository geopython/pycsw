"""pytest configuration file"""

import glob
import os
import subprocess
import random
import shlex
import time

import pytest

TESTS_ROOT = os.path.dirname(os.path.abspath(__file__))


# This list holds the names of the suites that are available for functional
# testing
FUNCTIONAL_SUITES = [
    "apiso",
    "apiso-inspire",
    "atom",
    "cite",
    "csw30",
    "default",
    "dif",
    "ebrim",
    "fgdc",
    "gm03",
    "harvesting",
    "oaipmh",
    "repofilter",
    "sru",
    "utf-8",
]


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "functional: Run only functional tests"
    )


def pytest_addoption(parser):
    parser.addoption(
        "--database-backend",
        choices=["sqlite", "postgres"],
        default="sqlite",
        help="Database backend to use when performing functional tests"
    )
    for suite_name in FUNCTIONAL_SUITES:
        parser.addoption(
            "--server-url-{0}-suite".format(suite_name),
            help="URL to perform functional tests for the {0!r} suite. If not "
                 "specified, a local pycsw instance is spawned, configured "
                 "with the {0!r} suite settings and used "
                 "in tests.".format(suite_name)
        )


def pytest_generate_tests(metafunc):
    """Parametrize tests programatically.

    Check pytest's documentation for information on this function:

    http://pytest.org/latest/parametrize.html#basic-pytest-generate-tests-example

    """

    expected_dir = os.path.join(TESTS_ROOT, "expected")
    for suite_name in FUNCTIONAL_SUITES:
        safe_suite_name = suite_name.replace("-", "_")
        option_name = "--server-url-{0}-suite".format(suite_name)
        fixture_name = "server_{0}_suite".format(safe_suite_name)
        test_name = "test_{0}_suite".format(safe_suite_name)
        uses_fixture = fixture_name in metafunc.fixturenames
        test_name_matches = metafunc.function.__name__ == test_name
        if uses_fixture and test_name_matches:
            test_data, test_names = _configure_functional_post_tests(
                expected_dir, safe_suite_name)
            metafunc.parametrize(
                ["test_request", "expected_result"],
                test_data,
                ids=test_names,
                scope="session"
            )
            break


@pytest.fixture(scope="session")
def suite_info(request):
    suite_name = request.param
    test_data = []
    test_names = []
    expected_dir = os.path.join(TESTS_ROOT, "expected")
    suite_dir = os.path.join(TESTS_ROOT, "suites", suite_name)
    configuration_path = os.path.join(suite_dir, "default.cfg")
    post_requests_dir = os.path.join(suite_dir, "post")
    for item in glob.iglob(os.path.join(post_requests_dir, "*")):
        test_id = os.path.splitext(os.path.basename(item))[0]
        expected = os.path.join(
            expected_dir,
            "suites_{0}_post_{1}.xml".format(suite_name, test_id)
        )
        if os.path.isfile(item) and os.path.isfile(expected):
            test_data.append((item, expected, configuration_path))
            test_names.append("{0}_{1}".format(suite_name, test_id))
    return configuration_path, test_data, test_names


@pytest.fixture(scope="session")
def server_apiso_suite(request):
    return _get_server_with_config(request, "apiso")


@pytest.fixture(scope="session")
def server_apiso_inspire_suite(request):
    return _get_server_with_config(request, "apiso-inspire")


@pytest.fixture(scope="session")
def server_atom_suite(request):
    return _get_server_with_config(request, "atom")


@pytest.fixture(scope="session")
def server_cite_suite(request):
    return _get_server_with_config(request, "cite")


@pytest.fixture(scope="session")
def server_csw30_suite(request):
    return _get_server_with_config(request, "csw30")


@pytest.fixture(scope="session")
def server_default_suite(request):
    return _get_server_with_config(request, "default")


@pytest.fixture(scope="session")
def server_dif_suite(request):
    return _get_server_with_config(request, "dif")


@pytest.fixture(scope="session")
def server_ebrim_suite(request):
    return _get_server_with_config(request, "ebrim")


@pytest.fixture(scope="session")
def server_fgdc_suite(request):
    return _get_server_with_config(request, "fgdc")


@pytest.fixture(scope="session")
def server_gm03_suite(request):
    return _get_server_with_config(request, "gm03")


@pytest.fixture(scope="session")
def server_harvesting_suite(request):
    return _get_server_with_config(request, "harvesting")


@pytest.fixture(scope="session")
def server_oaipmh_suite(request):
    return _get_server_with_config(request, "oaipmh")


@pytest.fixture(scope="session")
def server_repofilter_suite(request):
    return _get_server_with_config(request, "repofilter")


@pytest.fixture(scope="session")
def server_sru_suite(request):
    return _get_server_with_config(request, "sru")


@pytest.fixture(scope="session")
def server_utf_8_suite(request):
    return _get_server_with_config(request, "utf-8")


def _configure_functional_post_tests(expected_dir, suite_name):
    test_data = []
    test_names = []
    suite_dir = os.path.join(TESTS_ROOT, "suites", suite_name)
    post_requests_dir = os.path.join(suite_dir, "post")
    for item in glob.iglob(os.path.join(post_requests_dir, "*")):
        test_id = os.path.splitext(os.path.basename(item))[0]
        expected = os.path.join(
            expected_dir,
            "suites_{0}_post_{1}.xml".format(suite_name, test_id)
        )
        if os.path.isfile(item) and os.path.isfile(expected):
            test_data.append((item, expected))
            test_names.append("{0}_{1}".format(suite_name, test_id))
    return test_data, test_names


def _get_server_with_config(request, suite_name):
    url = request.config.getoption("--server-url-{0}-suite".format(suite_name))
    config = os.path.join(TESTS_ROOT, "suites", suite_name, "default.cfg")
    if url is None:
        url = _start_local_server(request, config)
    else:  # use the provided url and assume the config has been set
        url = url
    return url


def _start_local_server(request, config_path):
    port = random.randint(8000, 8050)
    command = "python pycsw/wsgi.py {}".format(port)
    working_dir = os.path.dirname(TESTS_ROOT)
    env = os.environ.copy()
    env["PYCSW_CONFIG"] = config_path
    pycsw_process = subprocess.Popen(shlex.split(command), cwd=working_dir,
                                     env=env)
    time.sleep(2)  # give the external process some time to start

    def finalizer():
        pycsw_process.terminate()
        pycsw_process.wait()

    request.addfinalizer(finalizer)
    return "http://localhost:{}".format(port)
