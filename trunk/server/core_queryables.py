# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2011 Tom Kralidis
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

class CoreQueryables(object):
    ''' Core Queryables for CSW '''
    def __init__(self, config, name):
        ''' Generate Core Queryables db and obj bindings '''
        self.typename = config['repository']['typename']
        self.name = name
        self.mappings = {}
        table = config['repository']['db_table']
        for cqm in config['repository']:
            if cqm.find('cq_') != -1:  # it's a cq
                k = cqm.replace('cq_','').replace('_',':') 
                cqv = config['repository'][cqm]
                val = '%s_%s' % (table, cqv)
                self.mappings[k] = {}
                self.mappings[k]['db_col'] = val
                self.mappings[k]['obj_attr'] = cqv
                # check for identifier, bbox, and anytext fields, and set
                # as internal keys
                # need to catch these to perform id, bbox, or anytext queries
                if k.split(':')[-1].lower() == 'identifier':
                    self.mappings['_id'] = {}
                    self.mappings['_id']['db_col'] = val
                    self.mappings['_id']['obj_attr'] = cqv
                if k.split(':')[-1].lower().find('boundingbox') != -1:
                    self.mappings['_bbox'] = {}
                    self.mappings['_bbox']['db_col'] = val
                    self.mappings['_bbox']['obj_attr'] = cqv
                if k.split(':')[-1].lower().find('anytext') != -1:
                    self.mappings['_anytext'] = {}
                    self.mappings['_anytext']['db_col'] = val
                    self.mappings['_anytext']['obj_attr'] = cqv


    def get_db_col(self, term):
        '''' Return database column of core queryable '''
        return self.mappings[term]['db_col']

    def get_obj_attr(self, term):
        '''' Return object attribute of core queryable '''
        return self.mappings[term]['obj_attr']
