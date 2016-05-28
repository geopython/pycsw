# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
# Copyright (c) 2015 Angelos Tzotsos
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

import time
import datetime
import logging
from six.moves.urllib.request import Request, urlopen
from shapely.wkt import loads
from owslib.util import http_post
from pycsw.core.etree import etree

from six import binary_type, text_type
LOGGER = logging.getLogger(__name__)

#Global variables for spatial ranking algorithm
ranking_enabled = False
ranking_pass = False
ranking_query_geometry = ''


PARSER = etree.XMLParser(resolve_entities=False)

def get_today_and_now():
    """Get the date, right now, in ISO8601"""
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())


def datetime2iso8601(value):
    """Return a datetime value as ISO8601"""
    if value is None:
        return None
    if isinstance(value, datetime.date):
        return value.strftime('%Y-%m-%d')
    if value.hour == 0 and value.minute == 0 and value.second == 0:
        # YYYY-MM-DD only
        return value.strftime('%Y-%m-%d')
    else:
        return value.strftime('%Y-%m-%dT%H:%M:%SZ')


def get_time_iso2unix(isotime):
    """Convert ISO8601 to UNIX timestamp"""
    return int(time.mktime(time.strptime(
        isotime, '%Y-%m-%dT%H:%M:%SZ'))) - time.timezone


def get_version_integer(version):
    """Get an integer of the OGC version value x.y.z"""
    if version is not None:  # split and make integer
        xyz = version.split('.')
        if len(xyz) != 3:
            return -1
        try:
            return int(xyz[0]) * 10000 + int(xyz[1]) * 100 + int(xyz[2])
        except Exception as err:
            raise RuntimeError('%s' % str(err))
    else:  # not a valid version string
        return -1


def find_exml(val, attrib=False):
    """Test that the XML value exists, return value, else return None"""
    if val is not None:
        if attrib:  # it's an XML attribute
            return val
        else:  # it's an XML value
            return val.text
    else:
        return None


def nspath_eval(xpath, nsmap):
    """Return an etree friendly xpath"""
    out = []
    for chunks in xpath.split('/'):
        namespace, element = chunks.split(':')
        out.append('{%s}%s' % (nsmap[namespace], element))
    return '/'.join(out)


def xmltag_split(tag):
    """Return XML element bare tag name (without prefix)"""
    try:
        return tag.split('}')[1]
    except:
        return tag


def xmltag_split2(tag, namespaces, colon=False):
    """Return XML namespace prefix of element"""
    try:
        nsuri = tag.split('}')[0].split('{')[1]
        nsprefix = [key for key, value in namespaces.items()
                    if value == nsuri]
        value = nsprefix[0]
        if colon:
            return '%s:' % nsprefix[0]
        else:
            return nsprefix[0]
    except:
        return ''


def wkt2geom(wkt, bounds=True):
    """return Shapely geometry object based on WKT/EWKT"""

    geometry = None

    if wkt.find('SRID') != -1:
        wkt = wkt.split(';')[-1]

    geometry = loads(wkt)

    if bounds:
        return geometry.envelope.bounds
    else:
        return geometry


def bbox2wktpolygon(bbox):
    """Return OGC WKT Polygon of a simple bbox string"""
    tmp = bbox.split(',')
    minx = float(tmp[0])
    miny = float(tmp[1])
    maxx = float(tmp[2])
    maxy = float(tmp[3])
    return 'POLYGON((%.2f %.2f, %.2f %.2f, %.2f %.2f, %.2f %.2f, %.2f %.2f))' \
        % (minx, miny, minx, maxy, maxx, maxy, maxx, miny, minx, miny)


def query_spatial(bbox_data_wkt, bbox_input_wkt, predicate, distance):
    """perform spatial query"""

    if bbox_data_wkt is None or bbox_input_wkt is None:
        return 'false'

    if predicate in ['beyond', 'dwithin'] and distance == 'false':
        return 'false'

    if bbox_data_wkt.find('SRID') != -1:  # it's EWKT; chop off 'SRID=\d+;'
        bbox1 = loads(bbox_data_wkt.split(';')[-1])
    else:
        bbox1 = loads(bbox_data_wkt)

    bbox2 = loads(bbox_input_wkt)

    # map query to Shapely Binary Predicates:
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
        if bbox1.intersects(bbox2) and not bbox1.touches(bbox2):
            result = True
        else:
            result = False
    elif predicate == 'touches':
        result = bbox1.touches(bbox2)
    elif predicate == 'within':
        result = bbox1.within(bbox2)
    else:
        raise RuntimeError('Invalid spatial query predicate: %s' % predicate)

    if result:
        return 'true'
    else:
        return 'false'


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

    from shapely.geometry.base import BaseGeometry
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
                    LOGGER.warn('Geometry has no area')
                    return '0'
            X = t_geom.intersection(q_geom).area
            if kt == 1.0 and kq == 1.0:
                LOGGER.debug('Spatial Rank: %s', str((X/Q)*(X/T)))
                return str((X/Q)*(X/T))
            else:
                LOGGER.debug('Spatial Rank: %s', str(((X/Q)**kq)*((X/T)**kt)))
                return str(((X/Q)**kq)*((X/T)**kt))
        except Exception as err:
                LOGGER.warn('Cannot derive spatial overlay ranking %s', err)
                return '0'
    return '0'

def bbox_from_polygons(bboxs):
    """Derive an aggregated bbox from n polygons"""

    from shapely.geometry import MultiPolygon

    polys = []
    for bbx in bboxs:
        polys.append(loads(bbx))

    try:
        bbx = MultiPolygon(polys).bounds
        bstr = '%.2f,%.2f,%.2f,%.2f' % (bbx[0], bbx[1], bbx[2], bbx[3])
        return bbox2wktpolygon(bstr)
    except Exception as err:
        raise RuntimeError('Cannot aggregate polygons: %s' % str(err))


def update_xpath(nsmap, xml, recprop):
    """Update XML document XPath values"""

    if isinstance(xml, binary_type) or isinstance(xml, text_type):
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


def transform_mappings(queryables, typename, reverse=False):
    """transform metadata model mappings"""
    if reverse:  # from csw:Record
        for qbl in queryables.keys():
            if qbl in typename.values():
                tmp = next(k for k, v in typename.items() if v == qbl)
                val = queryables[tmp]
                queryables[qbl] = {}
                queryables[qbl]['xpath'] = val['xpath']
                queryables[qbl]['dbcol'] = val['dbcol']
    else:  # to csw:Record
        for qbl in queryables.keys():
            if qbl in typename.keys():
                queryables[qbl] = queryables[qbl]


def get_anytext(bag):
    """
    generate bag of text for free text searches
    accepts list of words, string of XML, or etree.Element
    """

    if isinstance(bag, list):  # list of words
        return ' '.join([_f for _f in bag if _f]).strip()
    else:  # xml
        if isinstance(bag, binary_type) or isinstance(bag, text_type):
            # serialize to lxml
            bag = etree.fromstring(bag, PARSER)
        # get all XML element content
        return ' '.join([value.strip() for value in bag.xpath('//text()')])


def xml2dict(xml_string, namespaces):
    """Convert an lxml object to a dictionary"""

    import xmltodict

    namespaces_reverse = dict((v, k) for k, v in namespaces.items())

    return xmltodict.parse(xml_string, process_namespaces=True,
                           namespaces=namespaces_reverse)


def getqattr(obj, name):
    """get value of an object, safely"""
    try:
        value = getattr(obj, name)
        if hasattr(value, '__call__'):  # function generated value
            LOGGER.debug('attribute is a function')
            if name.find('link') != -1:  # list of link tuple quadruplets
                LOGGER.debug('attribute is a link')
                return _linkify(value())
            return value()
        elif (isinstance(value, datetime.datetime)
              or isinstance(value, datetime.date)):  # datetime object
            LOGGER.debug('attribute is a date')
            return datetime2iso8601(value)
        return value
    except:
        return None


def _linkify(value):
    """create link format"""
    out = []
    for link in value:
        out.append(','.join(list(link)))
    return '^'.join(out)


def http_request(method, url, request=None, timeout=30):
    """Perform HTTP request"""
    if method == 'POST':
        return http_post(url, request, timeout=timeout)
    else:  # GET
        request = Request(url)
        request.add_header('User-Agent', 'pycsw (http://pycsw.org/)')
        return urlopen(request, timeout=timeout).read()

def bind_url(url):
    """binds an HTTP GET query string endpoint"""
    if url.find('?') == -1: # like http://host/wms
        binder = '?'

    # if like http://host/wms?foo=bar& or http://host/wms?foo=bar
    if url.find('=') != -1:
        if url.find('&', -1) != -1: # like http://host/wms?foo=bar&
            binder = ''
        else: # like http://host/wms?foo=bar
            binder = '&'

    # if like http://host/wms?foo
    if url.find('?') != -1:
        if url.find('?', -1) != -1: # like http://host/wms?
            binder = ''
        elif url.find('&', -1) == -1: # like http://host/wms?foo=bar
            binder = '&'
    return '%s%s' % (url, binder)

def ip_in_network_cidr(ip, net):
    """decipher whether IP is within CIDR range"""
    ipaddr = int(''.join([ '%02x' % int(x) for x in ip.split('.') ]), 16)
    netstr, bits = net.split('/')
    netaddr = int(''.join([ '%02x' % int(x) for x in netstr.split('.') ]), 16)
    mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
    return (ipaddr & mask) == (netaddr & mask)

def ipaddress_in_whitelist(ipaddress, whitelist):
    """
    decipher whether IP is in IP whitelist
    IP whitelist is a list supporting:
    - single IP address (e.g. 192.168.0.1)
    - IP range using CIDR (e.g. 192.168.0/22)
    - IP range using subnet wildcard (e.g. 192.168.0.*, 192.168.*)
    """

    if ipaddress in whitelist:
        return True
    else:
        for white in whitelist:
            if white.find('/') != -1:  # CIDR
                if ip_in_network_cidr(ipaddress, white):
                    return True
            elif white.find('*') != -1:  # subnet wildcard
                    if ipaddress.startswith(white.split('*')[0]):
                        return True
    return False

def sniff_table(table):
    """Checks whether repository.table is a schema namespaced"""
    schema = None
    table = table
    if table.find('.') != - 1:
        schema, table = table.split('.')
    return [schema, table]


def validate_4326(bbox_list):
    ''' Helper function to validate 4326 '''

    is_valid = False

    if ((-180.0 <= float(bbox_list[0]) <= 180.0) and
        (-90.0 <= float(bbox_list[1]) <= 90.0) and
        (-180.0 <= float(bbox_list[2]) <= 180.0) and
        (-90.0 <= float(bbox_list[3]) <= 90.0)):
        is_valid = True

    return is_valid

def get_elapsed_time(begin, end):
    ''' Helper function to calculate elapsed time in milliseconds'''

    return int((end - begin) * 1000)
