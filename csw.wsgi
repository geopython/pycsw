# -*- coding: iso-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Adam Hinz <hinz.adam@gmail.com>
#
# Copyright (c) 2012 Adam Hinz
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
# WSGIScriptAlias /pycsw-wsgi /var/www/pycsw/csw.wsgi
#
# <Directory /var/www/pycsw>
#  Order deny,allow
#  Allow from all
# </Directory>
#
# or invoke this script from the command line:
#
# $ python ./csw.wsgi
#
# which will publish pycsw to:
#
# http://localhost:8000/
#

from StringIO import StringIO
import os, sys

app_path = os.path.dirname(__file__)
sys.path.append(app_path)

from pycsw import server

def application(env, start_response):
    config = 'default.cfg'

    if env.has_key('PYCSW_CONFIG'):
        config = env['PYCSW_CONFIG']

    if env['QUERY_STRING'].lower().find('config') != -1:
        for kvp in env['QUERY_STRING'].split('&'):
            if kvp.lower().find('config') != -1:
                config = kvp.split('=')[1]
    
    if os.path.isabs(config) is False:
        config = os.path.join(app_path, config)

    if 'HTTP_HOST' in env and ':' in env['HTTP_HOST']:
        env['HTTP_HOST'] = env['HTTP_HOST'].split(':')[0]

    env['local.app_root'] = app_path

    csw = server.Csw(config, env)

    gzip = False
    if (env.has_key('HTTP_ACCEPT_ENCODING') and
        env['HTTP_ACCEPT_ENCODING'].find('gzip') != -1):
        # set for gzip compressed response 
        gzip = True

    # set compression level
    if csw.config.has_option('server', 'gzip_compresslevel'):
        gzip_compresslevel = \
            int(csw.config.get('server', 'gzip_compresslevel'))
    else:
        gzip_compresslevel = 0

    contents = csw.dispatch_wsgi()

    headers = {}

    if gzip and gzip_compresslevel > 0:
        import gzip

        buf = StringIO()
        gzipfile = gzip.GzipFile(mode='wb', fileobj=buf,
                                 compresslevel=gzip_compresslevel)
        gzipfile.write(contents)
        gzipfile.close()
        
        contents = buf.getvalue()

        headers['Content-Encoding'] = 'gzip'

    headers['Content-Length'] = str(len(contents))
    headers['Content-Type'] = csw.contenttype

    status = '200 OK'
    start_response(status, headers.items())

    return [contents]

if __name__ == '__main__':  # run inline using WSGI reference implementation
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8000, application)
    print "Serving on port 8000..."
    httpd.serve_forever()
