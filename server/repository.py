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
    def __init__(self, repo, table, config):
        ''' Initialize repository '''

        database = repo['database']

        engine = create_engine('%s' % database, echo=False)

        base = declarative_base(bind=engine)

        self.dataset = type('dataset', (base,),
        dict(__tablename__=table,__table_args__={'autoload': True}))

        self.session = create_session(engine)
        self.connection = engine.raw_connection()
        self.connection.create_function('query_spatial', 4, util.query_spatial)
        self.connection.create_function('query_anytext', 2, util.query_anytext)
        self.connection.create_function('query_xpath', 2, util.query_xpath)
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
        query = self.session.query(func.query_xpath(
        self.dataset.xml, domain)).filter(
        self.dataset.typename.in_(typenames)).distinct()
        return query.all()

    def query_source(self, source):
        ''' Query by source '''
        query = self.session.query(self.dataset).filter(
        self.dataset.source == source)
        return query.all() 

    def query(self, constraint, sortby=None,
    typenames=['csw:Record', 'gmd:MD_Metadata']):
        ''' Query records from underlying repository '''

        if constraint.has_key('where'):  # it's a GetRecords with constraint
            query = self.session.query(self.dataset).filter(
            self.dataset.typename.in_(typenames)).filter(constraint['where'])

        elif constraint.has_key('where') is False: # it's a GetRecords sans constraint
            query = self.session.query(self.dataset).filter(
            self.dataset.typename.in_(typenames))

        if sortby is not None:
            if sortby['order'] == 'DESC':
                return query.order_by(
                desc(func.query_xpath(
                self.dataset.xml, sortby['propertyname']))).all()
            else: 
                return query.order_by(func.query_xpath(
                self.dataset.xml, sortby['propertyname'])).all()

        return query.all()

    def insert(self, record):
        ''' Insert a record into the repository '''

        record1 = self.dataset(
        identifier=record['identifier'],
        typename=record['typename'],
        schema=record['schema'],
        bbox=record['bbox'],
        xml=record['xml'],
        source=record['source'],
        insert_date=record['insert_date'])

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
                identifier=record['identifier']).update(
                {self.dataset.xml: record['xml'],
                self.dataset.insert_date: record['insert_date']})
                self.session.commit()
            except Exception, err:
                self.session.rollback()
                raise RuntimeError, 'ERROR: %s' % str(err)
        else:  # update based on record properties
            try:
                self.session.begin()
                self.session.query(self.dataset).filter(
                constraint['where']).update(
                {self.dataset.xml: func.update_xpath(
                self.dataset.xml, recprops)}, synchronize_session='fetch')
            except Exception, err:
                self.session.rollback()
                raise RuntimeError, 'ERROR: %s' % str(err)

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
