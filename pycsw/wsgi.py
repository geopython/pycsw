# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Adam Hinz <hinz.adam@gmail.com>
#          Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2015 Adam Hinz
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

# WSGI wrapper for pycsw
#
# Apache mod_wsgi configuration
#
# ServerName host1
# WSGIDaemonProcess host1 home=/var/www/pycsw processes=2
# WSGIProcessGroup host1
#
# WSGIScriptAlias /pycsw-wsgi /var/www/pycsw/wsgi.py
#
# <Directory /var/www/pycsw>
#  Order deny,allow
#  Allow from all
# </Directory>
#
# or invoke this script from the command line:
#
# $ python ./pycsw/wsgi.py
#
# which will publish pycsw to:
#
# http://localhost:8000/
#

import os
import sys
import six
from six.moves.urllib.parse import unquote

from pycsw import server


def application(env, start_response):
    """WSGI wrapper"""

    pycsw_root = get_pycsw_root_path(env)
    env['local.app_root'] = pycsw_root
    configuration_path = get_configuration_path(env, pycsw_root)
    if 'HTTP_HOST' in env and ':' in env['HTTP_HOST']:
        env['HTTP_HOST'] = env['HTTP_HOST'].split(':')[0]
    csw = server.Csw(configuration_path, env)
    gzip = False
    if ('HTTP_ACCEPT_ENCODING' in env and
            env['HTTP_ACCEPT_ENCODING'].find('gzip') != -1):
        # set for gzip compressed response
        gzip = True
    # set compression level
    if csw.config.has_option('server', 'gzip_compresslevel'):
        gzip_compresslevel = \
            int(csw.config.get('server', 'gzip_compresslevel'))
    else:
        gzip_compresslevel = 0
    status, contents = csw.dispatch_wsgi()
    headers = {}
    if gzip and gzip_compresslevel > 0:
        import gzip
        buf = six.BytesIO()
        gzipfile = gzip.GzipFile(mode='wb', fileobj=buf,
                                 compresslevel=gzip_compresslevel)
        gzipfile.write(contents)
        gzipfile.close()
        contents = buf.getvalue()
        headers['Content-Encoding'] = 'gzip'
    headers['Content-Length'] = str(len(contents))
    headers['Content-Type'] = str(csw.contenttype)
    start_response(status, list(headers.items()))
    return [contents]


def get_pycsw_root_path(request_environment, root_path_key="PYCSW_ROOT"):
    app_root = os.getenv(
        root_path_key,
        request_environment.get(root_path_key)
    )
    if app_root is None:
        app_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
    return app_root


def get_configuration_path(request_environment, pycsw_root,
                           config_path_key="PYCSW_CONFIG"):
    """Get the path for pycsw configuration file.

    The configuration file path is searched in the following:
    * The presence of a `config` parameter in the request's query string;
    * A `PYCSW_CONFIG` environment variable;
    * A `PYCSW_CONFIG WSGI variable.

    """

    query_string = request_environment["QUERY_STRING"].lower()
    for kvp in query_string.split('&'):
        if "config" in kvp:
            configuration_path = unquote(kvp.split('=')[1])
            break
    else:  # did not find any `config` parameter in the request
        configuration_path = os.getenv(
            config_path_key,
            request_environment.get(config_path_key, "")
        )
    if not os.path.isabs(configuration_path):
        configuration_path = os.path.join(pycsw_root, configuration_path)
    return configuration_path


if __name__ == '__main__':  # run inline using WSGI reference implementation
    from wsgiref.simple_server import make_server
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    httpd = make_server('', port, application)
    print('Serving on port %d...' % port)
    httpd.serve_forever()
