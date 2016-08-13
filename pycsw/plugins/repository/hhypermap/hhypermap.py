# -*- coding: iso-8859-15 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2016 Tom Kralidis
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

import inspect

from django.db import models
from django.db import connection
from django.db.models import Avg, Max, Min, Count
from django.conf import settings

from pycsw.core import util
from hypermap.aggregator.models import Layer, Service, Endpoint
from hypermap.aggregator.utils import create_layer_from_metadata_xml

HYPERMAP_SERVICE_TYPES = {
    # 'HHypermap enum': 'CSW enum'
    'http://www.opengis.net/cat/csw/2.0.2': 'OGC:CSW',
    'http://www.opengis.net/wms': 'OGC:WMS',
    'http://www.opengis.net/wmts/1.0': 'OGC:WMTS',
    'https://wiki.osgeo.org/wiki/TMS': 'OSGeo:TMS',
    'urn:x-esri:serviceType:ArcGIS:MapServer': 'ESRI:ArcGIS:MapServer',
    'urn:x-esri:serviceType:ArcGIS:ImageServer': 'ESRI:ArcGIS:ImageServer'
}

class HHypermapRepository(object):
    ''' Class to interact with underlying repository '''
    def __init__(self, context, repo_filter=None):
        ''' Initialize repository '''

        self.context = context
        self.filter = repo_filter
        self.fts = False
        self.label = 'HHypermap'
        self.local_ingest = True

        self.dbtype = settings.DATABASES['default']['ENGINE'].split('.')[-1]

        # HHypermap PostgreSQL installs are PostGIS enabled
        if self.dbtype == 'postgresql_psycopg2':
            self.dbtype = 'postgresql+postgis+wkt'

        if self.dbtype in ['sqlite', 'sqlite3']:  # load SQLite query bindings
            cursor = connection.cursor()
            connection.connection.create_function(
            'query_spatial', 4, util.query_spatial)
            connection.connection.create_function(
            'get_anytext', 1, util.get_anytext)
            connection.connection.create_function(
            'get_geometry_area', 1, util.get_geometry_area)

        # generate core queryables db and obj bindings
        self.queryables = {}

        for tname in self.context.model['typenames']:
            for qname in self.context.model['typenames'][tname]['queryables']:
                self.queryables[qname] = {}

                for qkey, qvalue in \
                self.context.model['typenames'][tname]['queryables'][qname].items():
                    self.queryables[qname][qkey] = qvalue

        # flatten all queryables
        # TODO smarter way of doing this
        self.queryables['_all'] = {}
        for qbl in self.queryables:
            self.queryables['_all'].update(self.queryables[qbl])
        self.queryables['_all'].update(self.context.md_core_model['mappings'])

        if 'Harvest' in self.context.model['operations'] and 'Transaction' in self.context.model['operations']:
            self.context.model['operations']['Harvest']['parameters']['ResourceType']['values'] = HYPERMAP_SERVICE_TYPES.keys()
            self.context.model['operations']['Transaction']['parameters']['TransactionSchemas']['values'] = HYPERMAP_SERVICE_TYPES.keys()

    def dataset(self):
        ''' Stub to mock a pycsw dataset object for Transactions'''
        return type('Service', (object,), {})

    def query_ids(self, ids):
        ''' Query by list of identifiers '''
        return self._get_repo_filter(Layer.objects).filter(id__in=ids).all()

    def query_domain(self, domain, typenames, domainquerytype='list',
        count=False):
        ''' Query by property domain values '''

        objects = self._get_repo_filter(Layer.objects)

        if domainquerytype == 'range':
            return [tuple(objects.aggregate(
            Min(domain), Max(domain)).values())]
        else:
            if count:
                return [(d[domain], d['%s__count' % domain]) \
                for d in objects.values(domain).annotate(Count(domain))]
            else:
                return objects.values_list(domain).distinct()

    def query_insert(self, direction='max'):
        ''' Query to get latest (default) or earliest update to repository '''
        from datetime import datetime
        if direction=='min':
            return Layer.objects.aggregate(
                Min('last_updated'))['last_updated__min'].strftime('%Y-%m-%dT%H:%M:%SZ')
        return self._get_repo_filter(Layer.objects).aggregate(
            Max('last_updated'))['last_updated__max'].strftime('%Y-%m-%dT%H:%M:%SZ')

    def query_source(self, source):
        ''' Query by source '''
        return self._get_repo_filter(Layer.objects).filter(url=source)

    def query(self, constraint, sortby=None, typenames=None,
        maxrecords=10, startposition=0):
        ''' Query records from underlying repository '''

        # run the raw query and get total
        if 'where' in constraint:  # GetRecords with constraint
            query = self._get_repo_filter(Layer.objects).extra(where=[constraint['where']], params=constraint['values'])

        else:  # GetRecords sans constraint
            query = self._get_repo_filter(Layer.objects)

        total = query.count()

        # apply sorting, limit and offset
        if sortby is not None:
            if 'spatial' in sortby and sortby['spatial']:  # spatial sort
                desc = False
                if sortby['order'] == 'DESC':
                    desc = True
                query = query.all()
                return [str(total), sorted(query, key=lambda x: float(util.get_geometry_area(getattr(x, sortby['propertyname']))), reverse=desc)[startposition:startposition+int(maxrecords)]]
            else:
                if sortby['order'] == 'DESC':
                    pname = '-%s' % sortby['propertyname']
                else:
                    pname = sortby['propertyname']
                return [str(total), \
                query.order_by(pname)[startposition:startposition+int(maxrecords)]]
        else:  # no sort
            return [str(total), query.all()[startposition:startposition+int(maxrecords)]]

    def insert(self, resourcetype, source, insert_date=None):
        ''' Insert a record into the repository '''

        caller = inspect.stack()[1][3]

        if caller == 'transaction':  # insert of Layer
            hhclass = 'Layer'
            source = resourcetype
            resourcetype = resourcetype.csw_schema
        else:  # insert of service
            hhclass = 'Service'
            if resourcetype not in HYPERMAP_SERVICE_TYPES.keys():
                raise RuntimeError('Unsupported Service Type')

        return self._insert_or_update(resourcetype, source, mode='insert', hhclass=hhclass)

    def _insert_or_update(self, resourcetype, source, mode='insert', hhclass='Service'):
        ''' Insert or update a record in the repository '''

        keywords = []
        try:
            if hhclass == 'Layer':
                # TODO: better way of figuring out duplicates
                match = Layer.objects.filter(name=source.title, title=source.title, abstract=source.abstract, is_monitored=False)
                matches = match.all()
                if matches:
                    if mode == 'insert':
                        raise RuntimeError('HHypermap error: Layer %d \'%s\' already exists' % (matches[0].id, source.title))
                    elif mode == 'update':
                        match.update(
                            name=source.title,
                            title=source.title,
                            abstract=source.abstract,
                            is_monitored=False,
                            xml=source.xml,
                            wkt_geometry=source.wkt_geometry,
                            anytext=util.get_anytext([source.title, source.abstract, source.keywords_csv])
                        )

                res, keywords = create_layer_from_metadata_xml(resourcetype, source.xml, monitor=False)
            else:
                if resourcetype == 'http://www.opengis.net/cat/csw/2.0.2':
                    res = Endpoint(url=source)
                else:
                    res = Service(type=HYPERMAP_SERVICE_TYPES[resourcetype], url=source)
            res.save()
            if keywords:
                for kw in keywords:
                    res.keywords.add(kw)
        except Exception as err:
           raise RuntimeError('HHypermap error: %s' % err)

        # return a list of ids that were inserted or updated
        ids = []

        if hhclass == 'Layer':
            ids.append({'identifier': res.id_string, 'title': res.title })
        else:
            if resourcetype == 'http://www.opengis.net/cat/csw/2.0.2':
                for res in Endpoint.objects.filter(url=source).all():
                    ids.append({'identifier': res.id_string, 'title': res.url})
            else:
                for res in Service.objects.filter(url=source).all():
                    ids.append({'identifier': res.id_string, 'title': res.title})

        return ids
        
    def delete(self, constraint):
        ''' Delete a record from the repository '''

        # FIXME: id_string is a virtual property and cannot be queried against
        constraint['where'] = constraint['where'].replace('id_string', 'id')

        results = self._get_repo_filter(Service.objects).extra(where=[constraint['where']],
                                                               params=constraint['values']).all()
        deleted = len(results)
        results.delete()
        return deleted

    def _get_repo_filter(self, query):
        ''' Apply repository wide side filter / mask query '''
        if self.filter is not None:
            return query.extra(where=[self.filter])
        return query
