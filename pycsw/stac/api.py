# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2024 Tom Kralidis
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

from copy import deepcopy
import json
import logging
import os

from pygeofilter.parsers.ecql import parse as parse_ecql

from pycsw import __version__
from pycsw.ogc.api.oapi import gen_oapi
from pycsw.ogc.api.records import API
from pycsw.core.pygeofilter_evaluate import to_filter
from pycsw.core.util import geojson_geometry2bbox

LOGGER = logging.getLogger(__name__)

#: Return headers for requests (e.g:X-Powered-By)
HEADERS = {
    'Content-Type': 'application/json',
    'X-Powered-By': f'pycsw {__version__}'
}

THISDIR = os.path.dirname(os.path.realpath(__file__))


CONFORMANCE_CLASSES = [
    'http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core',
    'http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections',
    'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core',
    'http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/queryables',
    'http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/queryables-query-parameters',
    'http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/filter',
    'http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/features-filter',
    'http://www.opengis.net/spec/ogcapi-features-4/1.0/conf/create-replace-delete',
    'http://www.opengis.net/spec/cql2/1.0/conf/cql2-json',
    'http://www.opengis.net/spec/cql2/1.0/conf/cql2-text',
    'https://api.stacspec.org/v1.0.0/core',
    'https://api.stacspec.org/v1.0.0/ogcapi-features',
    'https://api.stacspec.org/v1.0.0/item-search',
    'https://api.stacspec.org/v1.0.0/item-search#filter',
    'https://api.stacspec.org/v1.0.0/item-search#free-text'
]


class STACAPI(API):
    """STAC API object"""

    def __init__(self, config: dict):
        """
        constructor

        :param config: pycsw configuration dict

        :returns: `pycsw.ogc.api.STACAPI` instance
        """

        super().__init__(config)
        self.mode = 'stac-api'

        self.config['server']['url'] += '/stac'
        LOGGER.debug(f"Server URL: {self.config['server']['url']}")

    def landing_page(self, headers_, args):
        """
        Provide API landing page

        :param headers_: copy of HEADERS object
        :param args: request parameters

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = 'application/json'

        response = {
            'stac_version': '1.0.0',
            'id': 'pycsw-catalogue',
            'type': 'Catalog',
            'conformsTo': CONFORMANCE_CLASSES,
            'links': [],
            'title': self.config['metadata']['identification']['title'],
            'description':
                self.config['metadata']['identification']['description'],
            'keywords':
                self.config['metadata']['identification']['keywords']
        }

        LOGGER.debug('Creating links')
        response['links'] = [{
              'rel': 'self',
              'type': 'application/json',
              'href': f"{self.config['server']['url']}/"
            }, {
              'rel': 'root',
              'type': 'application/json',
              'href': f"{self.config['server']['url']}/"
            }, {
              'rel': 'service-doc',
              'type': 'text/html',
              'href': f"{self.config['server']['url']}/openapi?f=html"
            }, {
              'rel': 'service-desc',
              'type': 'application/vnd.oai.openapi+json;version=3.0',
              'href': f"{self.config['server']['url']}/openapi?f=json"
            }, {
              'rel': 'conformance',
              'type': 'application/json',
              'href': f"{self.config['server']['url']}/conformance"
            }, {
              'rel': 'data',
              'type': 'application/json',
              'href': f"{self.config['server']['url']}/collections"
            }, {
               'rel': 'http://www.opengis.net/def/rel/ogc/1.0/queryables',
               'type': 'application/schema+json',
               'title': 'Queryables',
               'href': f"{self.config['server']['url']}/queryables"
            }, {
              'rel': 'search',
              'type': 'application/geo+json',
              'href': f"{self.config['server']['url']}/search"
            }
        ]

        return self.get_response(200, headers_, response)

    def openapi(self, headers_, args):
        """
        Provide OpenAPI document / Swagger

        :param headers_: copy of HEADERS object
        :param args: request parameters

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = self.get_content_type(headers_, args)
        if headers_['Content-Type'] == 'application/json':
            headers_['Content-Type'] = 'application/vnd.oai.openapi+json;version=3.0'

        filepath = f"{THISDIR}/../core/schemas/ogc/ogcapi/records/part1/1.0/ogcapi-records-1.yaml"

        response = gen_oapi(self.config, filepath, self.mode)

        return self.get_response(200, headers_, response, 'openapi.html')

    def conformance(self, headers_, args):
        """
        Provide API conformance

        :param headers_: copy of HEADERS object
        :param args: request parameters

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = 'application/json'
        headers_['Accept'] = 'application/json'

        response = {
            'conformsTo': CONFORMANCE_CLASSES
        }

        return self.get_response(200, headers_, response)

    def collections(self, headers_, args):
        """
        Provide API collections

        :param headers_: copy of HEADERS object
        :param args: request parameters

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = 'application/json'

        collections = []

        LOGGER.debug('Generating default metadata:main collection')
        collection_info = self.get_collection_info()

        collections.append(collection_info)

        LOGGER.debug('Generating virtual collections')
        virtual_collections = self.repository.query_collections()

        for virtual_collection in virtual_collections:
            virtual_collection_info = self.get_collection_info(
                virtual_collection.identifier,
                dict(title=virtual_collection.title,
                     description=virtual_collection.abstract))

            collections.append(virtual_collection_info)

        response = {
            'collections': collections
        }

        LOGGER.debug('Generating STAC collections')
        mapping = {'typename': self.repository.dataset.typename}
        ast = parse_ecql("typename = 'stac:Collection'")
        LOGGER.debug(f'Abstract syntax tree: {ast}')
        filters = to_filter(ast, self.repository.dbtype, mapping)
        LOGGER.debug(f'Filter: {filters}')
        sc_query = self.repository.session.query(
            self.repository.dataset).filter(filters).all()

        for sc in sc_query:
            response['collections'].append(self.get_collection_info(
                sc.identifier, {
                    'title': sc.title or sc.identifier,
                    'description': sc.abstract or sc.identifier
                })
            )

        url_base = f"{self.config['server']['url']}/collections"

        for collection in response['collections']:
            collection['links'].append({
                'rel': 'self',
                'type': 'application/json',
                'href': f"{url_base}/{collection['id']}"
                })

        response['links'] = [{
            'rel': 'self',
            'type': 'application/json',
            'href': url_base
            }, {
            'rel': 'root',
            'type': 'application/json',
            'href': f"{self.config['server']['url']}/"
            }, {
            'rel': 'parent',
            'type': 'application/json',
            'href': self.config['server']['url']
        }]

        response['numberMatched'] = len(response['collections'])
        response['numberReturned'] = len(response['collections'])

        return self.get_response(200, headers_, response)

    def collection(self, headers_, args, collection='metadata:main'):
        """
        Provide API collections

        :param headers_: copy of HEADERS object
        :param args: request parameters
        :param collection: collection name

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = 'application/json'

        LOGGER.debug(f'Generating {collection} collection')

        if collection == 'metadata:main':
            collection_info = self.get_collection_info()
        else:
            virtual_collection = self.repository.query_ids([collection])[0]
            collection_info = self.get_collection_info(
                virtual_collection.identifier,
                dict(title=virtual_collection.title,
                     description=virtual_collection.abstract))

        response = collection_info
        url_base = f"{self.config['server']['url']}/collections/{collection}"

        response['links'] = [{
            'rel': 'self',
            'type': 'application/json',
            'href': url_base
            }, {
            'rel': 'root',
            'type': 'application/json',
            'href': f"{self.config['server']['url']}/"
            }, {
            'rel': 'parent',
            'type': 'application/json',
            'href': f"{self.config['server']['url']}/collections"
            }, {
            'rel': 'items',
            'type': 'application/geo+json',
            'href': f"{url_base}/items"
        }]

        return self.get_response(200, headers_, response)

    def queryables(self, headers_, args, collection='metadata:main'):
        """
        Provide collection queryables

        :param headers_: copy of HEADERS object
        :param args: request parameters
        :param collection: name of collection

        :returns: tuple of headers, status code, content
        """

        headers_['Accept'] = 'application/json'
        headers, status, response = super().queryables(headers_, args, collection)

        return self.get_response(status, headers, json.loads(response))

    def items(self, headers_, json_post_data, args, collection='metadata:main'):
        """
        Provide collection items

        :param headers_: copy of HEADERS object
        :param json_post_data: `dict` of JSON POST data
        :param args: request parameters
        :param collection: collection name

        :returns: tuple of headers, status code, content
        """

        headers_['Accept'] = 'application/json'
        headers, status, response = super().items(headers_, json_post_data, args, collection)

        if collection not in self.get_all_collections():
            msg = 'Invalid collection'
            LOGGER.exception(msg)
            return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

        response = json.loads(response)
        response2 = deepcopy(response)
        response2['features'] = []

        LOGGER.debug('Filtering on STAC items')
        for record in response['features']:
            if record.get('stac_version') is None:
                record['links'].extend([{
                    'rel': 'self',
                    'type': 'application/geo+json',
                    'href': f"{self.config['server']['url']}/collections/{collection}/items/{record['id']}"
                    }, {
                    'rel': 'root',
                    'type': 'application/json',
                    'href': f"{self.config['server']['url']}/"
                    }, {
                    'rel': 'parent',
                    'type': 'application/json',
                    'href': f"{self.config['server']['url']}/collections/{collection}"
                }])
                response2['features'].append(links2stacassets(collection, record))
            else:
                response2['features'].append(record)

            if record.get('bbox') is None:
                geometry = record.get('geometry')
                if geometry is not None:
                    LOGGER.debug('Calculating bbox from geometry')
                    bbox = geojson_geometry2bbox(geometry)
                    record['bbox'] = [float(t) for t in bbox.split(',')]

            for link in record['links']:
                if link.get('rel') is None:
                    LOGGER.debug('Missing link relation; adding rel=related')
                    link['rel'] = 'related'

        for count, value in enumerate(response2['links']):
            if value['rel'] == 'alternate':
                response2['links'].pop(count)

        response2['links'].extend([{
            'rel': 'root',
            'type': 'application/json',
            'href': f"{self.config['server']['url']}/"
            }
        ])

        return self.get_response(status, headers, response2)

    def item(self, headers_, args, collection, item):
        """
        Provide collection item

        :param headers_: copy of HEADERS object
        :param args: request parameters
        :param collection: name of collection
        :param item: record identifier

        :returns: tuple of headers, status code, content
        """

        headers_['Accept'] = 'application/geo+json'
        headers, status, response = super().item(headers_, args, collection, item)

        if collection not in self.get_all_collections():
            msg = 'Invalid collection'
            LOGGER.exception(msg)
            return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

        response = json.loads(response)
        response = links2stacassets(collection, response)

        return self.get_response(status, headers_, response)

    def get_collection_info(self, collection_name: str = 'metadata:main',
                            collection_info: dict = {}) -> dict:
        """
        Generate collection metadata

        :param collection_name: name of collection
                                default is 'metadata:main' main collection
        :param collection_info: `dict` of collecton info

        :returns: `dict` of collection
        """

        if collection_name == 'metadata:main':
            id_ = collection_name
            title = self.config['metadata']['identification']['title']
            description = self.config['metadata']['identification']['description']  # noqa
        else:
            id_ = collection_name
            title = collection_info.get('title')
            description = collection_info.get('description')

        return {
            'id': id_,
            'title': title,
            'description': description,
            'type': 'Collection',
            'links': [{
                'rel': 'collection',
                'type': 'application/json',
                'href': f"{self.config['server']['url']}/collections/{collection_name}"
            }, {
                'rel': 'items',
                'type': 'application/geo+json',
                'href': f"{self.config['server']['url']}/collections/{collection_name}/items"
            }]
        }


def links2stacassets(collection, record):
    LOGGER.debug('Transforming enclosure links to STAC assets')

    if 'stac_version' not in record:
        record['stac_version'] = '1.0.0'
    if 'collection' not in record:
        record['collection'] = collection

    links_assets = [i for i in record['links'] if i.get('rel', '') == 'enclosure']
    links_to_keep = [i for i in record['links'] if i.get('rel', '') != 'enclosure']

    record['links'] = links_to_keep

    LOGGER.debug('Adding assets')
    if links_assets:
        if 'assets' not in record:
            record['assets'] = {}

        for count, value in enumerate(links_assets):
            record['assets'][count] = value

    return record
