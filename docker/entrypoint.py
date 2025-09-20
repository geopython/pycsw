#!/usr/bin/env python3
# =================================================================
#
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#          Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2017 Ricardo Garcia Silva
# Copyright (c) 2024 Tom Kralidis
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
import sys

from pycsw.core.config import StaticContext
from pycsw.core.repository import Repository, setup
from pycsw.ogc.api.util import yaml_load

LOGGER = logging.getLogger(__name__)


def launch_pycsw(pycsw_config, workers=2, reload=False):
    """Launch pycsw.

    Main function of this entrypoint script. It will read pycsw's config file
    and handle the specified repository backend, after which it will yield
    control to the gunicorn wsgi server.

    The ``os.execlp`` function is used to launch gunicorn. This causes it to
    replace the current process - something analogous to bash's `exec`
    command, which seems to be a common techinque when writing docker
    entrypoint scripts. This means gunicorn will become PID 1 inside the
    container and it somehow simplifies the process of interacting with it
    (e.g. if the need arises to restart the worker processes). It also allows
    for a clean exit. See

    http://docs.gunicorn.org/en/latest/signals.html

    for more information on how to control gunicorn by sending UNIX signals.
    """

    database = pycsw_config['repository'].get('database')
    table = pycsw_config['repository'].get('table')

    try:
        setup(database, table)
    except Exception as err:
        LOGGER.debug(err)

    repo = Repository(database, StaticContext(), table=table)

    repo.ping()

    sys.stdout.flush()
    # we're using --reload-engine=poll because there is a bug with gunicorn
    # that prevents using inotify together with python3. For more info:
    #
    # https://github.com/benoitc/gunicorn/issues/1477
    #

    timeout = pycsw_config["server"].get('timeout', 30)

    args = ["--reload", "--reload-engine=poll"] if reload else []
    execution_args = ["gunicorn"] + args + [
        "--bind=0.0.0.0:8000",
        "--access-logfile=-",
        "--error-logfile=-",
        f"--workers={workers}",
        f"--timeout={timeout}",
        'pycsw.wsgi_flask:APP'

    ]
    LOGGER.debug(f"Launching pycsw with {' '.join(execution_args)} ...")
    os.execlp(
        "/venv/bin/gunicorn",
        *execution_args
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workers",
        default=2,
        help="Number of workers to use by the gunicorn server. Defaults to 2."
    )
    parser.add_argument(
        "-r",
        "--reload",
        action="store_true",
        help="Should the gunicorn server automatically restart workers when "
             "code changes? This option is only useful for development. "
             "Defaults to False."
    )

    args = parser.parse_args()

    with open(os.getenv('PYCSW_CONFIG'), encoding='utf8') as fh:
        config = yaml_load(fh)

    level = config['logging'].get('level', 'WARNING')

    workers = int(config['server'].get('workers', args.workers))
    logging.basicConfig(level=getattr(logging, level))
    launch_pycsw(config, workers=workers, reload=args.reload)
