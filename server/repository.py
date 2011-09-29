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
            self.connection.create_function('get_anytext', 1, util.get_anytext)

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

        try:
            self.session.begin()
            self.session.add(record)
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
                identifier=record.identifier).update({
                self.dataset.identifier: record.identifier,
                self.dataset.typename: record.typename,
                self.dataset.schema: record.schema,
                self.dataset.mdsource: record.mdsource,
                self.dataset.insert_date: record.insert_date,
                self.dataset.xml: record.xml,
                self.dataset.anytext: record.anytext,
                self.dataset.language: record.language,
                self.dataset.type: record.type,
                self.dataset.title: record.title,
                self.dataset.title_alternate: record.title_alternate,
                self.dataset.abstract: record.abstract,
                self.dataset.keywords: record.keywords,
                self.dataset.keywordstype: record.keywordstype,
                self.dataset.parentidentifier: record.parentidentifier,
                self.dataset.relation: record.relation,
                self.dataset.time_begin: record.time_begin,
                self.dataset.time_end: record.time_end,
                self.dataset.topicategory: record.topicategory,
                self.dataset.resourcelanguage: record.resourcelanguage,
                self.dataset.creator: record.creator,
                self.dataset.publisher: record.publisher,
                self.dataset.contributor: record.contributor,
                self.dataset.organization: record.organization,
                self.dataset.securityconstraints: record.securityconstraints,
                self.dataset.accessconstraints: record.accessconstraints,
                self.dataset.otherconstraints: record.otherconstraints,
                self.dataset.date: record.date,
                self.dataset.date_revision: record.date_revision,
                self.dataset.date_creation: record.date_creation,
                self.dataset.date_publication: record.date_publication,
                self.dataset.date_modified: record.date_modified,
                self.dataset.format: record.format,
                self.dataset.source: record.source,
                self.dataset.crs: record.crs,
                self.dataset.geodescode: record.geodescode,
                self.dataset.denominator: record.denominator,
                self.dataset.distancevalue: record.distancevalue,
                self.dataset.distanceuom: record.distanceuom,
                self.dataset.geometry: record.geometry,
                self.dataset.servicetype: record.servicetype,
                self.dataset.servicetypeversion: record.servicetypeversion,
                self.dataset.operation: record.operation,
                self.dataset.couplingtype: record.couplingtype,
                self.dataset.operateson: record.operateson,
                self.dataset.operatesonidentifier: record.operatesonidentifier,
                self.dataset.operatesoname: record.operatesoname,
                self.dataset.degree: record.degree,
                self.dataset.classification: record.classification,
                self.dataset.conditionapplyingtoaccessanduse: record.conditionapplyingtoaccessanduse,
                self.dataset.lineage: record.lineage,
                self.dataset.responsiblepartyrole: record.responsiblepartyrole,
                self.dataset.specificationtitle: record.specificationtitle,
                self.dataset.specificationdate: record.specificationdate,
                self.dataset.specificationdatetype: record.specificationdatetype
                })
                self.session.commit()
            except Exception, err:
                self.session.rollback()
                raise RuntimeError, 'ERROR: %s' % str(err)
        else:  # update based on record properties
            try:
                rows = 0
                self.session.begin()
                for rpu in recprops:
                    rows += self.session.query(self.dataset).filter(
                        constraint['where']).update({
                            getattr(self.dataset, rpu['rp']['dbcol']): rpu['value'],
                            self.dataset.xml: func.update_xpath(self.dataset.xml, str(rpu)),
                            self.dataset.anytext: func.get_anytext(self.dataset.xml)
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
            constraint['where']).delete(synchronize_session='fetch')
            self.session.commit()
        except Exception, err:
            self.session.rollback()
            raise RuntimeError, 'ERROR: %s' % str(err)

        return rows
