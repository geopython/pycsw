# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2022 Tom Kralidis
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

from configparser import ConfigParser
import json
import logging
import os
from urllib.parse import urlencode

from pygeofilter.parsers.ecql import parse as parse_ecql
from pygeofilter.parsers.cql2_json import parse as parse_cql2_json

from pycsw import __version__
from pycsw.core import log
from pycsw.core.config import StaticContext
from pycsw.core.metadata import parse_record
from pycsw.core.pygeofilter_evaluate import to_filter
from pycsw.core.util import bind_url, get_today_and_now, jsonify_links, load_custom_repo_mappings, wkt2geom
from pycsw.ogc.api.oapi import gen_oapi
from pycsw.ogc.api.util import match_env_var, render_j2_template, to_json

LOGGER = logging.getLogger(__name__)

#: Return headers for requests (e.g:X-Powered-By)
HEADERS = {
    'Content-Type': 'application/json',
    'X-Powered-By': 'pycsw {}'.format(__version__)
}

THISDIR = os.path.dirname(os.path.realpath(__file__))


CONFORMANCE_CLASSES = [
    'http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core',
    'http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections',
    'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core',
    'http://www.opengis.net/spec/ogcapi-features-3/1.0/req/filter',
    'http://www.opengis.net/spec/ogcapi-features-4/1.0/conf/create-replace-delete',  # noqa
    'http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/core',
    'http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/sorting',
    'http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/json',
    'http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/html',
    'https://api.stacspec.org/v1.0.0-rc.1/core',
    'https://api.stacspec.org/v1.0.0-rc.1/item-search',
    'https://api.stacspec.org/v1.0.0-rc.1/item-search#filter',
    'https://api.stacspec.org/v1.0.0-rc.1/item-search#sort'
]


class API:
    """API object"""

    def __init__(self, config: ConfigParser):
        """
        constructor

        :param config: ConfigParser pycsw configuration dict

        :returns: `pycsw.ogc.api.API` instance
        """

        self.config = config

        log.setup_logger(self.config)

        if self.config['server']['url'].startswith('${'):
            LOGGER.debug(f"Server URL is an environment variable: {self.config['server']['url']}")
            url_ = match_env_var(self.config['server']['url'])
        else:
            url_ = self.config['server']['url']

        LOGGER.debug(f'Server URL: {url_}')
        self.config['server']['url'] = url_.rstrip('/')

        self.context = StaticContext()

        LOGGER.debug('Setting maxrecords')
        try:
            self.maxrecords = int(self.config['server']['maxrecords'])
        except KeyError:
            self.maxrecords = 10
        LOGGER.debug(f'maxrecords: {self.maxrecords}')

        repo_filter = None
        if self.config.has_option('repository', 'filter'):
            repo_filter = self.config.get('repository', 'filter')

        custom_mappings_path = self.config.get('repository', 'mappings', fallback=None)
        if custom_mappings_path is not None:
            md_core_model = load_custom_repo_mappings(custom_mappings_path)
            if md_core_model is not None:
                self.context.md_core_model = md_core_model
            else:
                LOGGER.exception(
                    'Could not load custom mappings: %s', custom_mappings_path)

        self.orm = 'sqlalchemy'
        from pycsw.core import repository
        try:
            LOGGER.info('Loading default repository')
            self.repository = repository.Repository(
                self.config.get('repository', 'database'),
                self.context,
                # self.environ.get('local.app_root', None),
                None,
                self.config.get('repository', 'table'),
                repo_filter
            )
            LOGGER.debug(f'Repository loaded {self.repository.dbtype}')
        except Exception as err:
            msg = f'Could not load repository {err}'
            LOGGER.exception(msg)
            raise

        self.query_mappings = {
            'type': self.repository.dataset.type,
            'parentidentifier': self.repository.dataset.parentidentifier,
            'collections': self.repository.dataset.parentidentifier,
            'recordUpdated': self.repository.dataset.insert_date,
            'title': self.repository.dataset.title,
            'description': self.repository.dataset.abstract,
            'keywords': self.repository.dataset.keywords,
            'edition': self.repository.dataset.edition,
            'anytext': self.repository.dataset.anytext,
            'bbox': self.repository.dataset.wkt_geometry,
            'date': self.repository.dataset.date,
            'time_begin': self.repository.dataset.time_begin,
            'time_end': self.repository.dataset.time_end,
            'platform': self.repository.dataset.platform,
            'instrument': self.repository.dataset.instrument,
            'sensortype': self.repository.dataset.sensortype
        }
        if self.repository.dbtype == 'postgresql+postgis+native':
            self.query_mappings['bbox'] = self.repository.dataset.wkb_geometry

    def get_content_type(self, headers, args):
        """
        Decipher content type requested

        :param headers: `dict` of HTTP request headers
        :param args: `dict` of query arguments

        :returns: `str` of response content type
        """

        content_type = 'application/json'

        format_ = args.get('f')

        if headers and 'Accept' in headers:
            if 'text/html' in headers['Accept']:
                content_type = 'text/html'
            elif 'application/xml' in headers['Accept']:
                content_type = 'application/xml'

        if format_ is not None:
            if format_ == 'json':
                content_type = 'application/json'
            elif format_ == 'xml':
                content_type = 'application/xml'
            elif format_ == 'html':
                content_type = 'text/html'

        return content_type

    def get_response(self, status, headers, template, data):
        """
        Provide response

        :param status: `int` of HTTP status
        :param headers: `dict` of HTTP request headers
        :param template: template filename
        :param data: `dict` of response data

        :returns: tuple of headers, status code, content
        """

        if headers.get('Content-Type') == 'text/html':
            content = render_j2_template(self.config, template, data)
        else:
            content = to_json(data)

        headers['Content-Length'] = len(content)

        return headers, status, content

    def landing_page(self, headers_, args):
        """
        Provide API landing page

        :param headers_: copy of HEADERS object
        :param args: request parameters

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = self.get_content_type(headers_, args)

        response = {
            'stac_version': '1.0.0',
            'id': 'pycsw-catalogue',
            'type': 'Catalog',
            'conformsTo': CONFORMANCE_CLASSES,
            'links': [],
            'title': self.config['metadata:main']['identification_title'],
            'description':
                self.config['metadata:main']['identification_abstract'],
            'keywords':
                self.config['metadata:main']['identification_keywords'].split(',')
        }

        LOGGER.debug('Creating links')
        response['links'] = [{
              'rel': 'self',
              'type': 'application/json',
              'title': 'This document as JSON',
              'href': f"{self.config['server']['url']}?f=json",
              'hreflang': self.config['server']['language']
            }, {
              'rel': 'root',
              'type': 'application/json',
              'title': 'The root URI as JSON',
              'href': f"{self.config['server']['url']}?f=json",
              'hreflang': self.config['server']['language']
            }, {
              'rel': 'conformance',
              'type': 'application/json',
              'title': 'Conformance as JSON',
              'href': f"{self.config['server']['url']}/conformance?f=json"
            }, {
              'rel': 'service-doc',
              'type': 'text/html',
              'title': 'The OpenAPI definition as HTML',
              'href': f"{self.config['server']['url']}/openapi?f=html"
            }, {
              'rel': 'service-desc',
              'type': 'application/vnd.oai.openapi+json;version=3.0',
              'title': 'The OpenAPI definition as JSON',
              'href': f"{self.config['server']['url']}/openapi?f=json"
            }, {
              'rel': 'data',
              'type': 'application/json',
              'title': 'Collections as JSON',
              'href': f"{self.config['server']['url']}/collections?f=json"
            }, {
              'rel': 'search',
              'type': 'application/json',
              'title': 'Search collections',
              'href': f"{self.config['server']['url']}/search"
            }, {
              'rel': 'child',
              'type': 'application/json',
              'title': 'Main metadata collection',
              'href': f"{self.config['server']['url']}/collections/metadata:main?f=json"
            }, {
              'rel': 'service',
              'type': 'application/xml',
              'title': 'CSW 3.0.0 endpoint',
              'href': f"{self.config['server']['url']}/csw"
            }, {
              'rel': 'service',
              'type': 'application/xml',
              'title': 'CSW 2.0.2 endpoint',
              'href': f"{self.config['server']['url']}/csw?service=CSW&version=2.0.2&request=GetCapabilities"
            }, {
              'rel': 'service',
              'type': 'application/xml',
              'title': 'OpenSearch endpoint',
              'href': f"{self.config['server']['url']}/opensearch"
            }, {
              'rel': 'service',
              'type': 'application/xml',
              'title': 'OAI-PMH endpoint',
              'href': f"{self.config['server']['url']}/oaipmh"
            }, {
              'rel': 'service',
              'type': 'application/xml',
              'title': 'SRU endpoint',
              'href': f"{self.config['server']['url']}/sru"
            }, {
              'rel': 'child',
              'type': 'application/json',
              'title': 'Main collection',
              'href': f"{self.config['server']['url']}/collections/metadata:main"
            }
        ]

        return self.get_response(200, headers_, 'landing_page.html', response)

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

        filepath = f"{THISDIR}/../../core/schemas/ogc/ogcapi/records/part1/1.0/ogcapi-records-1.yaml"

        response = gen_oapi(self.config, filepath)

        return self.get_response(200, headers_, 'openapi.html', response)

    def conformance(self, headers_, args):
        """
        Provide API conformance

        :param headers_: copy of HEADERS object
        :param args: request parameters

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = self.get_content_type(headers_, args)

        response = {
            'conformsTo': CONFORMANCE_CLASSES
        }

        return self.get_response(200, headers_, 'conformance.html', response)

    def collections(self, headers_, args):
        """
        Provide API collections

        :param headers_: copy of HEADERS object
        :param args: request parameters

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = self.get_content_type(headers_, args)

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
        url_base = f"{self.config['server']['url']}/collections"

        is_html = headers_['Content-Type'] == 'text/html'

        response['links'] = [{
            'rel': 'self' if not is_html else 'alternate',
            'type': 'application/json',
            'title': 'This document as JSON',
            'href': f"{url_base}?f=json",
            'hreflang': self.config['server']['language']
        }, {
            'rel': 'self' if is_html else 'alternate',
            'type': 'text/html',
            'title': 'This document as HTML',
            'href': f"{url_base}?f=html",
            'hreflang': self.config['server']['language']
        }]

        return self.get_response(200, headers_, 'collections.html', response)

    def collection(self, headers_, args, collection='metadata:main'):
        """
        Provide API collections

        :param headers_: copy of HEADERS object
        :param args: request parameters
        :param collection: collection name

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = self.get_content_type(headers_, args)

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

        is_html = headers_['Content-Type'] == 'text/html'

        response['links'] = [{
            'rel': 'self' if not is_html else 'alternate',
            'type': 'application/json',
            'title': 'This document as JSON',
            'href': f"{url_base}?f=json",
            'hreflang': self.config['server']['language']
        }, {
            'rel': 'self' if is_html else 'alternate',
            'type': 'text/html',
            'title': 'This document as HTML',
            'href': f"{url_base}?f=html",
            'hreflang': self.config['server']['language']
        }]

        return self.get_response(200, headers_, 'collection.html', response)

    def queryables(self, headers_, args, collection='metadata:main'):
        """
        Provide collection queryables

        :param headers_: copy of HEADERS object
        :param args: request parameters
        :param collection: name of collection

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = self.get_content_type(headers_, args)

        properties = self.repository.describe()
        properties2 = {}

        for key, value in properties.items():
            if key in self.query_mappings or key == 'geometry':
                properties2[key] = value

        if collection == 'metadata:main':
            title = self.config['metadata:main']['identification_title']
        else:
            title = self.config['metadata:main']['identification_title']
            virtual_collection = self.repository.query_ids([collection])[0]
            title = virtual_collection.title

        response = {
            'id': collection,
            'type': 'object',
            'title': title,
            'properties': properties2,
            '$schema': 'http://json-schema.org/draft/2019-09/schema',
            '$id': f"{self.config['server']['url']}/collections/{collection}/queryables"
        }

        return self.get_response(200, headers_, 'queryables.html', response)

    def items(self, headers_, json_post_data, args, collection='metadata:main',
              stac_item=False):
        """
        Provide collection items

        :param headers_: copy of HEADERS object
        :param args: request parameters
        :param collection: collection name

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = self.get_content_type(headers_, args)

        reserved_query_params = [
            'f',
            'filter',
            'limit',
            'sortby',
            'offset'
        ]

        response = {
            'type': 'FeatureCollection',
            'features': [],
            'links': []
        }

        cql_query = None
        query_parser = None
        sortby = None
        limit = None
        collections = []

        if stac_item and json_post_data is not None:
            LOGGER.debug(f'JSON POST data: {json_post_data}')
            LOGGER.debug('Transforming JSON POST data into request args')

            for p in ['limit', 'bbox', 'datetime']:
                if p in json_post_data:
                    if p == 'bbox':
                        args[p] = ','.join(map(str, json_post_data.get(p)))
                    else:
                        args[p] = json_post_data.get(p)

            if 'sortby' in json_post_data:
                LOGGER.debug('Detected sortby')
                args['sortby'] = json_post_data['sortby'][0]['field']
                if json_post_data['sortby'][0].get('direction', 'asc') == 'desc':
                    args['sortby'] = f"-{args['sortby']}"

            LOGGER.debug(f'Transformed args: {args}')

        if 'filter' in args:
            LOGGER.debug(f'CQL query specified {args["filter"]}')
            cql_query = args['filter']

        LOGGER.debug('Transforming property filters into CQL')
        query_args = []
        for k, v in args.items():
            if k in reserved_query_params:
                continue

            if k not in reserved_query_params:
                if k == 'anytext':
                    query_args.append(build_anytext(k, v))
                elif k == 'bbox':
                    query_args.append(f'BBOX(geometry, {v})')
                elif k == 'keywords':
                    query_args.append(f"keywords ILIKE '%{v}%'")
                elif k == 'datetime':
                    if '/' not in v:
                        query_args.append(f'date = "{v}"')
                    else:
                        begin, end = v.split('/')
                        if begin != '..':
                            query_args.append(f'time_begin >= "{begin}"')
                        if end != '..':
                            query_args.append(f'time_end <= "{end}"')
                elif k == 'q':
                    if v not in [None,'']:
                        query_args.append(build_anytext('anytext', v))
                else:
                    query_args.append(f'{k} = "{v}"')

        if collection != 'metadata:main' and not stac_item:
            LOGGER.debug('Adding virtual collection filter')
            query_args.append(f'parentidentifier = "{collection}"')

        LOGGER.debug('Evaluating CQL and other specified filtering parameters')
        if cql_query is not None and query_args:
            LOGGER.debug('Combining CQL and other specified filtering parameters')
            cql_query += ' AND ' + ' AND '.join(query_args)
        elif cql_query is not None and not query_args:
            LOGGER.debug('Just CQL detected')
        elif cql_query is None and query_args:
            LOGGER.debug('Just other specified filtering parameters detected')
            cql_query = ' AND '.join(query_args)

        LOGGER.debug(f'CQL query: {cql_query}')

        if cql_query is not None:
            LOGGER.debug('Detected CQL text')
            query_parser = parse_ecql
        elif json_post_data is not None:
            if 'limit' in json_post_data:
                limit = json_post_data.pop('limit')
            if 'sortby' in json_post_data:
                sortby = json_post_data.pop('sortby')
            if 'collections' in json_post_data:
                collections = json_post_data.pop('collections')
            if not json_post_data:
                LOGGER.debug('No CQL specified, only query parameters')
                json_post_data = {}
            if not json_post_data and collections and collections != ['metadata:main']:
                json_post_data = {'eq': [{'property': 'parentidentifier'}, collections[0]]}

            cql_query = json_post_data
            LOGGER.debug('Detected CQL JSON; ignoring all other query predicates')
            query_parser = parse_cql2_json

        if query_parser is not None and json_post_data != {}:
            LOGGER.debug('Parsing CQL into AST')
            try:
                ast = query_parser(cql_query)
                LOGGER.debug(f'Abstract syntax tree: {ast}')
            except Exception as err:
                msg = f'CQL parsing error: {str(err)}'
                LOGGER.exception(msg)
                return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

            LOGGER.debug('Transforming AST into filters')
            try:
                filters = to_filter(ast, self.repository.dbtype, self.query_mappings)
                LOGGER.debug(f'Filter: {filters}')
            except Exception as err:
                msg = f'CQL evaluator error: {str(err)}'
                LOGGER.exception(msg)
                return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

            query = self.repository.session.query(self.repository.dataset).filter(filters)
        else:
            query = self.repository.session.query(self.repository.dataset)

        if 'sortby' in args:
            LOGGER.debug('sortby specified')
            sortby = args['sortby']

        if sortby is not None:
            LOGGER.debug('processing sortby')
            if sortby.startswith('-'):
                sortby = sortby.lstrip('-')

            if sortby not in list(self.query_mappings.keys()):
                msg = 'Invalid sortby property'
                LOGGER.exception(msg)
                return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

            if args['sortby'].startswith('-'):
                query = query.order_by(self.query_mappings[sortby].desc())
            else:
                query = query.order_by(self.query_mappings[sortby])

        if limit is None and 'limit' in args:
            limit = int(args['limit'])
            LOGGER.debug('limit specified')
            if limit < 1:
                msg = 'Limit must be a positive integer'
                LOGGER.exception(msg)
                return self.get_exception(400, headers_, 'InvalidParameterValue', msg)
            if limit > self.maxrecords:
                limit = self.maxrecords
        else:
            limit = self.maxrecords

        offset = int(args.get('offset', 0))

        LOGGER.debug(f'Query: {query}')
        LOGGER.debug('Querying repository')
        count = query.count()
        records = query.limit(limit).offset(offset).all()

        returned = len(records)

        response['numberMatched'] = count
        response['numberReturned'] = returned

        for record in records:
            response['features'].append(record2json(record, self.config['server']['url'], collection, stac_item))

        LOGGER.debug('Creating links')

        link_args = {**args}

        link_args.pop('f', None)

        if stac_item:
            fragment = 'search'
        else:
            fragment = f'collections/{collection}/items'

        if link_args:
            url_base = f"{self.config['server']['url']}/{fragment}?{urlencode(link_args)}"
        else:
            url_base = f"{self.config['server']['url']}/{fragment}"

        is_html = headers_['Content-Type'] == 'text/html'

        response['links'].extend([{
            'rel': 'self' if not is_html else 'alternate',
            'type': 'application/geo+json',
            'title': 'This document as GeoJSON',
            'href': f"{bind_url(url_base)}f=json",
            'hreflang': self.config['server']['language']
        }, {
            'rel': 'self' if is_html else 'alternate',
            'type': 'text/html',
            'title': 'This document as HTML',
            'href': f"{bind_url(url_base)}f=html",
            'hreflang': self.config['server']['language']
        }, {
            'rel': 'collection',
            'type': 'application/json',
            'title': 'Collection URL',
            'href': f"{self.config['server']['url']}/collections/{collection}",
            'hreflang': self.config['server']['language']
        }])

        if offset > 0:
            link_args.pop('offset', None)

            prev = max(0, offset - limit)

            url_ = f"{self.config['server']['url']}/{fragment}?{urlencode(link_args)}"

            response['links'].append(
                {
                    'type': 'application/geo+json',
                    'rel': 'prev',
                    'title': 'items (prev)',
                    'href': f"{bind_url(url_)}offset={prev}",
                    'hreflang': self.config['server']['language']
                })

        if (offset + returned) < count:
            link_args.pop('offset', None)

            next_ = offset + returned

            url_ = f"{self.config['server']['url']}/{fragment}?{urlencode(link_args)}"

            response['links'].append({
                'rel': 'next',
                'type': 'application/geo+json',
                'title': 'items (next)',
                'href': f"{bind_url(url_)}offset={next_}",
                'hreflang': self.config['server']['language']
            })

        if headers_['Content-Type'] == 'text/html':
            response['title'] = self.config['metadata:main']['identification_title']
            response['collection'] = collection

        if stac_item:
            template = 'stac_items.html'
        else:
            template = 'items.html'

        return self.get_response(200, headers_, template, response)

    def item(self, headers_, args, collection, item, stac_item=False):
        """
        Provide collection item

        :param headers_: copy of HEADERS object
        :param args: request parameters
        :param collection: name of collection
        :param item: record identifier

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = self.get_content_type(headers_, args)

        LOGGER.debug(f'Querying repository for item {item}')
        try:
            record = self.repository.query_ids([item])[0]
        except IndexError:
            return self.get_exception(
                    404, headers_, 'InvalidParameterValue', 'item not found')

        if headers_['Content-Type'] == 'application/xml':
            return headers_, 200, record.xml

        response = record2json(record, self.config['server']['url'], collection, stac_item)

        if headers_['Content-Type'] == 'text/html':
            response['title'] = self.config['metadata:main']['identification_title']
            response['collection'] = collection

        return self.get_response(200, headers_, 'item.html', response)

    def manage_collection_item(self, headers_, action='create', item=None, data=None):
        """
        :param action: action (create, update, delete)
        :param item: record identifier
        :param data: raw data / payload

        :returns: tuple of headers, status code, content
        """

        if self.config.get('manager', 'transactions') != 'true':
            return self.get_exception(
                    405, headers_, 'InvalidParameterValue',
                    'transactions not allowed')

        if action in ['create', 'update'] and data is None:
            msg = 'No data found'
            LOGGER.error(msg)
            return self.get_exception(
                400, headers_, 'InvalidParameterValue', msg)

        if action in ['create', 'update']:
            try:
                record = parse_record(self.context, data, self.repository)[0]
            except Exception as err:
                msg = f'Failed to parse data: {err}'
                LOGGER.exception(msg)
                return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

            if not hasattr(record, 'identifier'):
                msg = 'Record requires an identifier'
                LOGGER.exception(msg)
                return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

        if action == 'create':
            LOGGER.debug('Creating new record')
            LOGGER.debug(f'Querying repository for item {item}')
            try:
                _ = self.repository.query_ids([record.identifier])[0]
                return self.get_exception(
                    404, headers_, 'InvalidParameterValue', 'item exists')
            except Exception:
                LOGGER.debug('Identifier does not exist')

            # insert new record
            try:
                self.repository.insert(record, 'local', get_today_and_now())
            except Exception as err:
                msg = f'Record creation failed: {err}'
                LOGGER.exception(msg)
                return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

            code = 201
            response = {}

        elif action == 'update':
            LOGGER.debug(f'Querying repository for item {item}')
            try:
                _ = self.repository.query_ids([record.identifier])[0]
            except Exception:
                msg = 'Identifier does not exist'
                LOGGER.debug(msg)
                return self.get_exception(404, headers_, 'InvalidParameterValue', msg)

            _ = self.repository.update(record)

            code = 204
            response = {}

        elif action == 'delete':
            constraint = {
                'where': 'identifier = \'%s\'' % item,
                'values': [item]
            }
            _ = self.repository.delete(constraint)

            code = 200
            response = {}

        return self.get_response(code, headers_, None, response)

    def get_exception(self, status, headers, code, description):
        """
        Provide exception report

        :param status: `int` of HTTP status code
        :param headers_: copy of HEADERS object
        :param code: exception code
        :param description: exception description

        :returns: tuple of headers, status code, content
        """

        exception = {
            'code': code,
            'description': description
        }

        return self.get_response(status, headers, 'exception.html', exception)

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
            title = self.config['metadata:main']['identification_title']
            description = self.config['metadata:main']['identification_abstract']
        else:
            id_ = collection_name
            title = collection_info.get('title')
            description = collection_info.get('description')

        return {
            'id': id_,
            'title': title,
            'description': description,
            'itemType': 'record',
            'crs': 'http://www.opengis.net/def/crs/OGC/1.3/CRS84',
            'links': [{
                'rel': 'collection',
                'type': 'application/json',
                'title': 'Collection URL',
                'href': f"{self.config['server']['url']}/collections/{collection_name}",
                'hreflang': self.config['server']['language']
            }, {
                'rel': 'queryables',
                'type': 'application/json',
                'title': 'Collection queryables',
                'href': f"{self.config['server']['url']}/collections/{collection_name}/queryables",
                'hreflang': self.config['server']['language']
            }, {
                'rel': 'items',
                'type': 'application/json',
                'title': 'Collection items as GeoJSON',
                'href': f"{self.config['server']['url']}/collections/{collection_name}/items",
                'hreflang': self.config['server']['language']
            }]
        }


def record2json(record, url, collection, stac_item=False):
    """
    OGC API - Records record generator from core pycsw record model

    :param record: pycsw record object
    :param url: server URL
    :param collection: collection id
    :stac_item: whether the result should be a STAC item (default False)

    :returns: `dict` of record GeoJSON
    """

    if record.metadata_type == 'application/json':
        LOGGER.debug('Returning native JSON representation')
        return json.loads(record.metadata)

    record_dict = {
        'id': record.identifier,
        'type': 'Feature',
        'geometry': None,
        'time': record.date,
        'properties': {},
        'links': [],
        'assets': {}
    }

    if stac_item:
        record_dict['stac_version'] = '1.0.0'
        record_dict['collection'] = 'metadata:main'

    record_dict['properties']['recordUpdated'] = record.insert_date

    if record.type:
        record_dict['properties']['type'] = record.type

    if record.date_creation:
        record_dict['properties']['created'] = record.date_creation

    if record.date_modified:
        record_dict['properties']['updated'] = record.date_modified

    if record.language:
        record_dict['properties']['language'] = record.language

    #externalids: [{scheme:xxx, value:yyy}]
    if record.source:
        record_dict['properties']['externalIds'] = [{'value': record.source}]

    if record.title:
        record_dict['properties']['title'] = record.title

    if record.abstract:
        record_dict['properties']['description'] = record.abstract

    if record.format:
        record_dict['properties']['formats'] = [record.format]

    if record.keywords:
        record_dict['properties']['keywords'] = [x for x in record.keywords.split(',')]

    if record.links:
        rdl = record_dict['links']

        for link in jsonify_links(record.links):
            link2 = {
                'href': link['url'],
                'name': link['name'],
                'description': link['description'],
                'type': link['protocol']
            }
            if 'rel' in link:
                link2['rel'] = link['rel']
            elif link['protocol'] == 'WWW:LINK-1.0-http--image-thumbnail':
                link2['rel'] = 'preview'
            elif 'function' in link:
                link2['rel'] = link['function']

            rdl.append(link2)

    record_dict['links'].append({
        'rel': 'collection',
        'type': 'application/json',
        'title': 'Collection',
        'name': 'collection',
        'description': 'Collection',
        'href': f"{url}/collections/{collection}"
    })

    if record.wkt_geometry:
        minx, miny, maxx, maxy = wkt2geom(record.wkt_geometry)
        geometry = {
            'type': 'Polygon',
            'coordinates': [[
                [minx, miny],
                [minx, maxy],
                [maxx, maxy],
                [maxx, miny],
                [minx, miny]
            ]]
        }
        record_dict['geometry'] = geometry

    if record.time_begin or record.time_end:
        if record.time_end not in [None, '']:
            if record.time_begin not in [None, '']:
                record_dict['time'] = [record.time_begin, record.time_end]
            else:
                record_dict['time'] = record.time_end
        else:
            record_dict['time'] = record.time_begin

    return record_dict


def build_anytext(name, value):
    """
    deconstructs free-text search into CQL predicate(s)

    :param name: property name
    :param name: property value

    :returns: string of CQL predicate(s)
    """

    predicates = []
    tokens = value.split()

    if len(tokens) == 1:  # single term
        return f"{name} ILIKE '%{value}%'"

    for token in tokens:
        predicates.append(f"{name} ILIKE '%{token}%'")

    return f"({' AND '.join(predicates)})"
