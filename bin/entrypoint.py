#!/usr/bin/env python3

"""Entrypoint script for docker containers.

This module serves as the entrypoint for docker containers. Its main
purpose is to set up the pycsw database so that newly generated
containers may be useful soon after being launched, without requiring
additional input.

"""


import argparse
from collections import namedtuple
import logging
import os
from six.moves.configparser import SafeConfigParser
from subprocess import call
from subprocess import PIPE
from time import sleep

from pycsw.core import admin

logger = logging.getLogger(__name__)

DatabaseParameters = namedtuple("DatabaseParameters", [
    "host",
    "port",
    "user",
    "password",
    "path"
])


def launch_pycsw(gunicorn_workers=2):
    logger.debug("Reading pycsw config...")
    config = SafeConfigParser()
    config.read("/etc/pycsw/pycsw.cfg")
    db_url = config.get("repository", "database")
    db = db_url.partition(":")[0].partition("+")[0]
    db_handler = {
        "sqlite": handle_sqlite_db,
        "postgresql": handle_postgresql_db,
    }.get(db)
    logger.debug("Setting up pycsw's data repository...")
    logger.debug("Repository URL: {}".format(db_url))
    db_handler(db_url, config.get("repository", "table"))
    logger.debug("Launching pycsw...")
    pycsw_server_command = [
        "gunicorn",
        "--bind=0.0.0.0:8000",
        "--access-logfile=-",
        "--error-logfile=-",
        "--workers={}".format(gunicorn_workers)
    ]
    pycsw_server_command.append("--workers={}".format(gunicorn_workers))
    pycsw_server_command.append("pycsw.wsgi")
    call(pycsw_server_command)


def handle_sqlite_db(database_url, table_name):
    db_path = database_url.rpartition(":///")[-1]
    if not os.path.isfile(db_path):
        try:
            os.makedirs(os.path.dirname(db_path))
        except OSError as exc:
            if exc.args[0] == 17:  # directory already exists
                pass
        _create_pycsw_schema(database_url, table_name)


def handle_postgresql_db(database_url, table_name):
    db_params = _extract_postgres_url_params(database_url)
    _wait_for_network_service(db_params.host, db_params.port)
    # - set up the db with pycsw-admin if needed
    _create_pycsw_schema(database_url, table_name)


def _extract_postgres_url_params(database_url):
    db_params = database_url.partition("://")[-1]
    rest, db_name = db_params.rpartition("/")[::2]
    user_params, host_params = rest.partition("@")[::2]
    user, password = user_params.partition(":")[::2]
    host, port = host_params.partition(":")[::2]
    port = port if port != "" else "5432"
    return DatabaseParameters(host, port, user, password, db_name)


def _create_pycsw_schema(database_url, table):
    admin.setup_db(database=database_url, table=table, home="/home/pycsw")


def _wait_for_network_service(host, port, max_tries=10, wait_seconds=3):
    logger.debug("Waiting for {!r}:{!r}...".format(host, port))
    current_try = 0
    while current_try < max_tries:
        return_code = call(
            ["nc", "-z", str(host), str(port)], stdout=PIPE, stderr=PIPE)
        if int(return_code) == 0:
            logger.debug("{!r}:{!r} is already up!".format(host, port))
            break
        else:
            current_try += 1
            sleep(wait_seconds)
    else:
        raise RuntimeError("Could not find {}:{} after {} tries. "
                           "Giving up".format(host, port, max_tries))



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--workers",
        default=2,
        help="Number of workers to use by the gunicorn server. Defaults to 2."
    )
    args, remaining_args = parser.parse_known_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING)
    launch_pycsw(gunicorn_workers=args.workers)
