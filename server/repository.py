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

    def query(self, flt=None, cql=None, ids=None, sortby=None,
     propertyname=None, typenames=['csw:Record', 'gmd:MD_Metadata']):
        ''' Query records from underlying repository '''
        if ids is not None:  # it's a GetRecordById request
            query = self.session.query(
            self.dataset).filter(getattr(self.dataset, propertyname).in_(ids))
        elif flt is not None:  # it's a GetRecords with filter
            query = self.session.query(self.dataset).filter(
            self.dataset.typename.in_(typenames)).filter(flt.where)
        elif flt is None and propertyname is None and cql is None:
        # it's a GetRecords sans filter
            query = self.session.query(self.dataset).filter(
            self.dataset.typename.in_(typenames))
        elif propertyname is not None:  # it's a GetDomain query
            query = self.session.query(func.query_xpath(
            getattr(self.dataset, 'xml'), propertyname)).filter(
            self.dataset.typename.in_(typenames)).distinct()
        elif cql is not None:  # it's a CQL query
            query = self.session.query(self.dataset).filter(
            self.dataset.typename.in_(typenames)).filter(cql)

        if sortby is not None:
            if sortby['order'] == 'DESC':
                return query.order_by(
                desc(func.query_xpath(
                self.dataset.xml, sortby['propertyname']))).all()
            else: 
                return query.order_by(func.query_xpath(
                self.dataset.xml, sortby['propertyname'])).all()

        return query.all()

    def insert(self, identifier, typename, schema, bbox, xml, source, insert_date):
        ''' Insert a record into the repository '''

        ins = self.dataset.__table__.insert()
        ins.execute(
        identifier=identifier,
        typename=typename,
        schema=schema,
        bbox=bbox,
        xml=xml,
        source=source,
        insert_date=insert_date)

        self.session.flush()

