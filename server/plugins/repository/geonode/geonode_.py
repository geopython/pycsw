# -*- coding: iso-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2012 Tom Kralidis
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

import os, sys
# ensure GeoNode based settings are set/enabled

os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'
sys.path.append('/home/tkralidi/geonode/lib/python2.6/site-packages')
sys.path.append('/home/tkralidi/geonode/src/GeoNodePy')
sys.path.append('/home/tkralidi/geonode/src/gsconfig.py/src')
sys.path.append('/home/tkralidi/geonode/src/avatar')

from django.db import models
from django.db import connection
from django.db.models import Avg, Max, Min, Count
from django.conf import settings

from server import util
from geonode.maps.models import Layer

class GeoNodeRepository(object):
    ''' Class to interact with underlying repository '''
    def __init__(self, context):
        ''' Initialize repository '''

        self.context = context

        self.dbtype = settings.DATABASE_ENGINE

        if self.dbtype in ['sqlite', 'sqlite3']:  # load SQLite query bindings
            cursor = connection.cursor()
            connection.connection.create_function(
            'query_spatial', 4, util.query_spatial)
            connection.connection.create_function(
            'update_xpath', 2, util.update_xpath(self.context))
            connection.connection.create_function(
            'get_anytext', 1, util.get_anytext)

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
        return Layer.objects.filter(uuid__in=ids).all()

    def query_domain(self, domain, typenames, domainquerytype='list',
        count=False):
        ''' Query by property domain values '''

        if domainquerytype == 'range':
            return [tuple(Layer.objects.aggregate(
            Min(domain), Max(domain)).values())]
        else:
            if count is True:
                return [tuple(i.values()) for i in r.objects.values(
                domain).annotate(Count(domain))]
            else:
                return Layer.objects.values_list(domain).distinct()


    def query_latest_insert(self):
        ''' Query to get latest update to repository '''
        from datetime import datetime
        return Layer.objects.aggregate(
            Max('date'))['date__max'].strftime('%Y-%m-%dT%H:%M:%SZ')

    def query_source(self, source):
        ''' Query by source '''
        return Layer.objects.filter(source=source)

    def query(self, constraint, sortby=None, typenames=None,
        maxrecords=10, startposition=0):
        ''' Query records from underlying repository '''

        # run the raw query and get total
        if constraint.has_key('where'):  # GetRecords with constraint
            # escape wildcards for django
            if constraint['where'].find('%') != -1:
                constraint['where'] = constraint['where'].replace('%','%%')
            if not typenames:  # any typename
                query = Layer.objects.extra(where=[constraint['where']])
            else:
                query = Layer.objects.filter(csw_typename__in=typenames).extra(
                where=[constraint['where']])

            total = query.count()

        else:  # GetRecords sans constraint
            if not typenames:  # any typename
                query = Layer.objects
            else:
                query = Layer.objects.filter(csw_typename__in=typenames)

            total = query.count()

        # apply sorting, limit and offset
        if sortby is not None:
            if sortby['order'] == 'DESC':
                pname = '-%s' % sortby['propertyname']
            else:
                pname = sortby['propertyname']
            return [str(total), \
            query.order_by(pname)[startposition:maxrecords]]
        else:  # no sort
            return [str(total), query[startposition:maxrecords]]
