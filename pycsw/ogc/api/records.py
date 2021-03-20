# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2021 Tom Kralidis
# Copyright (c) 2021 Angelos Tzotsos
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

import codecs
from configparser import ConfigParser
import logging
import json

from pycsw import __version__
from pycsw.core.config import StaticContext
from pycsw.core.util import EnvInterpolation

LOGGER = logging.getLogger(__name__)

#: Return headers for requests (e.g:X-Powered-By)
HEADERS = {
    'Content-Type': 'application/json',
    'X-Powered-By': 'pycsw {}'.format(__version__)
}


class API:
    """API object"""

    def __init__(self, config):
        """
        constructor

        :param config: configuration dict

        :returns: `pycsw.ogcapi.API` instance
        """

        # load user configuration
        try:
            LOGGER.info('Loading user configuration')
            self.config = ConfigParser(interpolation=EnvInterpolation())
            with codecs.open(config, encoding='utf-8') as scp:
                self.config.read_file(scp)
        except Exception as err:
            msg = f'Could not load configuration: {err}'
            LOGGER.exception(msg)
            raise

        self.config['server']['url'] = self.config['server']['url'].rstrip('/')
        self.context = StaticContext()

        repo_filter = None
        if self.config.has_option('repository', 'filter'):
            repo_filter = self.config.get('repository', 'filter')

        self.orm = 'sqlalchemy'
        from pycsw.core import repository
        try:
            LOGGER.info('Loading default repository')
            self.repository = repository.Repository(
                self.config.get('repository', 'database'),
                self.context,
                #self.environ.get('local.app_root', None),
                None,
                self.config.get('repository', 'table'),
                repo_filter
            )
            LOGGER.debug(f'Repository loaded {self.repository.dbtype}')
        except Exception as err:
            msg = f'Could not load repository {err}'
            LOGGER.exception(msg)
            raise

    def landing_page(self, headers_, format_):
        """
        Provide API landing page

        :param headers_: copy of HEADERS object
        :param format_: format of requests, pre checked by
                        pre_process decorator

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = 'application/json'

        response = {
            'links': [],
            'title': self.config['metadata:main']['identification_title'],
            'description':
                self.config['metadata:main']['identification_abstract']
        }

        LOGGER.debug('Creating links')
        response['links'] = [{
              'rel': 'self',
              'type': 'application/json',
              'title': 'This document as JSON',
              'href': f"{self.config['server']['url']}?f=json",
              'hreflang': self.config['server']['language']
            }, {
              'rel': 'conformance',
              'type': 'application/json',
              'title': 'Conformance',
              'href': f"{self.config['server']['url']}/conformance"
            }, {
              'rel': 'data',
              'type': 'application/json',
              'title': 'Collections',
              'href': f"{self.config['server']['url']}/collections"
            }
        ]

        return headers_, 200, json.dumps(response)

    def conformance(self, headers_, format_):
        """
        Provide API conformance

        :param headers_: copy of HEADERS object
        :param format_: format of requests, pre checked by
                        pre_process decorator

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = 'application/json'

        conf_classes = [
            'http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core',
            'http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections',
            'http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/core',
            'http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/sorting',
            'http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/json',
            'http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/html'
        ]

        response = {
            'conformsTo': conf_classes
        }

        return headers_, 200, json.dumps(response)

    def collections(self, headers_, format_, collection=False):
        """
        Provide API collections

        :param headers_: copy of HEADERS object
        :param format_: format of requests, pre checked by
                        pre_process decorator
        :param collection_id: collection identifier

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = 'application/json'

        collection_info = {
            'id': 'metadata:main',
            'title': self.config['metadata:main']['identification_title'],
            'description': self.config['metadata:main']['identification_abstract'],
            'itemType': 'record',
            'crs': 'http://www.opengis.net/def/crs/OGC/1.3/CRS84',
            'links': [{
                'rel': 'collection',
                'type': 'application/json',
                'title': 'Collection URL',
                'href': f"{self.config['server']['url']}/collections/metadata:main",
                'hreflang': self.config['server']['language']
            }, {
                'rel': 'queryables',
                'type': 'application/json',
                'title': 'Collection queryables',
                'href': f"{self.config['server']['url']}/collections/metadata:main/queryables",
                'hreflang': self.config['server']['language']
            }, {
                'rel': 'items',
                'type': 'application/json',
                'title': 'Collection items as GeoJSON',
                'href': f"{self.config['server']['url']}/collections/metadata:main/items",
                'hreflang': self.config['server']['language']
            }]
        }

        if not collection:
            response = {
                'collections': [collection_info]
            }
        else:
            response = collection_info

        return headers_, 200, json.dumps(response)

    def queryables(self, headers_, format_):

        headers_['Content-Type'] = 'application/json'

        properties = self.repository.describe()

        response = {
            'type': 'object',
            'title': 'metadata:main',
            'properties': properties,
            '$schema': 'http://json-schema.org/draft/2019-09/schema',
            '$id': f"{self.config['server']['url']}/collections/metadata:main/queryables"
        }

        return headers_, 200, json.dumps(response)
