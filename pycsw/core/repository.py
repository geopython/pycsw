# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#          Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
# Copyright (c) 2015 Angelos Tzotsos
# Copyright (c) 2017 Ricardo Garcia Silva
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
import logging
import os

import six
from shapely.wkt import loads
from shapely.geos import ReadingError
from sqlalchemy import create_engine, func, __version__, select
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session

from pycsw.core import util
from pycsw.core.etree import etree
from pycsw.core.etree import PARSER

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
            LOGGER.info('creating new engine: %s', url)
            engine = create_engine('%s' % url, echo=False)

            # load SQLite query bindings
            # This can be directly bound via events
            # for sqlite < 0.7, we need to to this on a per-connection basis
            if engine.name in ['sqlite', 'sqlite3'] and __version__ >= '0.7':
                from sqlalchemy import event
                @event.listens_for(engine, "connect")
                def connect(dbapi_connection, connection_rec):
                    create_custom_sql_functions(dbapi_connection)

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

        LOGGER.info('binding ORM to existing database')

        self.postgis_geometry_column = None

        schema_name, table_name = table.rpartition(".")[::2]

        self.dataset = type(
            'dataset',
            (base,),
            {
                "__tablename__": table_name,
                "__table_args__": {
                    "autoload": True,
                    "schema": schema_name or None,
                },
            }
        )

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
                LOGGER.exception('PostgreSQL+PostGIS1+WKT detection failed')

            # check if PostgreSQL is enabled with PostGIS 2.x
            try:
                self.session.execute('select(postgis_version())')
                temp_dbtype = 'postgresql+postgis+wkt'
                LOGGER.debug('PostgreSQL+PostGIS2+WKT detected')
            except Exception as err:
                LOGGER.exception('PostgreSQL+PostGIS2+WKT detection failed')

            # check if a native PostGIS geometry column exists
            try:
                result = self.session.execute(
                    "select f_geometry_column "
                    "from geometry_columns "
                    "where f_table_name = '%s' "
                    "and f_geometry_column != 'wkt_geometry' "
                    "limit 1;" % table_name
                )
                row = result.fetchone()
                self.postgis_geometry_column = str(row['f_geometry_column'])
                temp_dbtype = 'postgresql+postgis+native'
                LOGGER.debug('PostgreSQL+PostGIS+Native detected')
            except Exception as err:
                LOGGER.exception('PostgreSQL+PostGIS+Native not picked up: %s')

            # check if a native PostgreSQL FTS GIN index exists
            result = self.session.execute("select relname from pg_class where relname='fts_gin_idx'").scalar()
            self.fts = bool(result)
            LOGGER.debug('PostgreSQL FTS enabled: %r', self.fts)

        if temp_dbtype is not None:
            LOGGER.debug('%s support detected', temp_dbtype)
            self.dbtype = temp_dbtype

        if self.dbtype in ['sqlite', 'sqlite3']:  # load SQLite query bindings
            # <= 0.6 behaviour
            if not __version__ >= '0.7':
                self.connection = self.engine.raw_connection()
                create_custom_sql_functions(self.connection)

        LOGGER.info('setting repository queryables')
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
            LOGGER.info('Generating property name range values')
            query = self.session.query(func.min(domain_value),
                                       func.max(domain_value))
        else:
            if count:
                LOGGER.info('Generating property name frequency counts')
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
            msg = 'Cannot commit to repository'
            LOGGER.exception(msg)
            raise RuntimeError(msg)

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
                msg = 'Cannot commit to repository'
                LOGGER.exception(msg)
                raise RuntimeError(msg)
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
                msg = 'Cannot commit to repository'
                LOGGER.exception(msg)
                raise RuntimeError(msg)

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
            msg = 'Cannot commit to repository'
            LOGGER.exception(msg)
            raise RuntimeError(msg)

        return rows

    def _get_repo_filter(self, query):
        ''' Apply repository wide side filter / mask query '''
        if self.filter is not None:
            return query.filter(text(self.filter))
        return query


def create_custom_sql_functions(connection):
    """Register custom functions on the database connection."""
    if six.PY2:
        inspect_function = inspect.getargspec
    else:  # python3
        inspect_function = inspect.getfullargspec

    for function_object in [
        query_spatial,
        update_xpath,
        util.get_anytext,
        get_geometry_area,
        get_spatial_overlay_rank
    ]:
        argspec = inspect_function(function_object)
        connection.create_function(
            function_object.__name__,
            len(argspec.args),
            function_object
        )


def query_spatial(bbox_data_wkt, bbox_input_wkt, predicate, distance):
    """Perform spatial query

    Parameters
    ----------
    bbox_data_wkt: str
        Well-Known Text representation of the data being queried
    bbox_input_wkt: str
        Well-Known Text representation of the input being queried
    predicate: str
        Spatial predicate to use in query
    distance: int or float or str
        Distance parameter for when using either of ``beyond`` or ``dwithin``
        predicates.

    Returns
    -------
    str
        Either ``true`` or ``false`` depending on the result of the spatial
        query

    Raises
    ------
    RuntimeError
        If an invalid predicate is used

    """

    try:
        bbox1 = loads(bbox_data_wkt.split(';')[-1])
        bbox2 = loads(bbox_input_wkt)
        if predicate == 'bbox':
            result = bbox1.intersects(bbox2)
        elif predicate == 'beyond':
            result = bbox1.distance(bbox2) > float(distance)
        elif predicate == 'contains':
            result = bbox1.contains(bbox2)
        elif predicate == 'crosses':
            result = bbox1.crosses(bbox2)
        elif predicate == 'disjoint':
            result = bbox1.disjoint(bbox2)
        elif predicate == 'dwithin':
            result = bbox1.distance(bbox2) <= float(distance)
        elif predicate == 'equals':
            result = bbox1.equals(bbox2)
        elif predicate == 'intersects':
            result = bbox1.intersects(bbox2)
        elif predicate == 'overlaps':
            result = bbox1.intersects(bbox2) and not bbox1.touches(bbox2)
        elif predicate == 'touches':
            result = bbox1.touches(bbox2)
        elif predicate == 'within':
            result = bbox1.within(bbox2)
        else:
            raise RuntimeError(
                'Invalid spatial query predicate: %s' % predicate)
    except (AttributeError, ValueError, ReadingError):
        result = False
    return "true" if result else "false"


def update_xpath(nsmap, xml, recprop):
    """Update XML document XPath values"""

    if isinstance(xml, six.binary_type) or isinstance(xml, six.text_type):
        # serialize to lxml
        xml = etree.fromstring(xml, PARSER)

    recprop = eval(recprop)
    nsmap = eval(nsmap)
    try:
        nodes = xml.xpath(recprop['rp']['xpath'], namespaces=nsmap)
        if len(nodes) > 0:  # matches
            for node1 in nodes:
                if node1.text != recprop['value']:  # values differ, update
                    node1.text = recprop['value']
    except Exception as err:
        print(err)
        raise RuntimeError('ERROR: %s' % str(err))

    return etree.tostring(xml)


def get_geometry_area(geometry):
    """Derive area of a given geometry"""
    try:
        if geometry is not None:
            return str(loads(geometry).area)
        return '0'
    except:
        return '0'


def get_spatial_overlay_rank(target_geometry, query_geometry):
    """Derive spatial overlay rank for geospatial search as per Lanfear (2006)
    http://pubs.usgs.gov/of/2006/1279/2006-1279.pdf"""

    #TODO: Add those parameters to config file
    kt = 1.0
    kq = 1.0
    if target_geometry is not None and query_geometry is not None:
        try:
            q_geom = loads(query_geometry)
            t_geom = loads(target_geometry)
            Q = q_geom.area
            T = t_geom.area
            if any(item == 0.0 for item in [Q, T]):
                LOGGER.warning('Geometry has no area')
                return '0'
            X = t_geom.intersection(q_geom).area
            if kt == 1.0 and kq == 1.0:
                LOGGER.debug('Spatial Rank: %s', str((X/Q)*(X/T)))
                return str((X/Q)*(X/T))
            else:
                LOGGER.debug('Spatial Rank: %s', str(((X/Q)**kq)*((X/T)**kt)))
                return str(((X/Q)**kq)*((X/T)**kt))
        except Exception as err:
            LOGGER.warning('Cannot derive spatial overlay ranking %s', err)
            return '0'
    return '0'

