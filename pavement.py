# -*- coding: iso-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2012 Tom Kralidis
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

import os
import time
from paver.easy import task, cmdopts, needs, \
    pushd, sh, call_task, path, info

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
    local_path = 'build/html/en'
    remote_host = 'pycsw.org'
    remote_path = '/osgeo/pycsw/pycsw-web'

    user = options.get('user', False)

    if not user:
        raise Exception('OSGeo userid required')

    call_task('make_docs')

    with pushd(DOCS):
        # change privs to be group writeable
        for root, dirs, files in os.walk(local_path):
            for dfile in files:
                os.chmod(os.path.join(root, dfile), 0664)
            for ddir in dirs:
                os.chmod(os.path.join(root, ddir), 0775)

        # copy documentation
        sh('scp -r %s%s* %s@%s:%s' % (local_path, os.sep, user, remote_host,
                                     remote_path))


@task
def gen_tests_html():
    """Generated tests/index.html for online testing"""
    with pushd('tests'):
        # ensure manager testsuite is writeable
        os.chmod(os.path.join('suites', 'manager', 'data'), 0777)
        os.chmod(os.path.join('suites', 'manager', 'data', 'records.db'), 0666)
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
@cmdopts([
    ('url=', 'u', 'pycsw endpoint'),
])
def test(options):
    """Run unit tests"""

    url = options.get('url', None)

    if url is None:
        raise Exception('pycsw endpoint required')

    with pushd('tests'):
        sh('python run_tests.py %s' % url)


@task
def start(options):
    """Start local WSGI server instance"""

    sh('python csw.wsgi 8000 &')


@task
def stop():
    """Stop local WSGI server instance"""

    kill('python', 'csw.wsgi')


def kill(arg1, arg2):
    """Stops a proces that contains arg1 and is filtered by arg2"""

    # from https://github.com/GeoNode/geonode/blob/dev/pavement.py#L443
    from subprocess import Popen, PIPE

    # Wait until ready
    time0 = time.time()
    # Wait no more than these many seconds
    time_out = 30
    running = True

    while running and time.time() - time0 < time_out:
        proc = Popen('ps aux | grep %s' % arg1, shell=True,
                  stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

        lines = proc.stdout.readlines()

        running = False
        for line in lines:

            if '%s' % arg2 in line:
                running = True

                # Get pid
                fields = line.strip().split()

                info('Stopping %s (process number %s)' % (arg1, fields[1]))
                kill2 = 'kill -9 %s 2> /dev/null' % fields[1]
                os.system(kill2)

        # Give it a little more time
        time.sleep(1)
    else:
        pass

    if running:
        raise Exception('Could not stop %s: '
                        'Running processes are\n%s'
                        % (arg1, '\n'.join([l.strip() for l in lines])))

