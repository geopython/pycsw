# =================================================================
#
# Authors: Massimo Di Stefano <massimods@met.no>
#          Magnar Martinsen <magnarem@met.no>
#          Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2025 Massimo Di Stefano
# Copyright (c) 2025 Magnar Martinsen
# Copyright (c) 2025 Tom Kralidis
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

import base64
from datetime import datetime
import json
import logging
from urllib.parse import urlencode

import dateutil.parser as dparser
from pycsw.core.etree import etree
from pygeofilter.backends.solr.evaluate import to_filter
import requests
from requests.auth import HTTPBasicAuth

LOGGER = logging.getLogger(__name__)


class SolrMETNORepository:
    """
    Class to interact with underlying METNO Solr backend repository
    """

    def __init__(self, repo_object: dict, context):
        """
        Initialize repository
        """

        self.database = None
        self.filter = repo_object.get('filter')
        #
        self.xslt_iso_transformer = repo_object.get('xslt_iso_transformer')
        self.xslt = repo_object.get('xslt')
        #self.mmd_to_iso_xslt = self.xslt[self.xslt_iso_transformer]
        #
        self.context = context
        self.fts = False
        self.label = 'MetNO/Solr'
        self.local_ingest = True
        self.solr_select_url = f'{self.filter}/select'
        self.dbtype = 'Solr'
        self.username = repo_object.get('username')
        self.password = repo_object.get('password')
        self.authentication = HTTPBasicAuth(self.username, self.password)
        self.session = self
        self.adc_collection = repo_object.get('adc_collection')
        # get the Solr mappings for main queryables
        self.query_mappings = repo_object.get('solr_mappings')

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

    def describe(self) -> dict:
        """Derive table columns and types"""

        type_mappings = {
            'TEXT': 'string',
            'VARCHAR': 'string',
            'text_en': 'string',
            'text_general': 'string',
            'pdate': 'string',
            'bbox': 'string',
            'string': 'string'
        }

        try:
            response = requests.get(f'{self.filter}/schema/fields',
                                    auth=self.authentication)
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.HTTPError as err:
            msg = f'Solr query error: {err.response.text}'
            LOGGER.error(msg)
            raise RuntimeError(msg)

        properties = {
            'geometry': {
                '$ref': 'https://geojson.org/schema/Polygon.json',
                'x-ogc-role': 'primary-geometry',
            }
        }

        for field in response.get('fields', []):
            if field['name'] in self.query_mappings.values():
                pname = dict((v,k) for k,v in self.query_mappings.items()).get(field['name'])
                properties[pname] = {
                    'title': pname
                }
                if field['type'] in type_mappings:
                    properties[pname]['type'] = type_mappings[field['type']]
                    if field['type'] == 'pdate':
                        properties[pname]['fomat'] = 'date-time'

                if pname == 'identifier':
                    properties[pname]['x-ogc-role'] = 'id'

        return properties

    def dataset(self, record):
        """
        Stub to mock a pycsw dataset object for Transactions
        """

        return type('dataset', (object,), record)

    def query_ids(self, ids: list) -> list:
        """
        Query by list of identifiers
        """

        results = []

        all_ids = '" OR "'.join(ids)
        params = {
            'fq': [
                f'metadata_identifier:("{all_ids}")'
            ],
            'q.op': 'OR',
            'q': '*:*'
        }

        if self.adc_collection not in ['', None]:
            params['fq'].append(f'collection:({self.adc_collection})')

        try:
            response = requests.get(self.solr_select_url, params=params,
                                    auth=self.authentication)
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.HTTPError as err:
            msg = f'Solr query error: {err.response.text}'
            LOGGER.error(msg)
            raise RuntimeError(msg)

        for doc in response['response']['docs']:
            results.append(self._doc2record(doc))

        return results

    def query_collections(self, filters=None, limit=10) -> list:
        ''' Query for parent collections '''

        results = []

        params = {
            'fq': ['isChild:false']
        }
        if self.adc_collection not in ['', None]:
            params['fq'].append(f'collection:({self.adc_collection})')

        try:
            response = requests.get(self.solr_select_url, params=params,
                                    auth=self.authentication)
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.HTTPError as err:
            msg = f'Solr query error: {err.response.text}'
            LOGGER.error(msg)
            raise RuntimeError(msg)

        for doc in response['response']['docs']:
            results.append(self._doc2record(doc))

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

        if self.adc_collection not in ['', None]:
            params['fq'].append('collection:({self.adc_collection})')

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

        if self.adc_collection not in ['', None]:
            params['fq'].append('collection:({self.adc_collection})')

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

    def query(self, constraint=None, sortby=None, typenames=None, maxrecords=10,
              startposition=0) -> tuple:
        """
        Query records from underlying repository
        """

        solr_query = {}
        results = []

        if constraint.get('ast') is not None:
            # ask pygeofilter to convert AST to Solr query
            solr_query = to_filter(constraint['ast'])
            if 'csw:AnyText' in solr_query['query']:
                solr_query['query'] = solr_query['query'].replace('csw:AnyText', 'full_text')
            if 'ows:BoundingBox' in solr_query['query']:
                solr_query['query'] = solr_query['query'].replace('ows:BoundingBox', 'bbox')
        else:
            # DO NOT ask pygeofilter to convert AST to Solr query
            solr_query = {'query': '*:*'}

        # add handle sortby, maxrecords, startposition
        solr_query['offset'] = startposition
        solr_query['limit'] = maxrecords

        if sortby is not None:
            solr_query['sort'] = f"{sortby['propertyname']} {sortby['order']}"

        LOGGER.info(f'Solr query: {solr_query}')
        try:
            response = requests.post(f'{self.filter}/select', json=solr_query,
                                     auth=self.authentication)
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.HTTPError as err:
            msg = f'Solr query error: {err.response.text}'
            LOGGER.error(msg)
            raise RuntimeError(msg)

        total = response['response']['numFound']
        LOGGER.debug(f'Found: {total}')
        for doc in response['response']['docs']:
            results.append(self._doc2record(doc))

        return total, results

    def _doc2record(self, doc: dict):
        """
        Transform a Solr doc into a pycsw dataset object
        """

        record = {}

        record['identifier'] = doc['metadata_identifier']
        record['metadata_type'] = 'application/xml'
        record['typename'] = 'gmd:MD_Metadata'
        record['schema'] = 'http://www.isotc211.org/2005/gmd'

        LOGGER.debug('Checking for parent-child relationship')
#        if doc.get('isParent', False):
#            record['type'] = 'series'
#        else:
#            record['type'] = 'dataset'

#        if doc.get('isChild', False):
#            record['parentidentifier'] = doc['related_dataset'][0]

        if 'isParent' in doc and doc["isParent"]:
            record['type'] = "series"
        else:
            record['type'] = "dataset"

        if 'isChild' in doc and doc["isChild"]:
            record['parentidentifier'] = doc["related_dataset"][0]  
        else:
            record['parentidentifier'] = None

        record['wkt_geometry'] = doc['bbox']
        record['title'] = doc['title'][0]
        record['abstract'] = doc['abstract'][0]

        if 'iso_topic_category' in doc:
            record['topicategory'] = ','.join(doc['iso_topic_category'])
        else:
            record['topicategory'] = None

#        if 'keywords_keyword' in doc:
#            record['keywords'] = ','.join(doc['keywords_keyword'])

#        if 'related_url_landing_page' in doc:
#            record['source'] = doc['related_url_landing_page'][0]

        record['source'] = None

        record['language'] = doc.get('dataset_language', 'en')

        # Transform the indexed time as insert_data
        insert = dparser.parse(doc['timestamp'][0])
        record['insert_date'] = insert.isoformat()

        # Transform the last metadata update datetime as modified
        if 'last_metadata_update_datetime' in doc:
            modified = dparser.parse(doc['last_metadata_update_datetime'][0])
            record['date_modified'] = modified.isoformat()

            if 'Created' in doc['last_metadata_update_type']:
                record['date_creation'] = modified.isoformat()
            else:
                record['date_creation'] = None

        # Transform temporal extendt start and end dates
        if 'temporal_extent_start_date' in doc:
            #time_begin = dparser.parse(doc['temporal_extent_start_date'][0])
            #record['time_begin'] = time_begin.isoformat()
            record['time_begin'] = doc['temporal_extent_start_date'][0]

        if 'temporal_extent_end_date' in doc:
            #time_end = dparser.parse(doc['temporal_extent_end_date'][0])
            #record['time_end'] = time_end.isoformat()
            #record['time_end'] = doc['temporal_extent_end_date'][0] 
            record['time_end'] = None
        else:
            record['time_end'] = None

        links = []
        record['relation'] = None

        if 'data_access_url_opendap' in doc:
            links.append(
                {
                    'name': 'OPeNDAP access',
                    'description': 'OPeNDAP access',
                    'protocol': 'OPeNDAP:OPeNDAP',
                    'url': doc['data_access_url_opendap'][0],
                }
            )
        if 'data_access_url_ogc_wms' in doc:
            links.append(
                {
                    'name': 'OGC-WMS Web Map Service',
                    'description': 'OGC-WMS Web Map Service',
                    'protocol': 'OGC:WMS',
                    'url': doc['data_access_url_ogc_wms'][0],
                }
            )
        if 'data_access_url_http' in doc:
            links.append(
                {
                    'name': 'File for download',
                    'description': 'Direct HTTP download',
                    'protocol': 'WWW:DOWNLOAD-1.0-http--download',
                    'url': doc['data_access_url_http'][0],
                }
            )
        if 'data_access_url_ftp' in doc:
            links.append(
                {
                    'name': 'File for download',
                    'description': 'Direct FTP download',
                    'protocol': 'ftp',
                    'url': doc['data_access_url_ftp'][0],
                }
            )
        record['links'] = json.dumps(links)

        # Transform the first investigator as creator.
        if 'personnel_investigator_name' in doc:
            record['creator'] = ','.join(doc['personnel_investigator_name'])

        if 'personnel_technical_name' in doc:
            record['contributor'] = ','.join(doc['personnel_technical_name'])

        if 'personnel_metadata_author_name' in doc:
            if 'contributor' in record:
                record['contributor'] += ',' + ','.join(
                    doc['personnel_metadata_author_name']
                )
            else:
                record['contributor'] = ','.join(doc['personnel_metadata_author_name'])  # noqa

        contacts = []
        for ct in ['technical', 'investigator', 'metadata_author']:
            ct2 = personnel2contact(doc, ct)
            if ct2:
                contacts.append(personnel2contact(doc, ct))

        record['contacts'] = json.dumps(contacts)
        #record['themes'] = keywords2themes(doc)
        record['themes'], record['keywords'] = keywords2themes(doc)

        # TODO: rights is mapped to accessconstraint, although we provide this
        # info in the use constraint.
        # we should use dc:license instead, but it is not mapped in csw.
        if 'use_constraint_license_text' in doc:
            record['otherconstraints'] = doc.get('use_constraint_license_text')
        else:
            record['otherconstraints'] = doc.get('use_constraint_identifier')

        #this is mapped to rights. We do not have it
        record['conditionapplyingtoaccessanduse'] = None

        if 'dataset_citation_publisher' in doc:
            record['publisher'] = doc['dataset_citation_publisher'][0]

        if 'storage_information_file_format' in doc:
            record['format'] = doc['storage_information_file_format']
        else:
            record['format'] = 'Not provided'

#        transform = etree.XSLT(etree.parse(self.mmd_to_iso_xslt))
#        xml_ = base64.b64decode(doc['mmd_xml_file'])
#
#        doc_ = etree.fromstring(xml_, self.context.parser)
#        pl = '/usr/local/share/parent_list.xml'
#        result_tree = transform(
#            doc_, path_to_parent_list=etree.XSLT.strparam(pl)).getroot()
#        record['xml'] = etree.tostring(result_tree)
#        record['mmd_xml_file'] = doc['mmd_xml_file']
#
#        LOGGER.debug(record['xml'])
        params = {
            'q.op': 'OR',
            'q': f"metadata_identifier:{doc['metadata_identifier']}"
        }

        mdsource_url = self.solr_select_url + urlencode(params)
        record['mdsource'] = mdsource_url

        return self.dataset(record)

    def ping(self):
        pass


def keywords2themes(doc: dict) -> list:
    schemes = {}
    themes = []
    kvoctothesaurus = {'GCMDSK' : 'https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/sciencekeywords',
          'CFSTDN' : 'https://vocab.nerc.ac.uk/standard_name/',
          'GEMET' : 'http://inspire.ec.europa.eu/theme',
          'NORTHEMES' : 'https://register.geonorge.no/metadata-kodelister/nasjonal-temainndeling',
          'GCMDPROV': 'https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/providers',
          'GCMDLOC' : 'https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/locations'}
    keywords = ""

    for scheme in set(doc.get('keywords_vocabulary', [])):
        schemes[scheme] = []
        for index, value in enumerate(doc['keywords_keyword']):
            if doc['keywords_vocabulary'][index] == scheme:
                schemes[doc['keywords_vocabulary'][index]].append(value)

    for key, value in schemes.items():
        if key != "None":
            themes.append({
                'keywords': [{'name': v} for v in value],
                #'scheme': key,
                'thesaurus': {'title': key, 'url' : kvoctothesaurus[key]}
            })
        else:
            keywords = ",".join(value)

    return json.dumps(themes), keywords


def personnel2contact(doc: dict, ct: str) -> dict:
    contact = {}

    mmdrole2roles = {'metadata_author': 'Metadata author',
                     'technical' : 'Technical contact',
                     'investigator': 'Investigator'}

    if f'personnel_{ct}_name' in doc:
        contact = {
            'name': doc[f'personnel_{ct}_name'][0],
            'organization': doc[f'personnel_{ct}_organisation'][0],
            'role': mmdrole2roles[f'{ct}'],
            'email': doc[f'personnel_{ct}_email'][0],
        }

    return contact
