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
        "--suite",
        action="append",
        choices=FUNCTIONAL_SUITES,
        default=[],
        help="Suites to run functional tests against. Specify this parameter "
             "multiple times in order to include several suites. If not "
             "specified, all available suites are tested"
    )


def pytest_generate_tests(metafunc):
    """Parametrize tests programatically.

    Check pytest's documentation for information on this function:

    http://pytest.org/latest/parametrize.html#basic-pytest-generate-tests-example

    """

    expected_dir = os.path.join(TESTS_ROOT, "expected")
    if metafunc.function.__name__ == "test_suites_post":
        test_data, test_names = _configure_functional_post_tests(metafunc,
                                                                 expected_dir)
        metafunc.parametrize(["test_request", "expected_result", "config"],
                             test_data, ids=test_names)


def _configure_functional_post_tests(metafunc, expected_dir):
    test_data = []
    test_names = []
    for suite in metafunc.config.getoption("suite") or FUNCTIONAL_SUITES:
        suite_dir = os.path.join(TESTS_ROOT, "suites", suite)
        configuration_path = os.path.join(suite_dir, "default.cfg")
        post_requests_dir = os.path.join(suite_dir, "post")
        for item in glob.iglob(os.path.join(post_requests_dir, "*")):
            test_id = os.path.splitext(os.path.basename(item))[0]
            expected = os.path.join(
                expected_dir, "suites_{0}_post_{1}.xml".format(suite, test_id))
            if os.path.isfile(item) and os.path.isfile(expected):
                test_data.append((item, expected, configuration_path))
                test_names.append("{0}_{1}".format(suite, test_id))
    return test_data, test_names


@pytest.fixture(scope="session")
def local_server(request):
    """A local pycsw server using Python's wsgiref server"""

    port = random.randint(8000, 8050)
    command = "python pycsw/wsgi.py {}".format(port)
    working_dir = os.path.dirname(TESTS_ROOT)
    pycsw_process = subprocess.Popen(shlex.split(command), cwd=working_dir)
    time.sleep(2)  # give the external process some time to start

    def finalizer():
        pycsw_process.terminate()
        pycsw_process.wait()

    request.addfinalizer(finalizer)
    return "http://localhost:{}".format(port)

