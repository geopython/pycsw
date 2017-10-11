#!/usr/bin/env python3
# =================================================================
#
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2017 Ricardo Garcia Silva
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
from six.moves.configparser import NoOptionError
from subprocess import call
from time import sleep

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import ProgrammingError

from pycsw.core import admin

logger = logging.getLogger(__name__)


def launch_pycsw(pycsw_config, gunicorn_workers=2):
    db_url = pycsw_config.get("repository", "database")
    db = db_url.partition(":")[0].partition("+")[0]
    db_handler = {
        "sqlite": handle_sqlite_db,
        "postgresql": handle_postgresql_db,
    }.get(db)
    logger.debug("Setting up pycsw's data repository...")
    logger.debug("Repository URL: {}".format(db_url))
    db_handler(
        db_url,
        pycsw_config.get("repository", "table"),
        pycsw_config.get("server", "home")
    )
    logger.debug("Launching pycsw...")
    pycsw_server_command = [
        "gunicorn",
        "--bind=0.0.0.0:8000",
        "--access-logfile=-",
        "--error-logfile=-",
        "--workers={}".format(gunicorn_workers)
    ]
    pycsw_server_command.append("pycsw.wsgi")
    call(pycsw_server_command)


def handle_sqlite_db(database_url, table_name, pycsw_home):
    db_path = database_url.rpartition(":///")[-1]
    if not os.path.isfile(db_path):
        try:
            os.makedirs(os.path.dirname(db_path))
        except OSError as exc:
            if exc.args[0] == 17:  # directory already exists
                pass
        admin.setup_db(database=database_url, table=table_name,
                       home=pycsw_home)


def handle_postgresql_db(database_url, table_name, pycsw_home):
    _wait_for_postgresql_db(database_url)
    try:
        admin.setup_db(database=database_url, table=table_name,
                       home=pycsw_home)
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workers",
        default=2,
        help="Number of workers to use by the gunicorn server. Defaults to 2."
    )
    args = parser.parse_args()
    config = SafeConfigParser()
    config.read(os.getenv("PYCSW_CONFIG"))
    try:
        level = config.get("server", "loglevel").upper()
    except NoOptionError:
        level = "WARNING"
    logging.basicConfig(level=getattr(logging, level))
    launch_pycsw(config, gunicorn_workers=args.workers)
