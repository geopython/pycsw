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

from pycql.integrations.sqlalchemy import to_filter, parse

from pycsw import __version__
from pycsw.core.config import StaticContext
from pycsw.core.util import EnvInterpolation, jsonify_links, wkt2geom
from pycsw.ogc.api.util import to_json

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

        :returns: `pycsw.ogc.api.API` instance
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

        LOGGER.debug('Setting maxrecords')
        try:
            self.maxrecords = int(self.config['server']['maxrecords'])
        except KeyError:
            self.maxrecords = 10
        LOGGER.debug(f'maxrecords: {self.maxrecords}')

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
            'record-updated': self.repository.dataset.insert_date,
            'title': self.repository.dataset.title,
            'description': self.repository.dataset.abstract,
            'keywords': self.repository.dataset.keywords,
            'anytext': self.repository.dataset.anytext,
            'bbox': self.repository.dataset.wkt_geometry
        }

    def landing_page(self, headers_, args):
        """
        Provide API landing page

        :param headers_: copy of HEADERS object
        :param args: request parameters

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

        return headers_, 200, to_json(response)

    def conformance(self, headers_, args):
        """
        Provide API conformance

        :param headers_: copy of HEADERS object
        :param args: request parameters

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

        return headers_, 200, to_json(response)

    def collections(self, headers_, args, collection=False):
        """
        Provide API collections

        :param headers_: copy of HEADERS object
        :param args: request parameters
        :param collection: `bool` of whether to emit single collection

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

        return headers_, 200, to_json(response)

    def queryables(self, headers_, args):
        """
        Provide collection queryables

        :param headers_: copy of HEADERS object
        :param args: request parameters

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = 'application/json'

        properties = self.repository.describe()

        response = {
            'type': 'object',
            'title': 'metadata:main',
            'properties': properties,
            '$schema': 'http://json-schema.org/draft/2019-09/schema',
            '$id': f"{self.config['server']['url']}/collections/metadata:main/queryables"
        }

        return headers_, 200, to_json(response)

    def items(self, headers_, args):
        """
        Provide collection items

        :param headers_: copy of HEADERS object
        :param args: request parameters

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = 'application/json'

        reserved_query_params = [
            'cql',
            'limit'
        ]

        response = {
            'type': 'FeatureCollection',
            'features': [],
            'links': []
        }

        cql_query = None

        if 'cql' in args:
            LOGGER.debug(f'CQL query specified {args["cql"]}')
            cql_query = args['cql']

        LOGGER.debug('Transforming property filters into CQL')
        query_args = []
        for k, v in args.items():
            if k in reserved_query_params:
                continue
            if k not in self.query_mappings:
                return self.get_exception(
                    400, headers_, 'InvalidParameterValue', f'Invalid property {k}')

            if k not in reserved_query_params:
                if k == 'anytext':
                    query_args.append(f'{k} LIKE "%{v}%"')
                elif k == 'bbox':
                    query_args.append(f'BBOX(geometry, {v})')
                elif k == 'q':
                    query_args.append(f'ANYTEXT LIKE "%{v}%"')
                else:
                    query_args.append(f'{k} = "{v}"')

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
        print("CQL", cql_query)

        if cql_query is not None:
            LOGGER.debug('Parsing CQL into AST')
            ast = parse(cql_query)
            LOGGER.debug(f'Abstract syntax tree: {ast}')

            LOGGER.debug('Transforming AST into filters')
            filters = to_filter(ast, self.query_mappings)
            LOGGER.debug(f'Filter: {filters}')

            query = self.repository.session.query(self.repository.dataset).filter(filters)
        else:
            query = self.repository.session.query(self.repository.dataset)

        LOGGER.debug(f'Query: {query}')
        LOGGER.debug('Querying repository')
        count = query.count()
        records = query.limit(self.maxrecords).all()

        if count < self.maxrecords:
            returned = count
        else:
            returned = self.maxrecords

        response['numberMatched'] = count
        response['numberReturned'] = returned

        for record in records:
            response['features'].append(record2json(record))

        return headers_, 200, to_json(response)

    def item(self, headers_, args, item):
        """
        Provide collection item

        :param headers_: copy of HEADERS object
        :param args: request parameters
        :param item: record identifier

        :returns: tuple of headers, status code, content
        """

        headers_['Content-Type'] = 'application/json'

        format_ = args.get('f', 'json')

        if format_ == 'xml':
            headers_['Content-Type'] = 'application/xml'
        elif format_ != 'json':
            return self.get_exception(
                400, headers_, 'InvalidParameterValue', 'Invalid format')

        LOGGER.debug(f'Querying repository for item {item}')
        try:
            record = self.repository.query_ids([item])[0]
        except IndexError as err:
            return self.get_exception(
                    404, headers_, 'InvalidParameterValue', 'item not found')

        if format_ == 'json':
            response = record2json(record)
            return headers_, 200, to_json(response)
        elif format_ == 'xml':
            response = record.xml
            return headers_, 200, response


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

        return headers, status, to_json(exception)

def record2json(record):
    """
    OGC API - Records record generator from core pycsw record model

    :param record: pycsw record object

    :returns: `dict` of record GeoJSON
    """

    record_dict = {
        'id': record.identifier,
        'type': 'Feature',
        'geometry': None,
        'properties': {}
    }

    record_dict['properties']['externalId'] = record.identifier

    record_dict['properties']['record-updated'] = record.insert_date

    if record.type:
        record_dict['properties']['type'] = record.type

    if record.date_creation:
        record_dict['properties']['created'] = record.date_creation

    if record.date_modified:
        record_dict['properties']['updated'] = record.date_modified

    if record.language:
        record_dict['properties']['language'] = record.language

    if record.title:
        record_dict['properties']['title'] = record.title

    if record.abstract:
        record_dict['properties']['description'] = record.abstract

    if record.format:
        record_dict['properties']['formats'] = [record.format]

    if record.keywords:
        record_dict['keywords'] = [x for x in record.keywords.split(',')]

    if record.links:
        record_dict['associations'] = []
        for link in jsonify_links(record.links):
            association = {
                'href': link['url'],
                'name': link['name'],
                'description': link['description'],
                'type': link['protocol'],
                'rel': link['type']
            }
            record_dict['associations'].append(association)

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

        record_dict['properties']['extents'] = {
            'spatial': {
                'bbox': [[minx, miny, maxx, maxy]],
                'crs': 'http://www.opengis.net/def/crs/OGC/1.3/CRS84'
            }
        }

    return record_dict
