# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
# Copyright (c) 2015 Angelos Tzotsos
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
import os
from sqlalchemy import create_engine, asc, desc, func, __version__, select
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session
from pycsw.core import util

LOGGER = logging.getLogger(__name__)

class Repository(object):
    _engines = {}

    @classmethod
    def create_engine(clazz, url):
        '''
        SQL Alchemy engines are thread-safe and simple wrappers for connection pools

        https://groups.google.com/forum/#!topic/sqlalchemy/t8i3RSKZGb0

        To reduce startup time we can cache the engine as a class variable in the
        repository object and do database initialization once

        Engines are memoized by url
        '''
        if url not in clazz._engines:
            LOGGER.debug('creating new engine: %s', url)
            engine = create_engine('%s' % url, echo=False)

            # load SQLite query bindings
            # This can be directly bound via events
            # for sqlite < 0.7, we need to to this on a per-connection basis
            if engine.name in ['sqlite', 'sqlite3'] and __version__ >= '0.7':
                from sqlalchemy import event
                @event.listens_for(engine, "connect")
                def connect(dbapi_connection, connection_rec):
                    dbapi_connection.create_function(
                    'query_spatial', 4, util.query_spatial)
                    dbapi_connection.create_function(
                    'update_xpath', 3, util.update_xpath)
                    dbapi_connection.create_function('get_anytext', 1,
                    util.get_anytext)
                    dbapi_connection.create_function('get_geometry_area', 1,
                    util.get_geometry_area)
                    dbapi_connection.create_function('get_spatial_overlay_rank', 2,
                    util.get_spatial_overlay_rank)

            clazz._engines[url] = engine

        return clazz._engines[url]

    ''' Class to interact with underlying repository '''
    def __init__(self, database, context, app_root=None, table='records', repo_filter=None):
        ''' Initialize repository '''

        self.context = context
        self.filter = repo_filter
        self.fts = False

        # Don't use relative paths, this is hack to get around
        # most wsgi restriction...
        if (app_root and database.startswith('sqlite:///') and
            not database.startswith('sqlite:////')):
            database = database.replace('sqlite:///',
                       'sqlite:///%s%s' % (app_root, os.sep))

        self.engine = Repository.create_engine('%s' % database)

        base = declarative_base(bind=self.engine)

        LOGGER.debug('binding ORM to existing database')

        self.postgis_geometry_column = None

        schema, table = util.sniff_table(table)

        self.dataset = type('dataset', (base,),
        dict(__tablename__=table,__table_args__={'autoload': True,
                                                 'schema': schema}))

        self.dbtype = self.engine.name

        self.session = create_session(self.engine)

        temp_dbtype = None

        if self.dbtype == 'postgresql':
            # check if PostgreSQL is enabled with PostGIS 1.x
            try:
                self.session.execute(select([func.postgis_version()]))
                temp_dbtype = 'postgresql+postgis+wkt'
                LOGGER.debug('PostgreSQL+PostGIS1+WKT detected')
            except Exception as err:
                LOGGER.debug('PostgreSQL+PostGIS1+WKT detection failed')

            # check if PostgreSQL is enabled with PostGIS 2.x
            try:
                self.session.execute('select(postgis_version())')
                temp_dbtype = 'postgresql+postgis+wkt'
                LOGGER.debug('PostgreSQL+PostGIS2+WKT detected')
            except Exception as err:
                LOGGER.debug('PostgreSQL+PostGIS2+WKT detection failed')

            # check if a native PostGIS geometry column exists
            try:
                result = self.session.execute("select f_geometry_column from geometry_columns where f_table_name = '%s' and f_geometry_column != 'wkt_geometry' limit 1;" % table)
                row = result.fetchone()
                self.postgis_geometry_column = str(row['f_geometry_column'])
                temp_dbtype = 'postgresql+postgis+native'
                LOGGER.debug('PostgreSQL+PostGIS+Native detected')
            except Exception as err:
                LOGGER.debug('PostgreSQL+PostGIS+Native not picked up: %s', str(err))

            # check if a native PostgreSQL FTS GIN index exists
            result = self.session.execute("select relname from pg_class where relname='fts_gin_idx'").scalar()
            self.fts = bool(result)
            LOGGER.debug('PostgreSQL FTS enabled: %r', self.fts)

        if temp_dbtype is not None:
            LOGGER.debug('%s support detected' % temp_dbtype)
            self.dbtype = temp_dbtype

        if self.dbtype in ['sqlite', 'sqlite3']:  # load SQLite query bindings
            # <= 0.6 behaviour
            if not __version__ >= '0.7':
                self.connection = self.engine.raw_connection()
                self.connection.create_function(
                'query_spatial', 4, util.query_spatial)
                self.connection.create_function(
                'update_xpath', 3, util.update_xpath)
                self.connection.create_function('get_anytext', 1,
                util.get_anytext)
                self.connection.create_function('get_geometry_area', 1,
                util.get_geometry_area)
                self.connection.create_function('get_spatial_overlay_rank', 2,
                util.get_spatial_overlay_rank)

        LOGGER.debug('setting repository queryables')
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

    def _create_values(self, values):
        value_dict = {}
        for num, value in enumerate(values):
            value_dict['pvalue%d' % num] = value
        return value_dict

    def query_ids(self, ids):
        ''' Query by list of identifiers '''

        column = getattr(self.dataset, \
        self.context.md_core_model['mappings']['pycsw:Identifier'])

        query = self.session.query(self.dataset).filter(column.in_(ids))
        return self._get_repo_filter(query).all()

    def query_domain(self, domain, typenames, domainquerytype='list',
        count=False):
        ''' Query by property domain values '''

        domain_value = getattr(self.dataset, domain)

        if domainquerytype == 'range':
            LOGGER.debug('Generating property name range values')
            query = self.session.query(func.min(domain_value),
                                       func.max(domain_value))
        else:
            if count:
                LOGGER.debug('Generating property name frequency counts')
                query = self.session.query(getattr(self.dataset, domain),
                    func.count(domain_value)).group_by(domain_value)
            else:
                query = self.session.query(domain_value).distinct()
        return self._get_repo_filter(query).all()

    def query_insert(self, direction='max'):
        ''' Query to get latest (default) or earliest update to repository '''
        column = getattr(self.dataset, \
        self.context.md_core_model['mappings']['pycsw:InsertDate'])

        if direction == 'min':
            return self._get_repo_filter(self.session.query(func.min(column))).first()[0]
        # else default max
        return self._get_repo_filter(self.session.query(func.max(column))).first()[0]

    def query_source(self, source):
        ''' Query by source '''
        column = getattr(self.dataset, \
        self.context.md_core_model['mappings']['pycsw:Source'])

        query = self.session.query(self.dataset).filter(column == source)
        return self._get_repo_filter(query).all()

    def query(self, constraint, sortby=None, typenames=None,
        maxrecords=10, startposition=0):
        ''' Query records from underlying repository '''

        # run the raw query and get total
        if 'where' in constraint:  # GetRecords with constraint
            LOGGER.debug('constraint detected')
            query = self.session.query(self.dataset).filter(
            text(constraint['where'])).params(self._create_values(constraint['values']))
        else:  # GetRecords sans constraint
            LOGGER.debug('No constraint detected')
            query = self.session.query(self.dataset)

        total = self._get_repo_filter(query).count()

        if util.ranking_pass:  #apply spatial ranking
            #TODO: Check here for dbtype so to extract wkt from postgis native to wkt
            LOGGER.debug('spatial ranking detected')
            LOGGER.debug('Target WKT: %s', getattr(self.dataset, self.context.md_core_model['mappings']['pycsw:BoundingBox']))
            LOGGER.debug('Query WKT: %s', util.ranking_query_geometry)
            query = query.order_by(func.get_spatial_overlay_rank(getattr(self.dataset, self.context.md_core_model['mappings']['pycsw:BoundingBox']), util.ranking_query_geometry).desc())
            #trying to make this wsgi safe
            util.ranking_pass = False
            util.ranking_query_geometry = ''

        if sortby is not None:  # apply sorting
            LOGGER.debug('sorting detected')
            #TODO: Check here for dbtype so to extract wkt from postgis native to wkt
            sortby_column = getattr(self.dataset, sortby['propertyname'])

            if sortby['order'] == 'DESC':  # descending sort
                if 'spatial' in sortby and sortby['spatial']:  # spatial sort
                    query = query.order_by(func.get_geometry_area(sortby_column).desc())
                else:  # aspatial sort
                    query = query.order_by(sortby_column.desc())
            else:  # ascending sort
                if 'spatial' in sortby and sortby['spatial']:  # spatial sort
                    query = query.order_by(func.get_geometry_area(sortby_column))
                else:  # aspatial sort
                    query = query.order_by(sortby_column)

        # always apply limit and offset
        return [str(total), self._get_repo_filter(query).limit(
        maxrecords).offset(startposition).all()]

    def insert(self, record, source, insert_date):
        ''' Insert a record into the repository '''

        try:
            self.session.begin()
            self.session.add(record)
            self.session.commit()
        except Exception as err:
            self.session.rollback()
            raise RuntimeError('ERROR: %s' % str(err.orig))

    def update(self, record=None, recprops=None, constraint=None):
        ''' Update a record in the repository based on identifier '''

        if record is not None:
            identifier = getattr(record,
            self.context.md_core_model['mappings']['pycsw:Identifier'])
            xml = getattr(self.dataset,
            self.context.md_core_model['mappings']['pycsw:XML'])
            anytext = getattr(self.dataset,
            self.context.md_core_model['mappings']['pycsw:AnyText'])

        if recprops is None and constraint is None:  # full update
            LOGGER.debug('full update')
            update_dict = dict([(getattr(self.dataset, key),
            getattr(record, key)) \
            for key in record.__dict__.keys() if key != '_sa_instance_state'])

            try:
                self.session.begin()
                self._get_repo_filter(self.session.query(self.dataset)).filter_by(
                identifier=identifier).update(update_dict, synchronize_session='fetch')
                self.session.commit()
            except Exception as err:
                self.session.rollback()
                raise RuntimeError('ERROR: %s' % str(err.orig))
        else:  # update based on record properties
            LOGGER.debug('property based update')
            try:
                rows = rows2 = 0
                self.session.begin()
                for rpu in recprops:
                    # update queryable column and XML document via XPath
                    if 'xpath' not in rpu['rp']:
                        self.session.rollback()
                        raise RuntimeError('XPath not found for property %s' % rpu['rp']['name'])
                    if 'dbcol' not in rpu['rp']:
                        self.session.rollback()
                        raise RuntimeError('property not found for XPath %s' % rpu['rp']['name'])
                    rows += self._get_repo_filter(self.session.query(self.dataset)).filter(
                        text(constraint['where'])).params(self._create_values(constraint['values'])).update({
                            getattr(self.dataset,
                            rpu['rp']['dbcol']): rpu['value'],
                            'xml': func.update_xpath(str(self.context.namespaces),
                                   getattr(self.dataset,
                                   self.context.md_core_model['mappings']['pycsw:XML']),
                                   str(rpu)),
                        }, synchronize_session='fetch')
                    # then update anytext tokens
                    rows2 += self._get_repo_filter(self.session.query(self.dataset)).filter(
                        text(constraint['where'])).params(self._create_values(constraint['values'])).update({
                            'anytext': func.get_anytext(getattr(
                            self.dataset, self.context.md_core_model['mappings']['pycsw:XML']))
                        }, synchronize_session='fetch')
                self.session.commit()
                return rows
            except Exception as err:
                self.session.rollback()
                raise RuntimeError('ERROR: %s' % str(err.orig))

    def delete(self, constraint):
        ''' Delete a record from the repository '''

        try:
            self.session.begin()
            rows = self._get_repo_filter(self.session.query(self.dataset)).filter(
            text(constraint['where'])).params(self._create_values(constraint['values']))

            parentids = []
            for row in rows:  # get ids
                parentids.append(getattr(row,
                self.context.md_core_model['mappings']['pycsw:Identifier']))

            rows=rows.delete(synchronize_session='fetch')

            if rows > 0:
                LOGGER.debug('Deleting all child records')
                # delete any child records which had this record as a parent
                rows += self._get_repo_filter(self.session.query(self.dataset)).filter(
                    getattr(self.dataset,
                    self.context.md_core_model['mappings']['pycsw:ParentIdentifier']).in_(parentids)).delete(
                    synchronize_session='fetch')

            self.session.commit()
        except Exception as err:
            self.session.rollback()
            raise RuntimeError('ERROR: %s' % str(err.orig))

        return rows

    def _get_repo_filter(self, query):
        ''' Apply repository wide side filter / mask query '''
        if self.filter is not None:
            return query.filter(text(self.filter))
        return query
