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

import gzip
import os
import sys

import six
from six.moves import configparser
from six.moves.urllib.parse import unquote

from pycsw import server


def application(env, start_response):
    """WSGI wrapper"""

    pycsw_root = get_pycsw_root_path(os.environ, env)
    configuration_path = get_configuration_path(os.environ, env, pycsw_root)
    env['local.app_root'] = pycsw_root
    if 'HTTP_HOST' in env and ':' in env['HTTP_HOST']:
        env['HTTP_HOST'] = env['HTTP_HOST'].split(':')[0]
    csw = server.Csw(configuration_path, env)
    status, contents = csw.dispatch_wsgi()
    headers = {
        'Content-Length': str(len(contents)),
        'Content-Type': str(csw.contenttype)
    }
    if "gzip" in env.get("HTTP_ACCEPT_ENCODING", ""):
        try:
            compression_level = int(
                csw.config.get("server", "gzip_compresslevel"))
            contents, compress_headers = compress_response(
                contents, compression_level)
            headers.update(compress_headers)
        except configparser.NoOptionError:
            print(
                "The client requested a gzip compressed response. However, "
                "the server does not specify the 'gzip_compresslevel' option. "
                "Returning an uncompressed response..."
            )
        except configparser.NoSectionError:
            print('Could not load user configuration %s' % configuration_path)

    start_response(status, list(headers.items()))
    return [contents]


def compress_response(response, compression_level):
    """Compress pycsw's response with gzip

    Parameters
    ----------
    response: str
        The already processed CSW request
    compression_level: int
        Level of compression to use in gzip algorithm

    Returns
    -------
    bytes
        The full binary contents of the compressed response
    dict
        Extra HTTP headers that are useful for the response

    """

    buf = six.BytesIO()
    gzipfile = gzip.GzipFile(mode='wb', fileobj=buf,
                             compresslevel=compression_level)
    gzipfile.write(response)
    gzipfile.close()
    compressed_response = buf.getvalue()
    compression_headers = {'Content-Encoding': 'gzip'}
    return compressed_response, compression_headers


def get_pycsw_root_path(process_environment, request_environment=None,
                        root_path_key="PYCSW_ROOT"):
    """Get pycsw's root path.

    The root path will be searched in the ``process_environment`` first, then
    in the ``request_environment``. If it cannot be found then it is determined
    based on the location on disk.

    Parameters
    ----------
    process_environment: dict
        A mapping with the process environment.
    request_environment: dict, optional
        A mapping with the request environment. Typically the WSGI's
        environment
    root_path_key: str
        Name of the key in both the ``process_environment`` and the
        ``request_environment`` parameters that specifies the path to pycsw's
        root path.

    Returns
    -------
    str
        Path to pycsw's root path, as read from the supplied configuration.

    """

    req_env = (
        dict(request_environment) if request_environment is not None else {})
    app_root = process_environment.get(
        root_path_key,
        req_env.get(
            root_path_key,
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
    )
    return app_root

def get_configuration_path(process_environment, request_environment,
                           pycsw_root, config_path_key="PYCSW_CONFIG"):
    """Get the path for pycsw configuration file.

    The configuration file path is searched in the following:
    * The presence of a ``config`` parameter in the request's query string;
    * A ``PYCSW_CONFIG`` environment variable;
    * A ``PYCSW_CONFIG`` WSGI variable.

    Parameters
    ----------
    process_environment: dict
        A mapping with the process environment.
    request_environment: dict
        A mapping with the request's environment. Typically the WSGI's
        environment
    pycsw_root: str
        pycsw's default root path
    config_path_key: str, optional
        Name of the variable that specifies the path to pycsw's configuration
        file.

    Returns
    -------
    str
        Path where pycsw expects to find its own configuration file

    """

    # scan from config= or PYCSW_CONFIG environment variable
    query_string = request_environment.get("QUERY_STRING", "").lower()

    for kvp in query_string.split('&'):
        if "config" in kvp:
            configuration_path = unquote(kvp.split('=')[1])
            break
    else:
        # did not find any `config` parameter in the request
        # lets try the process env, request env and fallback to
        # <pycsw_root>/default.cfg
        configuration_path = process_environment.get(
            config_path_key,
            request_environment.get(
                config_path_key, os.path.join(pycsw_root, "default.cfg")
            )
        )
    return configuration_path


if __name__ == '__main__':  # run inline using WSGI reference implementation
    from wsgiref.simple_server import make_server
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    httpd = make_server('', port, application)
    print('Serving on port {}...'.format(port))
    httpd.serve_forever()
