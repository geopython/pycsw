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
from paver.easy import task, options, cmdopts, needs, pushd, sh, call_task

docs = 'docs'

@task
def build_release():
    """Create release package"""
    pass


@task
def refresh_docs():
    """Build sphinx docs from scratch"""
    with pushd(docs):
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

    with pushd(docs):
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
        sh('python gen_html.py > index.html')


@task
@needs(['distutils.command.sdist'])
def publish_pypi():
    """Publish to PyPI"""
    pass

