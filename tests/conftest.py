"""pytest configuration file"""

from configparser import ConfigParser
import glob
import os
import subprocess
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
        safe_suite_name = _get_suite_safe_name(suite_name)
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
def server_apiso_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "apiso",
                                   tmpdir_factory, 8010)


@pytest.fixture(scope="session")
def server_apiso_inspire_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "apiso-inspire",
                                   tmpdir_factory, 8011)


@pytest.fixture(scope="session")
def server_atom_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "atom",
                                   tmpdir_factory, 8012)


@pytest.fixture(scope="session")
def server_cite_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "cite",
                                   tmpdir_factory, 8013)


@pytest.fixture(scope="session")
def server_csw30_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "csw30",
                                   tmpdir_factory, 8014)


@pytest.fixture(scope="session")
def server_default_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "default",
                                   tmpdir_factory, 8015)


@pytest.fixture(scope="session")
def server_dif_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "dif",
                                   tmpdir_factory, 8016)


@pytest.fixture(scope="session")
def server_ebrim_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "ebrim",
                                   tmpdir_factory, 8017)


@pytest.fixture(scope="session")
def server_fgdc_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "fgdc",
                                   tmpdir_factory, 8018)


@pytest.fixture(scope="session")
def server_gm03_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "gm03",
                                   tmpdir_factory, 8019)


@pytest.fixture(scope="session")
def server_harvesting_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "harvesting",
                                   tmpdir_factory, 8020)


@pytest.fixture(scope="session")
def server_oaipmh_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "oaipmh",
                                   tmpdir_factory, 8021)


@pytest.fixture(scope="session")
def server_repofilter_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "repofilter",
                                   tmpdir_factory, 8022)


@pytest.fixture(scope="session")
def server_sru_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "sru",
                                   tmpdir_factory, 8023)


@pytest.fixture(scope="session")
def server_utf_8_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "utf-8",
                                   tmpdir_factory, 8024)


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


def _get_suite_safe_name(suite_name):
    return suite_name.replace("-", "_")


def _get_server_with_config(request, suite_name, tmpdir_factory, port_number):
    url = request.config.getoption("--server-url-{0}-suite".format(suite_name))
    if url is None:
        print("Initializing server for {0} suite...".format(suite_name))
        original_config_path = os.path.join(TESTS_ROOT, "suites",
                                            suite_name, "default.cfg")
        safe_suite_name = _get_suite_safe_name(suite_name)
        config = ConfigParser()
        config.read(original_config_path)
        test_temp_directory = tmpdir_factory.mktemp(safe_suite_name,
                                                    numbered=True)
        db_url = _get_database_url(request, safe_suite_name,
                                   test_temp_directory)
        # now we can change the config as needed
        config.set("repository", "database", db_url)
        new_config = test_temp_directory.join("default.cfg")
        fh = new_config.open("w")
        config.write(fh)
        fh.close()
        # create the database, if needed
        # load records, if any
        url = _start_local_server(request, str(new_config), port_number)
    else:  # use the provided url and assume the config has been set
        url = url
    return url


def _get_database_url(request, suite_name, test_dir):
    db_type = request.config.getoption("--database-backend")
    if db_type == "sqlite":
        db_url = "sqlite:///{0}/records.db".format(test_dir)
    elif db_type == "postgres":
        user = request.config.getoption("--database-user-postgres")
        password = request.config.getoption("--database-password-postgres")
        db_url = "postgres://{0}:{1}@localhost/pycsw_test_{2}".format(
            user, password, suite_name)
    else:
        raise NotImplementedError
    return db_url


def _start_local_server(request, config_path, port_number):
    command = "python pycsw/wsgi.py {}".format(port_number)
    working_dir = os.path.dirname(TESTS_ROOT)
    env = os.environ.copy()
    env["PYCSW_CONFIG"] = config_path
    pycsw_process = subprocess.Popen(shlex.split(command), cwd=working_dir,
                                     env=env)
    time.sleep(3)  # give the external process some time to start

    def finalizer():
        pycsw_process.terminate()
        pycsw_process.wait()

    request.addfinalizer(finalizer)
    return "http://localhost:{}".format(port_number)
