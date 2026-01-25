# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2026 Tom Kralidis
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

from datetime import datetime
import json
import logging

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Document, Index, Search, Text
from pygeofilter.backends.elasticsearch import to_filter
import requests

LOGGER = logging.getLogger(__name__)

ES_VERSION = '8.3'


class Record(Document):
    identifier = Text()
    parentidentifier = Text()
    title = Text()
    description = Text()
#    anytext = Text()
#    datetime = Text()


class ElasticsearchRepository:
    """
    Class to interact with Elasticsearch metadata repository
    """

    def __init__(self, repo_object: dict, context):
        """
        Initialize repository
        """

        self.database = None
        self.filter = repo_object.get('filter')
        self.context = context
        self.fts = False
        self.label = 'Elasticsearch'
        self.local_ingest = True
        self.dbtype = self.label
        self.username = repo_object.get('username')
        self.password = repo_object.get('password')
        self.authentication = None

        self.query_mappings = {
            # OGC API - Records mappings
            'geometry': 'geometry',
            'identifier': 'identifier',
            'type': 'type',
            'typename': 'typename',
            'parentidentifier': 'parentidentifier',
            'collection': 'collection',
            'collections': 'parentidentifier',
            'updated': 'insert_date',
            'title': 'title',
            'abstract': 'abstract',
            'description': 'abstract',
            'keywords': 'keywords',
            'edition': 'edition',
            'anytext': 'title',
            'bbox': 'wkt_geometry',
            'date': 'date',
            'datetime': 'date',
            'time_begin': 'time_begin',
            'time_end': 'time_end',
            'platform': 'platform',
            'instrument': 'instrument',
            'sensortype': 'sensortype',
            'off_nadir': 'illuminationelevationangle'
        }

        self.es_host, self.index_name = self.filter.rsplit('/', 1)
        self.es_search_url = f'{self.filter}/_search'
        self.es = Elasticsearch(self.es_host)

        # generate core queryables db and obj bindings
        self.queryables = {}

        for tname in self.context.model['typenames']:
            for qname in self.context.model['typenames'][tname]['queryables']:
                self.queryables[qname] = {}
                items = self.context.model['typenames'][tname]['queryables'][
                    qname
                ].items()

                for qkey, qvalue in items:
                    self.queryables[qname][qkey] = qvalue

        # flatten all queryables
        self.queryables['_all'] = {}
        for qbl in self.queryables:
            self.queryables['_all'].update(self.queryables[qbl])
        self.queryables['_all'].update(self.context.md_core_model['mappings'])

        LOGGER.debug('Connecting to Elasticsearch')
        if not self.es.ping():
            msg = f'Cannot connect to Elasticsearch: {self.es_host}'
            LOGGER.error(msg)
            raise RuntimeError(msg)

    def describe(self) -> dict:
        """Derive table columns and types"""

        properties = {
            'geometry': {
                '$ref': 'https://geojson.org/schema/Polygon.json',
                'x-ogc-role': 'primary-geometry'
            }
        }

        i = Index(name=self.index_name, using=self.es)
        mapping = i.get_mapping()[self.index_name]['mappings']['properties']

        LOGGER.debug(f'Response: {mapping}')

        for key, value in mapping.items():
            properties[key] = {
                'type': value.get('type', 'string')
            }

        return properties

    def dataset(self, record={}):
        """
        Stub to mock a pycsw dataset object for Transactions
        """

        return type('dataset', (object,), record)

    def query_ids(self, ids: list) -> list:
        """
        Query by list of identifiers
        """

        results = []

        s = Search(using=self.es, index=self.index_name)
        s = s.query('ids', values=ids)
        response = s.execute()

        for hit in response:
            results.append(self._doc2record(hit))

        return results

    def query_collections(self, filters=None, limit=10) -> list:
        ''' Query for parent collections '''

        results = []
        params = {
            'size': limit
        }

        try:
            response = requests.get(self.es_search_url, params=params,
                                    auth=self.authentication)
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.HTTPError as err:
            msg = f'Elasticsearch query error: {err.response.text}'
            LOGGER.error(msg)
            raise RuntimeError(msg)

        for hit in response['hits']['hits']:
            if hit['_source']['type'] == 'Collection':
                dataset = type('dataset', (object,), hit['_source'])
                dataset.identifier = dataset.id
                dataset.title = hit['_source'].get('title')
                dataset.abstract = hit['_source'].get('description')

                results.append(self._doc2record(hit['_source']))

        return results

    def query_domain(self, domain, typenames, domainquerytype='list',
                     count=False) -> list:
        """
        Query by property domain values
        """

        results = []

        params = {
            'q': '*:*',
            'rows': 0,
            'facet': 'true',
            'facet.query': 'distinct',
            'facet.type': 'terms',
            'facet.field': domain,
            'fq': ['metadata_status:Active']
        }

        try:
            response = requests.get(f'{self.filter}/select', params=params,
                                    auth=self.authentication)
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.HTTPError as err:
            msg = f'Solr query error: {err.response.text}'
            LOGGER.error(msg)
            raise RuntimeError(msg)

        counts = response['facet_counts']['facet_fields'][domain]

        for term in zip(*([iter(counts)] * 2)):
            LOGGER.debug(f'Term: {term}')
            results.append(term)

        return results

    def query_insert(self, direction='max') -> str:
        """
        Query to get latest (default) or earliest update to repository
        """

        if direction == 'min':
            sort_order = 'asc'
        else:
            sort_order = 'desc'

        params = {
            'q': '*:*',
            'q.op': 'OR',
            'fl': 'timestamp',
            'sort': f'timestamp {sort_order}',
            'fq': ['metadata_status:Active'],
        }

        try:
            response = requests.get(f'{self.filter}/select', params=params,
                                    auth=self.authentication)
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.HTTPError as err:
            msg = f'Solr query error: {err.response.text}'
            LOGGER.error(msg)
            raise RuntimeError(msg)

        try:
            timestamp = datetime.strptime(
                response['response']['docs'][0]['timestamp'],
                '%Y-%m-%dT%H:%M:%S.%fZ'
            )
        except IndexError:
            timestamp = datetime.now()

        return timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')

    def query_source(self, source):
        """
        Query by source
        """

        return NotImplementedError()

    def query(self, constraint=None, sortby=None, typenames=None,
              maxrecords=10, startposition=0) -> tuple:
        """
        Query records from underlying repository
        """

        results = []
        record = Record()
        extra = {
            'track_total_hits': True,
            'from_': startposition,
            'size': maxrecords
        }

        es_query = record.search(using=self.es, index=self.index_name)

        if constraint.get('ast') is not None:
            LOGGER.debug(f"Applying filter {constraint['ast']}")

            filter_ = to_filter(constraint['ast'], self.query_mappings,
                                version=ES_VERSION)

            LOGGER.debug(f'filter {filter_}')
            es_query = es_query.query(filter_)

        es_response = es_query.extra(**extra).execute()

        total = es_response.hits.total.value
        LOGGER.debug(f'Found: {total}')

        for doc in es_response:
            results.append(self._doc2record(doc))

        return total, results

    def insert(self, record, source, insert_date):
        item = json.loads(record.metadata)
        LOGGER.debug(f"Inserting/updating item with identifier {item['id']}")
        _ = self.es.index(index=self.index_name, id=item['id'], body=item)
        LOGGER.debug('Item added')

        return item['id']

    def update(self, record=None, recprops=None, constraint=None):
        self.insert(record, None, None)

    def delete(self, constraint):
        LOGGER.debug(f"Deleting item with {constraint['values'][0]}")
        _ = self.es.delete(index=self.index_name, id=constraint['values'][0])

    def _doc2record(self, doc: dict):
        """
        Transform a Solr doc into a pycsw dataset object
        """

        if not isinstance(doc, dict):
            record = doc.to_dict()
        else:
            record = doc

        record['metadata_type'] = 'application/geo+json'
        record['metadata'] = json.dumps(record)
        record['identifier'] = record['id']
        record['parentidentifier'] = record.get('collection')
        record['abstract'] = record.get('description')
        return self.dataset(record)
