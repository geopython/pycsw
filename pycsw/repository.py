# -*- coding: iso-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2010 Tom Kralidis
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

import os
from sqlalchemy import create_engine, asc, desc, func, __version__, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session
import util

class Repository(object):
    ''' Class to interact with underlying repository '''
    def __init__(self, database, context, app_root=None, table='records'):
        ''' Initialize repository '''

        self.context = context

        # Don't use relative paths, this is hack to get around
        # most wsgi restriction...
        if (app_root and database.startswith('sqlite:///') and
            not database.startswith('sqlite:////')):
            database = database.replace('sqlite:///',
                       'sqlite:///%s%s' % (app_root, os.sep))

        engine = create_engine('%s' % database, echo=False)

        base = declarative_base(bind=engine)

        self.dataset = type('dataset', (base,),
        dict(__tablename__=table,__table_args__={'autoload': True}))

        self.dbtype = engine.name

        self.session = create_session(engine)

        # check if PostgreSQL is enabled with PostGIS
        if self.dbtype == 'postgresql':
            try:
                self.session.execute(select([func.postgis_version()]))
                self.dbtype = 'postgresql+postgis'
            except:
                pass

        if self.dbtype in ['sqlite', 'sqlite3']:  # load SQLite query bindings
            if __version__ >= '0.7':
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
            else:  # <= 0.6 behaviour
                self.connection = engine.raw_connection()
                self.connection.create_function(
                'query_spatial', 4, util.query_spatial)
                self.connection.create_function(
                'update_xpath', 3, util.update_xpath)
                self.connection.create_function('get_anytext', 1,
                util.get_anytext)
                self.connection.create_function('get_geometry_area', 1,
                util.get_geometry_area)

        # generate core queryables db and obj bindings
        self.queryables = {}

        for tname in self.context.model['typenames']:
            for qname in self.context.model['typenames'][tname]['queryables']:
                self.queryables[qname] = {}

                for qkey, qvalue in \
                self.context.model['typenames'][tname]['queryables'][qname].iteritems():
                    self.queryables[qname][qkey] = qvalue

        # flatten all queryables
        # TODO smarter way of doing this
        self.queryables['_all'] = {}
        for qbl in self.queryables:
            self.queryables['_all'].update(self.queryables[qbl])

        self.queryables['_all'].update(self.context.md_core_model['mappings'])

    def query_ids(self, ids):
        ''' Query by list of identifiers '''
        column = getattr(self.dataset, \
        self.context.md_core_model['mappings']['pycsw:Identifier'])

        query = self.session.query(
        self.dataset).filter(column.in_(ids))
        return query.all()

    def query_domain(self, domain, typenames, domainquerytype='list',
        count=False):
        ''' Query by property domain values '''

        if domainquerytype == 'range':
            query = self.session.query(
            func.min(getattr(self.dataset, domain)),
            func.max(getattr(self.dataset, domain)))
        else:
            if count is True:
                query = self.session.query(getattr(self.dataset, domain),
                func.count(getattr(self.dataset, domain))).group_by(
                getattr(self.dataset, domain))
            else:
                query = self.session.query(
                getattr(self.dataset, domain)).distinct()
        return query.all()

    def query_latest_insert(self):
        ''' Query to get latest update to repository '''
        column = getattr(self.dataset, \
        self.context.md_core_model['mappings']['pycsw:InsertDate'])

        return self.session.query(
        func.max(column)).first()[0]

    def query_source(self, source):
        ''' Query by source '''
        column = getattr(self.dataset, \
        self.context.md_core_model['mappings']['pycsw:Source'])

        query = self.session.query(self.dataset).filter(
        column == source)
        return query.all() 

    def query(self, constraint, sortby=None, typenames=None,
        maxrecords=10, startposition=0):
        ''' Query records from underlying repository '''

        typename_column = getattr(self.dataset, \
        self.context.md_core_model['mappings']['pycsw:Typename'])

        # run the raw query and get total
        if constraint.has_key('where'):  # GetRecords with constraint
            if not typenames:  # any typename
                query = self.session.query(self.dataset).filter(
                constraint['where'])
            else:
                query = self.session.query(self.dataset).filter(
                typename_column.in_(typenames)).filter(
                constraint['where'])

            total = query.count()

        else:  # GetRecords sans constraint
            if not typenames:  # any typename
                query = self.session.query(self.dataset)
            else:
                query = self.session.query(self.dataset).filter(
                typename_column.in_(typenames))

            total = query.count()

        if sortby is not None:  # apply sorting
            sortby_column = getattr(self.dataset, sortby['propertyname'])

            if sortby['order'] == 'DESC':  # descending sort
                if sortby.has_key('spatial') and sortby['spatial'] is True:  # spatial sort
                    query = query.order_by(func.get_geometry_area(sortby_column).desc())
                else:  # aspatial sort
                    query = query.order_by(sortby_column.desc())
            else:  # ascending sort
                if sortby.has_key('spatial') and sortby['spatial'] is True:  # spatial sort
                    query = query.order_by(func.get_geometry_area(sortby_column))
                else:  # aspatial sort
                    query = query.order_by(sortby_column)

        # always apply limit and offset
        return [str(total), query.limit(
        maxrecords).offset(startposition).all()]

    def insert(self, record, source, insert_date):
        ''' Insert a record into the repository '''

        try:
            self.session.begin()
            self.session.add(record)
            self.session.commit()
        except Exception, err:
            self.session.rollback()
            raise RuntimeError, 'ERROR: %s' % str(err)

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

            update_dict = dict([(getattr(self.dataset, key),
            getattr(record, key)) \
            for key in record.__dict__.keys() if key != '_sa_instance_state'])

            try:
                self.session.begin()
                self.session.query(self.dataset).filter_by(
                identifier=identifier).update(update_dict)
                self.session.commit()
            except Exception, err:
                self.session.rollback()
                raise RuntimeError, 'ERROR: %s' % str(err)
        else:  # update based on record properties
            try:
                rows = rows2 = 0
                self.session.begin()
                for rpu in recprops:
                    # update queryable column and XML document via XPath
                    rows += self.session.query(self.dataset).filter(
                        constraint['where']).update({
                            getattr(self.dataset,
                            rpu['rp']['dbcol']): rpu['value'],
                            'xml': func.update_xpath(str(self.context.namespaces),
                                   getattr(self.dataset,
                                   self.context.md_core_model['mappings']['pycsw:XML']),
                                   str(rpu)),
                        }, synchronize_session='fetch')
                    # then update anytext tokens
                    rows2 += self.session.query(self.dataset).filter(
                        constraint['where']).update({
                            'anytext': func.get_anytext(getattr(
                            self.dataset, self.context.md_core_model['mappings']['pycsw:XML']))
                        }, synchronize_session='fetch')
                self.session.commit()
                return rows
            except Exception, err:
                self.session.rollback()
                raise RuntimeError, 'ERROR: %s' % str(err)

    def delete(self, constraint):
        ''' Delete a record from the repository '''

        try:
            self.session.begin()
            rows = self.session.query(self.dataset).filter(
            constraint['where'])

            parentids = []
            for row in rows:  # get ids
                parentids.append(getattr(row,
                self.context.md_core_model['mappings']['pycsw:Identifier']))

            rows=rows.delete(synchronize_session='fetch')

            if rows > 0:
                # delete any child records which had this record as a parent
                rows += self.session.query(self.dataset).filter(
                    getattr(self.dataset,
                    self.context.md_core_model['mappings']['pycsw:ParentIdentifier']).in_(parentids)).delete(
                    synchronize_session='fetch')

            self.session.commit()
        except Exception, err:
            self.session.rollback()
            raise RuntimeError, 'ERROR: %s' % str(err)

        return rows
