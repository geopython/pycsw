# -*- coding: ISO-8859-15 -*-
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

from sqlalchemy import create_engine, desc, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session
import util

class Repository(object):
    ''' Class to interact with underlying repository '''
    def __init__(self, database, table, config):
        ''' Initialize repository '''

        engine = create_engine('%s' % database, echo=False)

        base = declarative_base(bind=engine)

        self.dataset = type('dataset', (base,),
        dict(__tablename__=table,__table_args__={'autoload': True}))

        self.dbtype = engine.name

        self.session = create_session(engine)

        if self.dbtype == 'sqlite':  # load SQLite query bindings
            self.connection = engine.raw_connection()
            self.connection.create_function('query_spatial', 4, util.query_spatial)
            self.connection.create_function('update_xpath', 2, util.update_xpath)

        # generate core queryables db and obj bindings
        self.queryables = {}       

        for tname in config:
            for qname in config[tname]['queryables']:
                self.queryables[qname] = {}

                for qkey, qvalue in \
                config[tname]['queryables'][qname].iteritems():
                    self.queryables[qname][qkey] = qvalue

        # flatten all queryables
        # TODO smarter way of doing this
        self.queryables['_all'] = {}
        for qbl in self.queryables:
            self.queryables['_all'].update(self.queryables[qbl])

    def query_ids(self, ids):
        ''' Query by list of identifiers '''
        query = self.session.query(
        self.dataset).filter(self.dataset.identifier.in_(ids))
        return query.all()

    def query_domain(self, domain, typenames):
        ''' Query by property domain values '''
        query = self.session.query(getattr(self.dataset, domain)).distinct()
        return query.all()

    def query_latest_insert(self):
        ''' Query to get latest update to repository '''
        return self.session.query(
        func.max(self.dataset.insert_date)).first()[0]

    def query_source(self, source):
        ''' Query by source '''
        query = self.session.query(self.dataset).filter(
        self.dataset.source == source)
        return query.all() 

    def query(self, constraint, sortby=None, typenames=[],
        maxrecords=10, startposition=0):
        ''' Query records from underlying repository '''

        # run the raw query and get total
        if constraint.has_key('where'):  # GetRecords with constraint
            if not typenames:  # any typename
                query = self.session.query(self.dataset).filter(
                constraint['where'])
            else:
                query = self.session.query(self.dataset).filter(
                self.dataset.typename.in_(typenames)).filter(
                constraint['where'])

            total = query.count()

        elif constraint.has_key('where') is False: # GetRecords sans constraint
            if not typenames:  # any typename
                query = self.session.query(self.dataset)
            else:
                query = self.session.query(self.dataset).filter(
                self.dataset.typename.in_(typenames))

            total = query.count()

        # apply sorting, limit and offset
        if sortby is not None:
            if sortby['order'] == 'DESC':
                return [str(total), query.order_by(desc(sortby['propertyname'])).limit(maxrecords).offset(startposition).all()]
            else: 
                return [str(total), query.order_by(sortby['propertyname']).limit(maxrecords).offset(startposition).all()]
        else:  # no sort
            return [str(total), query.limit(maxrecords).offset(startposition).all()]

    def insert(self, record, source, insert_date):
        ''' Insert a record into the repository '''

        record1 = self.dataset(
        typename = record['typename'],
        schema = record['schema'],
        anytext = record['anytext'],
        identifier = record['identifier'],
        title = record['properties'].title,
        creator = record['properties'].creator,
        keywords = ','.join(record['properties'].subjects),
        abstract = record['properties'].abstract,
        publisher = record['properties'].publisher,
        contributor = record['properties'].contributor,
        date_modified = record['properties'].modified,
        date = record['properties'].date,
        type = record['properties'].type,
        format = record['properties'].format,
        source = record['properties'].source,
        language = record['properties'].language,
        relation = record['properties'].relation,
        accessconstraints = ','.join(record['properties'].rights),
        geometry = record['geometry'],
        xml = record['xml'],
        mdsource = source,
        insert_date = insert_date)

        try:
            self.session.begin()
            self.session.add(record1)
            self.session.commit()
        except Exception, err:
            self.session.rollback()
            raise RuntimeError, 'ERROR: %s' % str(err)

    def update(self, record=None, recprops=None, constraint=None):
        ''' Update a record in the repository based on identifier '''

        if recprops is None and constraint is None:  # full update
            try:
                self.session.begin()
                self.session.query(self.dataset).filter_by(
                identifier=record['identifier']).update({
                self.dataset.typename: record['typename'],
                self.dataset.schema: record['schema'],
                self.dataset.anytext: record['anytext'],
                self.dataset.identifier: record['identifier'],
                self.dataset.title: record['properties'].title,
                self.dataset.creator: record['properties'].creator,
                self.dataset.keywords: ','.join(record['properties'].subjects),
                self.dataset.abstract: record['properties'].abstract,
                self.dataset.publisher: record['properties'].publisher,
                self.dataset.contributor: record['properties'].contributor,
                self.dataset.date_modified: record['properties'].modified,
                self.dataset.date: record['properties'].date,
                self.dataset.type: record['properties'].type,
                self.dataset.format: record['properties'].format,
                self.dataset.source: record['properties'].source,
                self.dataset.language: record['properties'].language,
                self.dataset.relation: record['properties'].relation,
                self.dataset.accessconstraints: ','.join(record['properties'].rights),
                self.dataset.geometry: record['geometry'],
                self.dataset.xml: record['xml'],
                self.dataset.mdsource: record['source'],
                self.dataset.insert_date: record['insert_date']
                })
                self.session.commit()
            except Exception, err:
                self.session.rollback()
                raise RuntimeError, 'ERROR: %s' % str(err)
        else:  # update based on record properties
            try:
                self.session.begin()
#                rows=self.session.query(self.dataset).filter(
#                constraint['where']).update({
#                    self.dataset.xml: func.update_xpath(self.dataset.xml, str(recprops))
#                    getattr(self.dataset, .xml: func.update_xpath(self.dataset.xml, str(recprops))
#                }, synchronize_session='fetch')
                self.session.commit()
            except Exception, err:
                self.session.rollback()
                raise RuntimeError, 'ERROR: %s' % str(err)
            return rows

    def delete(self, constraint):
        ''' Delete a record from the repository '''

        try:
            self.session.begin()
            rows = self.session.query(self.dataset).filter(
            constraint['where']).delete(synchronize_session='fetch')
            self.session.commit()
        except Exception, err:
            self.session.rollback()
            raise RuntimeError, 'ERROR: %s' % str(err)

        return rows
