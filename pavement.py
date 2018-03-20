# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
# Copyright (c) 2016 Ricardo Garcia Silva
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
        os.chmod(os.path.join('functionaltests', 'suites', 'manager', 'data'), 0o777)
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
