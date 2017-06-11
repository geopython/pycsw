# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#          Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
# Copyright (c) 2015 Angelos Tzotsos
# Copyright (c) 2017 Ricardo Garcia Silva
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

import datetime
import logging
import time

import six
from six.moves.urllib.request import Request, urlopen
from six.moves.urllib.parse import urlparse
from shapely.wkt import loads
from owslib.util import http_post

from pycsw.core.etree import etree, PARSER

LOGGER = logging.getLogger(__name__)

# Global variables for spatial ranking algorithm
ranking_enabled = False
ranking_pass = False
ranking_query_geometry = ''


def get_today_and_now():
    """Get the date, right now, in ISO8601"""
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime())


def datetime2iso8601(value):
    """Return a datetime value as ISO8601

    Parameters
    ----------
    value: datetime.date or datetime.datetime
        The temporal value to be converted

    Returns
    -------
    str
        A string with the temporal value in ISO8601 format.

    """

    if isinstance(value, datetime.datetime):
        if value == value.replace(hour=0, minute=0, second=0, microsecond=0):
            result = value.strftime("%Y-%m-%d")
        else:
            result = value.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:  # value is a datetime.date
        result = value.strftime('%Y-%m-%d')
    return result


def get_time_iso2unix(isotime):
    """Convert ISO8601 to UNIX timestamp"""
    return int(time.mktime(time.strptime(
        isotime, '%Y-%m-%dT%H:%M:%SZ'))) - time.timezone


def get_version_integer(version):
    """Get an integer of the OGC version value x.y.z

    In case of an invalid version string this returns -1.

    Parameters
    ----------
    version: str
        The version string that is to be transformed into an integer

    Returns
    -------
    int
        The transformed version

    Raises
    ------
    RuntimeError
        When the input version is neither a string or None

    """

    try:
        xyz = version.split('.')
        if len(xyz) == 3:
            result = int(xyz[0]) * 10000 + int(xyz[1]) * 100 + int(xyz[2])
        else:
            result = -1
    except AttributeError as err:
        raise RuntimeError('%s' % str(err))
    return result


def nspath_eval(xpath, nsmap):
    """Return an etree friendly xpath.

    This function converts XPath expressions that use prefixes into
    their full namespace. This is the form expected by lxml [1]_.

    Parameters
    ----------
    xpath: str
        The XPath expression to be converted
    nsmap: dict

    Returns
    -------
    str
        The XPath expression using namespaces instead of prefixes.

    References
    ----------
    .. [1] http://lxml.de/tutorial.html#namespaces

    """

    out = []
    for node in xpath.split('/'):
        chunks = node.split(":")
        if len(chunks) == 2:
            prefix, element = node.split(':')
            out.append('{%s}%s' % (nsmap[prefix], element))
        elif len(chunks) == 1:
            out.append(node)
        else:
            raise RuntimeError("Invalid XPath expression: {0}".format(xpath))
    return '/'.join(out)


def wktenvelope2bbox(envelope):
    """returns bbox string of WKT ENVELOPE definition"""

    tmparr = [x.strip() for x in envelope.split('(')[1].split(')')[0].split(',')]
    bbox = '%s,%s,%s,%s' % (tmparr[0], tmparr[3], tmparr[1], tmparr[2])
    return bbox


def wkt2geom(ewkt, bounds=True):
    """Return Shapely geometry object based on WKT/EWKT

    Parameters
    ----------
    ewkt: str
        The geometry to convert, in Extended Well-Known Text format. More info
        on this format at [1]_
    bounds: bool
        Whether to return only the bounding box of the geometry as a tuple or
        the full shapely geometry instance

    Returns
    -------
    shapely.geometry.base.BaseGeometry or tuple
        Depending on the value of the ``bounds`` parameter, returns either 
        the shapely geometry instance or a tuple with the bounding box.

    References
    ----------
    .. [1] http://postgis.net/docs/ST_GeomFromEWKT.html

    """

    wkt = ewkt.split(";")[-1] if ewkt.find("SRID") != -1 else ewkt
    if wkt.startswith('ENVELOPE'):
        wkt = bbox2wktpolygon(wktenvelope2bbox(wkt))
    geometry = loads(wkt)
    return geometry.envelope.bounds if bounds else geometry


def bbox2wktpolygon(bbox):
    """Return OGC WKT Polygon of a simple bbox string

    Parameters
    ----------
    bbox: str
        The bounding box to convert to WKT.

    Returns
    -------
    str
        The bounding box's Well-Known Text representation.

    """

    if bbox.startswith('ENVELOPE'):
        bbox = wktenvelope2bbox(bbox)
    minx, miny, maxx, maxy = [float(coord) for coord in bbox.split(",")]
    return 'POLYGON((%.2f %.2f, %.2f %.2f, %.2f %.2f, %.2f %.2f, %.2f %.2f))' \
        % (minx, miny, minx, maxy, maxx, maxy, maxx, miny, minx, miny)


def transform_mappings(queryables, typename):
    """Transform metadata model mappings

    Parameters
    ----------
    queryables: dict
    typename: dict

    """

    for item in queryables:
        try:
            matching_typename = [key for key, value in typename.items() if
                                 value == item][0]
            queryable_value = queryables[matching_typename]
            queryables[item] = {
                "xpath": queryable_value["xpath"],
                "dbcol": queryable_value["dbcol"],
            }
        except IndexError:
            pass


def getqattr(obj, name):
    """Get value of an object, safely"""
    result = None
    try:
        item = getattr(obj, name)
        value = item()
        if "link" in name:  # create link format
            links = []
            for link in value:
                links.append(','.join(list(link)))
            result = '^'.join(links)
        else:
            result = value
    except TypeError:  # item is not callable
        try:
            result = datetime2iso8601(item)
        except AttributeError:  # item is not date(time)
            result = item
    except AttributeError:  # obj does not have a name property
        pass
    return result


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
    parsed_url = urlparse(url)
    if parsed_url.query == "":
        binder = "?"
    elif parsed_url.query.endswith("&"):
        binder = ""
    else:
        binder = "&"
    return "".join((parsed_url.geturl(), binder))


def ip_in_network_cidr(ip, net):
    """decipher whether IP is within CIDR range"""
    ipaddr = int(
        ''.join(['%02x' % int(x) for x in ip.split('.')]),
        16
    )
    netstr, bits = net.split('/')
    netaddr = int(
        ''.join(['%02x' % int(x) for x in netstr.split('.')]),
        16
    )
    mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
    return (ipaddr & mask) == (netaddr & mask)


def ipaddress_in_whitelist(ipaddress, whitelist):
    """decipher whether IP is in IP whitelist

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


def get_anytext(bag):
    """
    generate bag of text for free text searches
    accepts list of words, string of XML, or etree.Element
    """

    if isinstance(bag, list):  # list of words
        return ' '.join([_f for _f in bag if _f]).strip()
    else:  # xml
        if isinstance(bag, six.binary_type) or isinstance(bag, six.text_type):
            # serialize to lxml
            bag = etree.fromstring(bag, PARSER)
        # get all XML element content
        return ' '.join([value.strip() for value in bag.xpath('//text()')])
