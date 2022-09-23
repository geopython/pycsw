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

import logging

LOGGER = logging.getLogger(__name__)

MSG_FORMAT = '%(asctime)s] [%(levelname)s] file=%(pathname)s \
line=%(lineno)s module=%(module)s function=%(funcName)s %(message)s'

TIME_FORMAT = '%a, %d %b %Y %H:%M:%S'

LOGLEVELS = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'NOTSET': logging.NOTSET,
}


def setup_logger(config=None):
    """Initialize logging facility"""
    if config is None:
        return None

    # Do not proceed if logging has not been set up.
    if not (config.has_option('server', 'loglevel') or
            config.has_option('server', 'logfile')):
        return None

    logfile = None
    loglevel = 'NOTSET'
    logging_handlers = []
    to_stdout = False

    loglevel = config.get('server', 'loglevel', fallback=loglevel)

    if loglevel not in LOGLEVELS.keys():
        raise RuntimeError(
            'Invalid server configuration (server.loglevel).')

    if loglevel != 'NOTSET':
        if config.has_option('server', 'logfile'):
            logfile = config.get('server', 'logfile')
            if logfile.strip() != '':
                logging_handlers.append(logging.FileHandler(logfile))
            else:  # stdout
                to_stdout = True
        else:  # stdout
            to_stdout = True

        if to_stdout:
            logging_handlers.append(logging.StreamHandler())

        # Setup logging globally (not only for the pycsw module)
        # based on the parameters passed.
        logging.basicConfig(level=LOGLEVELS[loglevel],
                            format=MSG_FORMAT,
                            datefmt=TIME_FORMAT,
                            handlers=logging_handlers)

    LOGGER.info('Logging initialized (level: %s).', loglevel)

    if loglevel == 'DEBUG':  # turn on CGI debugging
        LOGGER.info('CGI debugging enabled.')
        import cgitb
        cgitb.enable()
