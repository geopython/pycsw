#!/usr/bin/python -u
# -*- coding: iso-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2010 Tom Kralidis
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

import os, sys
from server import server

CONFIG = 'default.cfg'

if os.environ.has_key('PYCSW_CONFIG'):
    CONFIG = os.environ['PYCSW_CONFIG']
if os.environ['QUERY_STRING'].lower().find('config') != -1:
    for kvp in os.environ['QUERY_STRING'].split('&'):
        if kvp.lower().find('config') != -1:
            CONFIG = kvp.split('=')[1]

gzip = False
if (os.environ.has_key('HTTP_ACCEPT_ENCODING') and
    os.environ['HTTP_ACCEPT_ENCODING'].find('gzip') != -1):
    # set for gzip compressed response 
    gzip = True

# get runtime configuration
csw = server.Csw(CONFIG)

# set compression level
if csw.config.has_option('server', 'gzip_compresslevel'):
    gzip_compresslevel = \
        int(csw.config.get('server', 'gzip_compresslevel'))
else:
    gzip_compresslevel = 0


# go!
outp = csw.dispatch_cgi()

sys.stdout.write("Content-Type:%s\r\n" % csw.contenttype)

if gzip and gzip_compresslevel > 0:
    import gzip
    
    buf = StringIO()
    gzipfile = gzip.GzipFile(mode='wb', fileobj=buf,
                                 compresslevel=self.gzip_compresslevel)
    gzipfile.write(outp)
    gzipfile.close()
        
    outp = buf.getvalue()

    sys.stdout.write('Content-Encoding: gzip\r\n')

sys.stdout.write('Content-Length: %d\r\n' % len(outp))
sys.stdout.write('\r\n')
sys.stdout.write(outp)

