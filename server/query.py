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

from sqlalchemy import *
from sqlalchemy.orm import *
import config, util

class dsc(object):
    pass

class Query(object):
    def __init__(self, db):
        db = create_engine('sqlite:///%s' % db, echo=False)

        dst = Table('dataset', MetaData(db), autoload=True)
       
        mapper(dsc,dst)
        
        self.session=create_session()
        self.connection = db.raw_connection()
        self.connection.create_function('bbox_query',2,util.bbox_query)
        self.connection.create_function('anytext_query',2,util.anytext_query)
       
    def get(self,filter=None,ids=None,sortby=None):
        if ids is not None:  # it's a GetRecordById request
            q = self.session.query(dsc).filter(dsc.identifier.in_(ids))
        elif filter is not None:  # it's a GetRecords with filter
            q = self.session.query(dsc).filter(filter.where)
        elif filter is None:  # it's a GetRecords sans filter
            q = self.session.query(dsc)

        if sortby is not None:
            if sortby['order'] == 'DESC':
                return q.order_by(desc(config.mappings[sortby['propertyname']])).all()
            else: 
                return q.order_by(config.mappings[sortby['propertyname']]).all()

        return q.all()
