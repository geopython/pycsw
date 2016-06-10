"""pytest configuration file"""

from configparser import ConfigParser
import glob
import os
import subprocess
import shlex
import time

import pytest

from pycsw.core import admin
from pycsw.core.config import StaticContext

TESTS_ROOT = os.path.dirname(os.path.abspath(__file__))


# This dict holds the names of the suites that are available for functional
# testing and also if they use a custom database or not. If a suite has a
# custom database, then a new db is created and possibly loaded with the suite's
# test data (if there is any test data). If a suite does not use a custom db,
# then it means that its tests it will have a database loaded with records
# from the CITE suite
# If you omit the "has_own_db" key from a suite's dict, it is assumed that
# the value is False
FUNCTIONAL_SUITES = {
    "apiso": {"has_own_db": True},
    "apiso-inspire": {},
    "atom": {},
    "cite": {"has_own_db": True},
    "csw30": {},
    "default": {},
    "dif": {},
    "ebrim": {},
    "fgdc": {},
    "gm03": {},
    "harvesting": {"has_own_db": True},
    "manager": {"has_own_db": True},
    "oaipmh": {},
    "repofilter": {},
    "sru": {},
    "utf-8": {},
}


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
    for suite_name in FUNCTIONAL_SUITES.keys():
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
    for suite_name in FUNCTIONAL_SUITES.keys():
        safe_suite_name = _get_suite_safe_name(suite_name)
        fixture_name = "server_{0}_suite".format(safe_suite_name)
        uses_fixture = fixture_name in metafunc.fixturenames
        test_name_post = "test_post_requests"
        test_name_get = "test_get_requests"
        test_name_get_matches = metafunc.function.__name__ == test_name_get
        test_name_post_matches = metafunc.function.__name__ == test_name_post
        if uses_fixture and test_name_post_matches:
            test_data, test_names = _configure_functional_post_tests(
                expected_dir, safe_suite_name)
            metafunc.parametrize(
                ["test_request", "expected_result"],
                test_data,
                ids=test_names,
                scope="session"
            )
            break
        elif uses_fixture and test_name_get_matches:
            test_data, test_names = _configure_functional_get_tests(
                expected_dir, suite_name)
            metafunc.parametrize(
                ["test_request_parameters", "expected_result"],
                test_data,
                ids=test_names,
                scope="session"
            )
            break


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
def server_manager_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "manager",
                                   tmpdir_factory, 8021)


@pytest.fixture(scope="session")
def server_oaipmh_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "oaipmh",
                                   tmpdir_factory, 8022)


@pytest.fixture(scope="session")
def server_repofilter_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "repofilter",
                                   tmpdir_factory, 8023)


@pytest.fixture(scope="session")
def server_sru_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "sru",
                                   tmpdir_factory, 8024)


@pytest.fixture(scope="session")
def server_utf_8_suite(request, tmpdir_factory):
    return _get_server_with_config(request, "utf-8",
                                   tmpdir_factory, 8025)


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


def _configure_functional_get_tests(expected_dir, suite_name):
    test_data = []
    test_names = []
    request_file_path = os.path.join(TESTS_ROOT, "suites", suite_name,
                                     "get", "requests.txt")
    try:
        with open(request_file_path, encoding="utf-8") as fh:
            for line in fh:
                test_name, sep, test_params = line.partition(",")
                expected = os.path.join(
                    expected_dir,
                    "suites_{0}_get_{1}.xml".format(suite_name, test_name)
                )
                if os.path.isfile(expected):
                    test_data.append((test_params.strip(), expected))
                    test_names.append("{0}_{1}".format(suite_name, test_name))
    except FileNotFoundError:
        pass  # this suite does not have GET tests
    return test_data, test_names


def _get_suite_safe_name(suite_name):
    return suite_name.replace("-", "_")


def _get_server_with_config(request, suite_name, tmpdir_factory, port_number):
    """Provide a pycsw server to execute tests for the input suite name

    This function introspects the test context. If tests are to be run against
    a user-provided url, it does nothing. If there is no user-provided url,
    a new pycsw instance is created locally and its URL is returned.

    Parameters
    ----------
    request: FixtureRequest
        Pytest's FixtureRequest object, holding information about the test
        context
    suite_name: str
        The safe name of the current suite
    tmpdir_factory: TempDirFactory
        Pytest's TempDirFactory fixture object, that is used to create
        temporary directories for tests
    port_number: int
        Port where a local server shall be started for the input suite_name

    Returns
    -------
    str
        The pycsw URL that can be used in tests for the input suite_name

    """

    url = request.config.getoption("--server-url-{0}-suite".format(suite_name))
    if url is None:
        print("Initializing server for {0!r} suite...".format(suite_name))
        original_config_path = os.path.join(TESTS_ROOT, "suites",
                                            suite_name, "default.cfg")
        config = ConfigParser()
        config.read(original_config_path)
        #safe_suite_name = _get_suite_safe_name(suite_name)
        test_temp_directory = tmpdir_factory.mktemp(suite_name,
                                                    numbered=True)
        db_url = _initialize_database(
            request, suite_name, test_temp_directory,
            config.get("repository", "table"),
            os.path.join(TESTS_ROOT, "suites", suite_name, "data")
        )
        # now we can change the config as needed
        config.set("repository", "database", db_url)
        new_config = test_temp_directory.join("default.cfg")
        fh = new_config.open("w")
        config.write(fh)
        fh.close()
        server_url = _start_local_server(request, str(new_config), port_number)
    else:  # use the provided url and assume the config has been set
        server_url = url
    return server_url


def _initialize_database(request, suite_name, test_dir, table_name, data_path):
    """Initialize local database for functional tests.

    This function will:

    * Configure the correct database url
    * Create the database
    * Load any test data that the suite may require

    Parameters
    ----------
    request: FixtureRequest
        Pytest's FixtureRequest object, holding information about the test
        context
    suite_name: str
        The name of the current suite
    test_dir: str
        Full path to the temporary directory being used in the suite's tests
    data_path: str
        Full path to a directory that has test data to be loaded up into
        the suite's database

    Returns
    -------
    str
        The SQLAlchemy engine URL for the database.

    """

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
    print("Setting up {0!r} database for suite {1!r}...".format(db_type,
                                                          suite_name))
    admin.setup_db(db_url, table_name, test_dir)
    print("Loading database data...")
    if not FUNCTIONAL_SUITES[suite_name].get("has_own_db", False):
        print("Loading CITE data into database...")
        cite_data_dir = os.path.join(TESTS_ROOT, "suites", "cite", "data")
        data_path = cite_data_dir
    admin.load_records(StaticContext(), db_url, table_name, data_path)
    return db_url


def _start_local_server(request, config_path, port_number):
    """Start a local pycsw instance

    This function starts a new pycsw instance and also
    registers a pytest finalizer function that takes care of stopping the
    server when the tests are finished.

    Parameters
    ----------

    request: FixtureRequest
        Pytest's FixtureRequest object, holding information about the test
        context
    config_path: str
        Full path to pycsw's configuration file
    port_number: int
        Port where the server will be listening

    Returns
    -------
    str
        The URL of the newly started pycsw instance

    """

    command = "python pycsw/wsgi.py {}".format(port_number)
    working_dir = os.path.dirname(TESTS_ROOT)
    env = os.environ.copy()
    env["PYCSW_CONFIG"] = config_path
    pycsw_process = subprocess.Popen(shlex.split(command), cwd=working_dir,
                                     stdout=subprocess.PIPE,
                                     env=env)
    time.sleep(3)  # give the external process some time to start

    def finalizer():
        pycsw_process.terminate()
        pycsw_process.wait()

    request.addfinalizer(finalizer)
    return "http://localhost:{}".format(port_number)
