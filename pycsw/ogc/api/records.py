# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2025 Tom Kralidis
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

import json
import logging
from operator import itemgetter
import os
from urllib.parse import urlencode, quote

from owslib.ogcapi.records import Records
from pygeofilter.parsers.ecql import parse as parse_ecql
from pygeofilter.parsers.cql2_json import parse as parse_cql2_json

from pycsw import __version__
from pycsw.core import log
from pycsw.core.config import StaticContext
from pycsw.core.metadata import parse_record
from pycsw.core.pygeofilter_evaluate import to_filter
from pycsw.core.util import bind_url, get_today_and_now, jsonify_links, load_custom_repo_mappings, str2bool, wkt2geom
from pycsw.ogc.api.oapi import gen_oapi
from pycsw.ogc.api.util import match_env_var, render_j2_template, to_json, to_rfc3339

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
    'http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/queryables-query-parameters',  # noqa
    'http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/filter',
    'http://www.opengis.net/spec/ogcapi-features-3/1.0/conf/features-filter',
    'http://www.opengis.net/spec/ogcapi-features-4/1.0/conf/create-replace-delete',  # noqa
    'http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/core',
    'http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/sorting',
    'http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/json',
    'http://www.opengis.net/spec/ogcapi-records-1/1.0/conf/html',
    'http://www.opengis.net/spec/cql2/1.0/conf/cql2-json',
    'http://www.opengis.net/spec/cql2/1.0/conf/cql2-text'
]


class API:
    """API object"""

    def __init__(self, config: dict):
        """
        constructor

        :param config: pycsw configuration dict

        :returns: `pycsw.ogc.api.API` instance
        """

        self.mode = 'ogcapi-records'
        self.config = config

        log.setup_logger(self.config.get('logging', {}))

        if self.config['server']['url'].startswith('${'):
            LOGGER.debug(f"Server URL is an environment variable: {self.config['server']['url']}")
            url_ = match_env_var(self.config['server']['url'])
        else:
            url_ = self.config['server']['url']

        LOGGER.debug(f'Server URL: {url_}')
        self.config['server']['url'] = url_.rstrip('/')
        self.facets = self.config['repository'].get('facets', ['type'])

        self.context = StaticContext()

        LOGGER.debug('Setting limit')
        try:
            self.limit = int(self.config['server']['maxrecords'])
        except KeyError:
            self.limit = 10
        LOGGER.debug(f'limit: {self.limit}')

        repo_filter = self.config['repository'].get('filter')

        custom_mappings_path = self.config['repository'].get('mappings')
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
                self.config['repository']['database'],
                self.context,
                table=self.config['repository']['table'],
                repo_filter=repo_filter
            )
            LOGGER.debug(f'Repository loaded {self.repository.dbtype}')
        except Exception as err:
            msg = f'Could not load repository {err}'
            LOGGER.exception(msg)
            raise

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

    def get_response(self, status, headers, data, template=None):
        """
        Provide response

        :param status: `int` of HTTP status
        :param headers: `dict` of HTTP request headers
        :param data: `dict` of response data
        :param template: template filename (default is `None`)

        :returns: tuple of headers, status code, content
        """

        if headers.get('Content-Type') == 'text/html' and template is not None:
            content = render_j2_template(self.config, template, data)
        else:
            pretty_print = str2bool(self.config['server'].get('pretty_print', False))
            content = to_json(data, pretty_print)

        headers['Content-Length'] = len(content.encode('utf-8'))

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
            'id': 'pycsw-catalogue',
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
              'title': 'This document as JSON',
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
              'rel': 'http://www.opengis.net/def/rel/ogc/1.0/queryables',
              'type': 'application/schema+json',
              'title': 'Queryables',
              'href': f"{self.config['server']['url']}/queryables"
            }, {
              'rel': 'child',
              'type': 'application/json',
              'title': 'Main collection',
              'href': f"{self.config['server']['url']}/collections/metadata:main"
            },{
              'rel': 'http://www.opengis.net/def/rel/ogc/1.0/ogc-catalog',
              'type': 'application/json',
              'title': 'Record catalogue collection',
              'href': f"{self.config['server']['url']}/collections/metadata:main"
            }
        ]

        return self.get_response(200, headers_, response, 'landing_page.html')

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

        return self.get_response(200, headers_, response, 'openapi.html')

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

        return self.get_response(200, headers_, response, 'conformance.html')

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

        return self.get_response(200, headers_, response, 'collections.html')

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
        }, {
            'rel': 'items',
            'type': 'application/geo+json',
            'title': 'items as GeoJSON',
            'href': f"{url_base}/items?f=json",
            'hreflang': self.config['server']['language']
        }, {
            'rel': 'items',
            'type': 'text/html',
            'title': 'items as HTML',
            'href': f"{url_base}/items?f=html",
            'hreflang': self.config['server']['language']
        }, {
            'rel': 'http://www.opengis.net/def/rel/ogc/1.0/queryables',
            'type': 'application/schema+json',
            'title': 'Queryables as JSON',
            'href': f"{url_base}/queryables?f=json",
            'hreflang': self.config['server']['language']
        }, {
            'rel': 'http://www.opengis.net/def/rel/ogc/1.0/queryables',
            'type': 'text/html',
            'title': 'Queryables as HTML',
            'href': f"{url_base}/queryables?f=html",
            'hreflang': self.config['server']['language']
        }]

        return self.get_response(200, headers_, response, 'collection.html')

    def queryables(self, headers_, args, collection='metadata:main'):
        """
        Provide collection queryables

        :param headers_: copy of HEADERS object
        :param args: request parameters
        :param collection: name of collection

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = self.get_content_type(headers_, args)

        if 'json' in headers_['Content-Type']:
            headers_['Content-Type'] = 'application/schema+json'

        if collection not in self.get_all_collections():
            msg = 'Invalid collection'
            LOGGER.exception(msg)
            return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

        properties = self.repository.describe()
        properties2 = {}

        for key, value in properties.items():
            if key in self.repository.query_mappings or key == 'geometry':
                properties2[key] = value

        if collection == 'metadata:main':
            title = self.config['metadata']['identification']['title']
        else:
            title = self.config['metadata']['identification']['title']
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

        return self.get_response(200, headers_, response, 'queryables.html')

    def items(self, headers_, json_post_data, args, collection='metadata:main'):
        """
        Provide collection items

        :param headers_: copy of HEADERS object
        :param args: request parameters
        :param collection: collection name

        :returns: tuple of headers, status code, content
        """

        LOGGER.debug(f'Request args: {args.keys()}')
        LOGGER.debug('converting request argument names to lower case')
        args = {k.lower(): v for k, v in args.items()}
        LOGGER.debug(f'Request args (lower case): {args.keys()}')

        headers_['Content-Type'] = self.get_content_type(headers_, args)

        reserved_query_params = [
            'distributed',
            'f',
            'facets',
            'filter',
            'filter-lang',
            'limit',
            'sortby',
            'offset'
        ]

        filter_langs = [
            'cql2-json',
            'cql2-text'
        ]

        response = {
            'type': 'FeatureCollection',
            'facets': [],
            'features': [],
            'links': []
        }

        cql_query = None
        query_parser = None
        sortby = None
        limit = None
        bbox = []
        facets_requested = False
        collections = []

        if collection not in self.get_all_collections():
            msg = 'Invalid collection'
            LOGGER.exception(msg)
            return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

        if json_post_data is not None:
            LOGGER.debug(f'JSON POST data: {json_post_data}')
            LOGGER.debug('Transforming JSON POST data into request args')

            for p in ['limit', 'bbox', 'datetime', 'collections']:
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
            filter_lang = args.get('filter-lang')
            if filter_lang is not None and filter_lang not in filter_langs:
                msg = f'Invalid filter-lang, available: {", ".join(filter_langs)}'
                LOGGER.exception(f'{msg} Used: {filter_lang}')
                return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

        LOGGER.debug('Transforming property filters into CQL')
        query_args = []
        for k, v in args.items():
            if k in reserved_query_params:
                continue

            if k not in reserved_query_params:
                if k == 'ids':
                    ids = ','.join(f'"{x}"' for x in v.split(','))
                    query_args.append(f"identifier IN ({ids})")
                elif k == 'collections':
                    if isinstance(v, str):
                        collections = ','.join(f'"{x}"' for x in v.split(','))
                    else:
                        collections = ','.join(f'"{x}"' for x in v)
                    query_args.append(f"parentidentifier IN ({collections})")
                elif k == 'anytext':
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
                    if v not in [None, '']:
                        query_args.append(build_anytext('anytext', v))
                else:
                    query_args.append(f'{k} = "{v}"')

        facets_requested = str2bool(args.get('facets', False))

        if collection != 'metadata:main':
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
            if 'bbox' in json_post_data:
                bbox = json_post_data.pop('bbox')
            if not json_post_data:
                LOGGER.debug('No CQL specified, only query parameters')
                json_post_data = {}
            if not json_post_data and collections and collections != ['metadata:main']:
                json_post_data = {'op': 'eq', 'args': [{'property': 'parentidentifier'}, collections[0]]}
                if bbox:
                    json_post_data = {
                        'op': 'and',
                        'args': [{
                           'op': 's_intersects',
                           'args': [
                               {'property': 'geometry2'},
                               {'bbox': [bbox]}
                           ]},
                           json_post_data
                        ]
                    }

            cql_query = json_post_data
            LOGGER.debug('Detected CQL JSON; ignoring all other query predicates')
            query_parser = parse_cql2_json

        LOGGER.debug(f'query parser: {query_parser}')

        if query_parser is not None and json_post_data != {}:
            LOGGER.debug('Parsing CQL into AST')
            LOGGER.debug(json_post_data)
            LOGGER.debug(cql_query)
            try:
                ast = query_parser(cql_query)
                LOGGER.debug(f'Abstract syntax tree: {ast}')
            except Exception as err:
                msg = f'CQL parsing error: {str(err)}'
                LOGGER.exception(msg)
                return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

            LOGGER.debug('Transforming AST into filters')
            try:
                filters = to_filter(ast, self.repository.dbtype, self.repository.query_mappings)
                LOGGER.debug(f'Filter: {filters}')
            except Exception as err:
                msg = f'CQL evaluator error: {str(err)}'
                LOGGER.exception(msg)
                return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

            query = self.repository.session.query(self.repository.dataset).filter(filters)
            if facets_requested:
                LOGGER.debug('Running facet query')
                facets_results = self.get_facets(filters)
        else:
            query = self.repository.session.query(self.repository.dataset)
            facets_results = self.get_facets()

        if facets_requested:
            response['facets'] = facets_results
        else:
            response.pop('facets')

        if 'sortby' in args:
            LOGGER.debug('sortby specified')
            sortby = args['sortby']

        if sortby is not None:
            LOGGER.debug('processing sortby')
            if sortby.startswith('-'):
                sortby = sortby.lstrip('-')

            if sortby not in list(self.repository.query_mappings.keys()):
                msg = 'Invalid sortby property'
                LOGGER.exception(msg)
                return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

            if args['sortby'].startswith('-'):
                query = query.order_by(self.repository.query_mappings[sortby].desc())
            else:
                query = query.order_by(self.repository.query_mappings[sortby])

        if limit is None and 'limit' in args:
            limit = int(args['limit'])
            LOGGER.debug('limit specified')
            if limit < 1:
                msg = 'Limit must be a positive integer'
                LOGGER.exception(msg)
                return self.get_exception(400, headers_, 'InvalidParameterValue', msg)
            if limit > self.limit:
                limit = self.limit
        else:
            limit = self.limit

        offset = int(args.get('offset', 0))

        LOGGER.debug(f'Query: {query}')
        LOGGER.debug('Querying repository')
        count = query.count()
        records = query.limit(limit).offset(offset).all()

        returned = len(records)

        response['numberMatched'] = count
        response['numberReturned'] = returned

        for record in records:
            response['features'].append(record2json(record, self.config['server']['url'], collection, self.mode))

        response['distributedFeatures'] = []

        distributed = str2bool(args.get('distributed', False))

        if distributed:
            for fc in self.config.get('federatedcatalogues', []):
                LOGGER.debug(f'Running distributed search against {fc}')
                fc_url, _, fc_collection = fc.rsplit('/', 2)
                try:
                    w = Records(fc_url)
                    fc_results = w.collection_items(fc_collection, **args)
                    for feature in fc_results['features']:
                        response['distributedFeatures'].append(feature)
                except Exception as err:
                    LOGGER.warning(err)

        LOGGER.debug('Creating links')

        link_args = {**args}

        link_args.pop('f', None)

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
            response['title'] = self.config['metadata']['identification']['title']
            response['collection'] = collection

        template = 'items.html'

        return self.get_response(200, headers_, response, template)

    def item(self, headers_, args, collection, item):
        """
        Provide collection item

        :param headers_: copy of HEADERS object
        :param args: request parameters
        :param collection: name of collection
        :param item: record identifier

        :returns: tuple of headers, status code, content
        """

        record = None
        headers_['Content-Type'] = self.get_content_type(headers_, args)

        if collection not in self.get_all_collections():
            msg = 'Invalid collection'
            LOGGER.exception(msg)
            return self.get_exception(400, headers_, 'InvalidParameterValue', msg)

        LOGGER.debug(f'Querying repository for item {item}')
        try:
            record = self.repository.query_ids([item])[0]
            response = record2json(record, self.config['server']['url'],
                                   collection, self.mode)
        except IndexError:
            distributed = str2bool(args.get('distributed', False))

            if distributed:
                for fc in self.config.get('federatedcatalogues', []):
                    LOGGER.debug(f'Running distributed item search against {fc}')
                    fc_url, _, fc_collection = fc.rsplit('/', 2)
                    try:
                        w = Records(fc_url)
                        response = record = w.collection_item(fc_collection, item)
                        LOGGER.debug(f'Found item from {fc}')
                        break
                    except RuntimeError:
                        continue

        if record is None:
            return self.get_exception(
                    404, headers_, 'InvalidParameterValue', 'item not found')

        if headers_['Content-Type'] == 'application/xml':
            return headers_, 200, record.xml

        if headers_['Content-Type'] == 'text/html':
            response['title'] = self.config['metadata']['identification']['title']
            response['collection'] = collection

        if 'json' in headers_['Content-Type']:
            headers_['Content-Type'] = 'application/geo+json'

        return self.get_response(200, headers_, response, 'item.html')

    def manage_collection_item(self, headers_, action='create', item=None, data=None):
        """
        :param action: action (create, update, delete)
        :param item: record identifier
        :param data: raw data / payload

        :returns: tuple of headers, status code, content
        """

        if not self.config['manager']['transactions']:
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
                    400, headers_, 'InvalidParameterValue', 'item exists')
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

        return self.get_response(code, headers_, response)

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

        return self.get_response(status, headers, exception, 'exception.html')

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
            description = self.config['metadata']['identification']['description']
        else:
            id_ = collection_name
            title = collection_info.get('title')
            description = collection_info.get('description')

        collection_info = {
            'id': id_,
            'type': 'catalog',
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
                'rel': 'http://www.opengis.net/def/rel/ogc/1.0/ogc-catalog',
                'type': 'application/json',
                'title': 'Record catalog collection',
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
                'type': 'application/geo+json',
                'title': 'Collection items as GeoJSON',
                'href': f"{self.config['server']['url']}/collections/{collection_name}/items",
                'hreflang': self.config['server']['language']
            }]
        }

        if collection_name == 'metadata:main':
            if 'federatedcatalogues' in self.config:
                LOGGER.debug('Adding federated catalogues')
                collection_info['federatedCatalogues'] = []
                if self.config.get('federatedcatalogues') not in [None, '']:  # if empty in config
                    for fc in self.config.get('federatedcatalogues'):
                        collection_info['federatedCatalogues'].append({
                            'type': 'OGC API - Records',
                            'url': fc
                        })

        return collection_info

    def get_all_collections(self) -> list:
        """
        Get all collections

        :returns: `list` of collection identifiers
        """

        default_collection = 'metadata:main'
        virtual_collections = self.repository.query_collections()

        return [default_collection] + [vc.identifier for vc in virtual_collections]

    def get_facets(self, filters=None) -> dict:
        """
        Gets all facets for a given query

        :returns: `dict` of facets
        """

        facets_results = {}

        for facet in self.facets:
            LOGGER.debug(f'Running facet for {facet}')
            facetq = self.repository.session.query(self.repository.query_mappings[facet], self.repository.func.count(facet)).group_by(facet)

            if filters is not None:
                facetq = facetq.filter(filters)

            LOGGER.debug('Writing facet query results')
            facets_results[facet] = {
                'type': 'terms',
                'property': facet,
                'buckets': []
            }

            for fq in facetq.all():
                facets_results[facet]['buckets'].append({
                    'value': fq[0],
                    'count': fq[1]
                })

            facets_results[facet]['buckets'].sort(key=itemgetter('count'), reverse=True)

        return facets_results


def record2json(record, url, collection, mode='ogcapi-records'):
    """
    OGC API - Records record generator from core pycsw record model

    :param record: pycsw record object
    :param url: server URL
    :param collection: collection id
    :param mode: `str` of API mode

    :returns: `dict` of record GeoJSON
    """

    if record.metadata_type == 'application/json':
        rec = json.loads(record.metadata)
        if rec.get('stac_version') is not None and rec['type'] == 'Feature' and mode == 'stac-api':
            LOGGER.debug('Returning native STAC representation')
            rec['links'].extend([{
                'rel': 'self',
                'type': 'application/geo+json',
                'href': f"{url}/collections/{collection}/items/{rec['id']}"
                }, {
                'rel': 'root',
                'type': 'application/json',
                'href': url
                }, {
                'rel': 'parent',
                'type': 'application/json',
                'href': f"{url}/collections/{collection}"
                }, {
                'rel': 'collection',
                'type': 'application/json',
                'href': f"{url}/collections/{collection}"
                }
            ])

            return rec

        LOGGER.debug('Removing STAC version')
        _ = rec.pop('stac_version', None)
        _ = rec.pop('stac_extensions', None)
        LOGGER.debug('Transforming assets to enclosure links')
        assets = rec.pop('assets', {})
        for key, value in assets.items():
            value['rel'] = 'enclosure'
            value['name'] = key
            rec['links'].append(value)

        return rec

    record_dict = {
        'id': record.identifier,
        'type': 'Feature',
        'geometry': None,
        'properties': {},
        'links': []
    }

    try:
        dt, dt_type = to_rfc3339(record.date)
        record_dict['time'] = {
            dt_type: dt
        }
    except Exception:
        record_dict['time'] = None

    # todo; for keywords with a scheme use the theme property
    if record.topicategory:
        tctheme = {
            'concepts': [],
            'scheme': 'https://standards.iso.org/iso/19139/resources/gmxCodelists.xml#MD_TopicCategoryCode'
        }

        if isinstance(record.topicategory, list):
            for rtp in record.topicategory:
                tctheme['concepts'].append({'id': rtp})
        elif isinstance(record.topicategory, str):
            tctheme['concepts'].append({'id': record.topicategory})

        record_dict['properties']['themes'] = [tctheme]

    if record.otherconstraints:
        if isinstance(record.otherconstraints, str) and record.otherconstraints not in [None, 'None']:
            record.otherconstraints = [record.otherconstraints]
            record_dict['properties']['license'] = ", ".join(record.otherconstraints)

    if record.conditionapplyingtoaccessanduse:
        if isinstance(record.conditionapplyingtoaccessanduse, str) and record.conditionapplyingtoaccessanduse not in [None, 'None']:
            record_dict['properties']['rights'] = record.conditionapplyingtoaccessanduse

    record_dict['properties']['updated'] = record.insert_date

    if record.type:
        record_dict['properties']['type'] = record.type

    if record.date_creation:
        record_dict['properties']['created'] = record.date_creation

    if record.date_modified:
        record_dict['properties']['updated'] = record.date_modified

    if record.language:
        record_dict['properties']['language'] = record.language

    if record.source:
        record_dict['properties']['externalIds'] = [{'value': record.source}]

    if record.title:
        record_dict['properties']['title'] = record.title

    if record.abstract:
        record_dict['properties']['description'] = record.abstract

    if record.format:
        record_dict['properties']['formats'] = [{'name': f} for f in record.format.split(',') if len(f) > 1]

    if record.keywords:
        record_dict['properties']['keywords'] = [x for x in record.keywords.split(',')]

    if record.contacts not in [None, '', 'null']:
        rcnt = []
        roles = []
        try:
            for cnt in json.loads(record.contacts):
                try:
                    roles.append(cnt.get('role', '').lower())
                    rcnt.append({
                        'name': cnt['name'],
                        'organization': cnt.get('organization', ''),
                        'position': cnt.get('position', ''),
                        'roles': [cnt.get('role', '')],
                        'phones': [{
                            'value': cnt.get('phone', '')
                        }],
                        'emails': [{
                            'value': cnt.get('email', '')
                        }],
                        'addresses': [{
                            'deliveryPoint': [cnt.get('address', '')],
                            'city': cnt.get('city', ''),
                            'administrativeArea': cnt.get('region', ''),
                            'postalCode': cnt.get('postcode', ''),
                            'country': cnt.get('country', '')
                        }],
                        'links': [{
                            'href': cnt.get('onlineresource')
                        }]
                    })
                except Exception as err:
                    LOGGER.exception(f"failed to parse contact of {record.identifier}: {err}")
            for r2 in "creator,publisher,contributor".split(","):  # match role-fields with contacts
                if r2 not in roles and hasattr(record, r2) and record[r2] not in [None, '']:
                    rcnt.append({
                        'organization': record[r2],
                        'roles': [r2]
                    })

        except Exception as err:
            LOGGER.warning(f"failed to parse contacts json of {record.identifier}: {err}")

        record_dict['properties']['contacts'] = rcnt

    if record.themes not in [None, '', 'null']:
        ogcapi_themes = record_dict['properties'].get('themes', [])
        # For a scheme, prefer uri over label
        # OWSlib currently uses .keywords_object for keywords with url, see https://github.com/geopython/OWSLib/pull/765
        try:
            for theme in json.loads(record.themes):
                try:
                    ogcapi_themes.append({
                        'scheme': theme['thesaurus'].get('url') or theme['thesaurus'].get('title'),
                        'concepts': [{'id': c.get('name', '')} for c in theme.get('keywords', []) if 'name' in c and c['name'] not in [None, '']]
                    })
                except Exception as err:
                    LOGGER.exception(f"failed to parse theme of {record.identifier}: {err}")
        except Exception as err:
            LOGGER.exception(f"failed to parse themes json of {record.identifier}: {err}")

        record_dict['properties']['themes'] = ogcapi_themes

    if record.links:
        rdl = record_dict['links']

        for link in jsonify_links(record.links):
            if link['url'] in [None, 'None']:
                LOGGER.debug(f'Skipping null link: {link}')
                continue

            link2 = {
                'href': link['url']
            }
            if link.get('name') not in [None, 'None']:
                link2['name'] = link['name']
            if link.get('description') not in [None, 'None']:
                link2['description'] = link['description']
            if link.get('protocol') not in [None, 'None']:
                link2['protocol'] = link['protocol']
            if 'rel' in link:
                link2['rel'] = link['rel']
            elif link['protocol'] == 'WWW:LINK-1.0-http--image-thumbnail':
                link2['rel'] = 'preview'
            elif 'function' in link:
                link2['rel'] = link['function']

            rdl.append(link2)

    for lnk in [record.parentidentifier, record.relation]:
        if lnk and len(lnk.strip()) > 0:
            if not lnk.startswith('http'):
                lnk = f"{url}/collections/{collection}/items/{quote(lnk)}"
            record_dict['links'].append({
                'rel': 'related',
                'href': lnk,
                'name': 'related record',
                'description': 'related record',
                'type': 'application/json'
            })

    record_dict['links'].append({
        'rel': 'self',
        'type': 'application/geo+json',
        'title': record.identifier,
        'name': 'item',
        'description': record.identifier,
        'href': f'{url}/collections/{collection}/items/{record.identifier}'
    })

    record_dict['links'].append({
        'rel': 'collection',
        'type': 'application/json',
        'title': 'Collection',
        'name': 'collection',
        'description': 'Collection',
        'href': f'{url}/collections/{collection}'
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
                begin, _ = to_rfc3339(record.time_begin)
                end, _ = to_rfc3339(record.time_end)
                record_dict['time'] = {
                    'interval': [begin, end]
                }
            else:
                end, end_type = to_rfc3339(record.time_end)
                record_dict['time'] = {
                    end_type: end
                }
        else:
            begin, begin_type = to_rfc3339(record.time_begin)
            record_dict['time'] = {
                begin_type: begin
            }

    if mode == 'stac-api':
        date_, date_type = to_rfc3339(record.date)
        record_dict['properties']['datetime'] = date_

        if None not in [record.time_begin, record.time_end]:
            start_date, start_date_type = to_rfc3339(record.time_begin)
            end_date, end_date_type = to_rfc3339(record.time_end)

            record_dict['properties']['start_datetime'] = start_date
            record_dict['properties']['end_datetime'] = end_date

    return record_dict


def build_anytext(name, value):
    """
    deconstructs free-text search into CQL predicate(s)

    :param name: property name
    :param name: property value

    :returns: string of CQL predicate(s)
    """

    LOGGER.debug(f'Name: {name}')
    LOGGER.debug(f'Value: {value}')

    predicates = []
    tokens = value.split(',')

    if len(tokens) == 1 and ' ' not in value:  # single term
        LOGGER.debug('Single term with no spaces')
        return f"{name} ILIKE '%{value}%'"

    for token in tokens:
        if ' ' in token:
            tokens2 = token.split()
            predicates2 = []
            for token2 in tokens2:
                predicates2.append(f"{name} ILIKE '%{token2}%'")

            predicates.append('(' + ' AND '.join(predicates2) + ')')
        else:
            predicates.append(f"{name} ILIKE '%{token}%'")

    return f"({' OR '.join(predicates)})"
