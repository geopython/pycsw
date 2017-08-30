#!/usr/bin/env python3

"""Entrypoint script for docker containers.

This module serves as the entrypoint for docker containers. Its main
purpose is to set up the pycsw database so that newly generated
containers may be useful soon after being launched, without requiring
additional input.

"""


import argparse
import logging
import os
from six.moves.configparser import SafeConfigParser
from subprocess import call
from time import sleep

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import ProgrammingError

from pycsw.core import admin

logger = logging.getLogger(__name__)


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
    _wait_for_postgresql_db(database_url)
    try:
        _create_pycsw_schema(database_url, table_name)
    except ProgrammingError:
        pass  # database tables are already created


def _wait_for_postgresql_db(database_url, max_tries=10, wait_seconds=3):
    logger.debug("Waiting for {!r}...".format(database_url))
    engine = create_engine(database_url)
    current_try = 0
    while current_try < max_tries:
        try:
            engine.execute("SELECT version();")
            logger.debug("Database is already up!")
            break
        except OperationalError:
            logger.debug("Database not responding yet ...")
            current_try += 1
            sleep(wait_seconds)
    else:
        raise RuntimeError(
            "Database not responding at {} after {} tries. "
            "Giving up".format(database_url, max_tries)
        )


def _create_pycsw_schema(database_url, table):
    admin.setup_db(database=database_url, table=table, home="/home/pycsw")


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
