# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2011 Tom Kralidis
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

import logging

msg_format = '%(asctime)s] [%(levelname)s] file=%(pathname)s line=%(lineno)s module=%(module)s function=%(funcName)s %(message)s'
time_format = '%a, %d %b %Y %H:%M:%S'

loglevels = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'NOTSET': logging.NOTSET,
}

def initlog(config=None):
    if config is None:
        return None

    logfile=None
    loglevel='NOTSET'

    if config['server'].has_key('loglevel') is True:
        loglevel = config['server']['loglevel']

        if loglevel not in loglevels.keys():
            raise RuntimeError, ('Invalid server configuration (server.loglevel).')

    if config['server'].has_key('logfile'):
        logfile = config['server']['logfile']

    if loglevel != 'NOTSET' and logfile is None:
        raise RuntimeError, ('Invalid server configuration (server.loglevel set, but server.logfile is not).')

    log=logging.getLogger('pycsw')
    log.setLevel(loglevels[loglevel])

    if logfile:
        try:
            fh = logging.FileHandler(logfile)
            fh.setLevel(loglevels[loglevel])
            fh.setFormatter(logging.Formatter(msg_format,time_format))
            log.addHandler(fh)
        except Exception, err:
            raise RuntimeError, ('Invalid server configuration (server.logfile access denied.  Make sure filepath exists and is writable')
    log.info('Logging initalized (level: %s)' % loglevel)
    return log
