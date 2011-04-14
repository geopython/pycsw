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

from sqlalchemy import create_engine, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session
import util

class Repository(object):
    ''' Class to interact with underlying repository '''
    def __init__(self, database, table):
        ''' Initialize repository '''
        engine = create_engine('%s' % database, echo=False)

        base = declarative_base(bind=engine)

        self.dataset = type('dataset', (base,),
        dict(__tablename__=table,__table_args__={'autoload': True}))

        self.session = create_session(engine)
        self.connection = engine.raw_connection()
        self.connection.create_function('query_bbox', 2, util.query_bbox)
        self.connection.create_function('query_anytext', 2, util.query_anytext)
        self.connection.create_function('query_xpath', 2, util.query_xpath)
       
    def query(self, flt=None, cql=None, ids=None, sortby=None,
     propertyname=None):
        ''' Query records from underlying repository '''
        if ids is not None:  # it's a GetRecordById request
            query = self.session.query(
            self.dataset).filter(getattr(self.dataset, propertyname).in_(ids))
        elif flt is not None:  # it's a GetRecords with filter
            query = self.session.query(self.dataset).filter(flt.where)
        elif flt is None and propertyname is None and cql is None:
        # it's a GetRecords sans filter
            query = self.session.query(self.dataset)
        elif propertyname is not None:  # it's a GetDomain query
            query = self.session.query(getattr(self.dataset,
            propertyname)).filter('%s is not null' % propertyname).distinct()
        elif cql is not None:  # it's a CQL query
            query = self.session.query(self.dataset).filter(cql)

        if sortby is not None:
            if sortby['order'] == 'DESC':
                return query.order_by(desc(sortby['cq_mapping'])).all()
            else: 
                return query.order_by(sortby['cq_mapping']).all()

        return query.all()
