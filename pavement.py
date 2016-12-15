# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
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

from __future__ import (absolute_import, division, print_function)

import glob
import os
import sys
import time

from six.moves import configparser

from paver.easy import task, cmdopts, needs, \
    pushd, sh, call_task, path, info, BuildFailure

DOCS = 'docs'
STAGE_DIR = '/tmp'


@task
def build_release():
    """Create release package"""
    pass


@task
def refresh_docs():
    """Build sphinx docs from scratch"""
    with pushd(DOCS):
        sh('make clean')
        sh('make html')


@task
@cmdopts([
    ('user=', 'u', 'OSGeo userid'),
])
def publish_docs(options):
    """Publish dev docs to production"""
    local_path = '_build/html'
    remote_host = 'pycsw.org'
    remote_path = '/osgeo/pycsw/pycsw-web/docs/latest'

    user = options.get('user', False)
    if not user:
        raise Exception('OSGeo userid required')

    call_task('refresh_docs')

    with pushd(DOCS):
        # change privs to be group writeable
        for root, dirs, files in os.walk(local_path):
            for dfile in files:
                os.chmod(os.path.join(root, dfile), 0o664)
            for ddir in dirs:
                os.chmod(os.path.join(root, ddir), 0o775)

        # copy documentation
        sh('scp -r %s%s* %s@%s:%s' % (local_path, os.sep, user, remote_host,
                                      remote_path))


@task
def gen_tests_html():
    """Generate tests/index.html for online testing"""
    with pushd('tests'):
        # ensure manager testsuite is writeable
        os.chmod(os.path.join('suites', 'manager', 'data'), 0o777)
        sh('python gen_html.py > index.html')


@task
@needs(['distutils.command.sdist'])
def publish_pypi():
    """Publish to PyPI"""
    pass


@task
def package():
    """Package a distribution .tar.gz/.zip"""

    import pycsw

    version = pycsw.__version__

    package_name = 'pycsw-%s' % version

    call_task('package_tar_gz', options={'package_name': package_name})


@task
@cmdopts([
    ('package_name=', 'p', 'Name of package'),
])
def package_tar_gz(options):
    """Package a .tar.gz distribution"""

    import tarfile

    package_name = options.get('package_name', None)

    if package_name is None:
        raise Exception('Package name required')

    filename = path('%s/%s.tar.gz' % (STAGE_DIR, package_name))

    if filename.exists():
        info('Package %s already exists' % filename)
        return

    with pushd(STAGE_DIR):
        stage_path = '%s/%s' % (STAGE_DIR, package_name)

        if not path(stage_path).exists():
            raise Exception('Directory %s does not exist' % stage_path)

        tar = tarfile.open(filename, 'w:gz')
        tar.add(package_name)
        tar.close()

@task
def setup_testdata():
    """Create test databases and load test data"""

    test_database_parameters = {
        # suite: has_testdata
        'apiso': True,
        'cite': True,
        'harvesting': False,
        'manager': False
    }

    for suite in test_database_parameters.keys():
        dbfile = 'tests/suites/%s/data/records.db' % suite
        if os.path.isfile(dbfile):
            os.remove(dbfile)

    for database, has_testdata in test_database_parameters.items():
        info('Setting up test database %s' % database)
        cfg = path('tests/suites/%s/default.cfg' % database)
        sh('pycsw-admin.py -c setup_db -f %s' % cfg)
        if has_testdata:
            datapath = path('tests/suites/%s/data' % database)
            info('Loading test data from %s' % datapath)
            sh('pycsw-admin.py -c load_records -f %s -p %s' % (cfg, datapath))
            exportpath = path('tests/results/exports')
            sh('pycsw-admin.py -c export_records -f %s -p %s' % (cfg, exportpath))

@task
@cmdopts([
    ('url=', 'u', 'pycsw endpoint'),
    ('suites=', 's', 'comma-separated list of testsuites'),
    ('database=', 'd', 'database (SQLite3 [default], PostgreSQL, MySQL)'),
    ('user=', 'U', 'database username'),
    ('pass=', 'p', 'database password'),
    ('pedantic', 'P', 'run tests in pedantic mode (byte level diff check) (default: c14n mode)'),
    ('remote', 'r', 'remote testing (harvesting)'),
    ('time=', 't', 'time (milliseconds) in which requests should complete')
])
def test(options):
    """Run unit tests"""

    db_setup = False
    db_conn = None
    cfg_files = []
    status = 0

    url = options.get('url', None)
    suites = options.get('suites', None)
    database = options.get('database', 'SQLite3')
    remote = options.get('remote')
    timems = options.get('time', None)
    pedantic = options.get('pedantic', False)

    if url is None:
        # run against default server
        call_task('stop')
        call_task('reset')
        if database == 'SQLite3':
            call_task('setup_testdata')
        call_task('start')
        url = 'http://localhost:8000'

    if suites is not None:
        cmd = 'python run_tests.py -u %s -s %s' % (url, suites)
    else:
        cmd = 'python run_tests.py -u %s' % url

    if remote:
        cmd = '%s -r' % cmd

    if pedantic:
        cmd = '%s -p' % cmd

    if timems:
        cmd = '%s -t %s' % (cmd, timems)

    # configure/setup database if not default
    if database != 'SQLite3':
        db_setup = True
        temp_db = 'pycsw_ci_test_pid_%d' % os.getpid()

        if database == 'PostgreSQL':  # configure PG

            from pycsw.admin import setup_db, load_records, export_records
            from pycsw.config import StaticContext

            cmd = '%s -d %s' % (cmd, database)

            init_sfsql = True
            home = os.path.abspath(os.path.dirname(__file__))
            user = options.get('user', 'postgres')
            password = options.get('pass', '')
            context = StaticContext()

            db_conn = 'postgresql://%s:%s@localhost/%s' % (
                      user, password, temp_db)

            if password:
                sh('set PGPASSWORD=%s' % password)

            sh('createdb %s -U %s' % (temp_db, user))
            sh('createlang --dbname=%s plpythonu -U %s' % (temp_db, user))

            # update all default.cfg files to point to test DB
            cfg_files = glob.glob('tests%ssuites%s*%s*.cfg' % (3*(os.sep,)))

            for cfg in cfg_files:
                # generate table
                suite = cfg.split(os.sep)[2]

                tablename = 'records_cite'

                if suite == 'manager':
                    tablename = 'records_manager'
                elif suite == 'apiso':
                    tablename = 'records_apiso'

                config = configparser.SafeConfigParser()
                with open(cfg) as read_data:
                    config.readfp(read_data)
                config.set('repository', 'database', db_conn)
                config.set('repository', 'table', tablename)
                with open(cfg, 'wb') as config2:
                    config.write(config2)

                if suite in ['cite', 'manager', 'apiso']:  # setup tables
                    setup_db(db_conn, tablename, home, init_sfsql, init_sfsql)
                    init_sfsql = False

                if suite in ['cite', 'apiso']:  # load test data
                    dirname = '%s%sdata' % (os.path.dirname(cfg), os.sep)
                    load_records(context, db_conn, tablename, dirname)

                if suite in ['cite', 'apiso']:  # export test data
                    exportpath = 'tests/results/exports'
                    export_records(context, db_conn, tablename, exportpath)

        else:
            raise Exception('Invalid database specified')

    with pushd('tests'):
        try:
            sh(cmd)
        except BuildFailure as err:
            status = 1
        # stop pycsw instance
        call_task('stop')

    if db_setup:  # tearDown
        for cfg in cfg_files:
            sh('git checkout %s' % cfg)
        if database == 'PostgreSQL':
            sh("psql -c \"select pg_terminate_backend(procpid) from pg_stat_activity where datname='%s';\" -U %s" % (temp_db, user))
            sh('dropdb %s -U %s' % (temp_db, user))
            sh('unset PGPASSWORD')

    sys.exit(status)


@task
def start(options):
    """Start local WSGI server instance"""
    sh('python pycsw/wsgi.py 8000 &')
    time.sleep(10)


@task
def stop():
    """Stop local WSGI server instance"""

    kill_process('python', 'pycsw/wsgi.py')


@task
@cmdopts([
    ('force', 'f', 'forces git clean'),
])
def reset(options):
    """Return codebase to pristine state"""

    force = options.get('force')
    if force:
        sh('git clean -dxf')


def kill_process(procname, scriptname):
    """kill WSGI processes that may be running in development"""

    # from http://stackoverflow.com/a/2940878
    import subprocess, signal
    p = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
    out, err = p.communicate()

    for line in out.decode().splitlines():
        if procname in line and scriptname in line:
            pid = int(line.split()[1])
            info('Stopping %s %s %d' % (procname, scriptname, pid))
            os.kill(pid, signal.SIGKILL)
