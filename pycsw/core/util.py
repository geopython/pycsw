# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#          Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2025 Tom Kralidis
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

from configparser import BasicInterpolation, ConfigParser
from pathlib import Path
import importlib
import importlib.util
import json
import os
import re
import datetime
import logging
import sys
import time
import typing

from urllib.request import Request, urlopen
from urllib.parse import urlparse
from shapely.geometry import shape
from shapely.wkt import loads
from owslib.util import http_post

from pycsw.core.etree import etree, PARSER

LOGGER = logging.getLogger(__name__)

# Global variables for spatial ranking algorithm
ranking_enabled = False
ranking_pass = False
ranking_query_geometry = ''

# Lookups for the secure_filename function
# https://github.com/pallets/werkzeug/blob/778f482d1ac0c9e8e98f774d2595e9074e6984d7/werkzeug/utils.py#L30-L31
_filename_ascii_strip_re = re.compile(r'[^A-Za-z0-9_.-]')
_windows_device_files = ('CON', 'AUX', 'COM1', 'COM2', 'COM3', 'COM4', 'LPT1',
                         'LPT2', 'LPT3', 'PRN', 'NUL')


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
        raise RuntimeError('%s' % str(err)) from err
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
            raise RuntimeError(f"Invalid XPath expression: {xpath}")
    return '/'.join(out)


def wktenvelope2bbox(envelope):
    """returns bbox string of WKT ENVELOPE definition"""

    tmparr = [x.strip() for x in envelope.split('(')[1].split(')')[0].split(',')]
    bbox = '%s,%s,%s,%s' % (tmparr[0], tmparr[3], tmparr[1], tmparr[2])
    return bbox


def geojson_geometry2bbox(geometry):
    """returns bbox string of GeoJSON geometry"""

    bounds = shape(geometry).bounds
    return ','.join([str(b) for b in bounds])


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

    precision = int(os.environ.get('COORDINATE_PRECISION', 2))
    if bbox.startswith('ENVELOPE'):
        bbox = wktenvelope2bbox(bbox)
    minx, miny, maxx, maxy = [f"{float(coord):.{precision}f}" for coord in bbox.split(",")]
    wktGeometry = 'POLYGON((%s %s, %s %s, %s %s, %s %s, %s %s))' \
        % (minx, miny, minx, maxy, maxx, maxy, maxx, miny, minx, miny)
    return wktGeometry


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
        request.add_header('User-Agent', 'pycsw (https://pycsw.org/)')
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
        if isinstance(bag, bytes) or isinstance(bag, str):
            # serialize to lxml
            bag = etree.fromstring(bag, PARSER)
        # get all XML element content
        return ' '.join([value.strip() for value in bag.xpath('//text()')])


# https://stackoverflow.com/a/39234154
def get_anytext_from_obj(obj):
    """
    generate bag of text for free text searches
    accepts dict, list or string
    """

    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, (list, dict)):
                yield from get_anytext_from_obj(value)
            else:
                yield value
    elif isinstance(obj, list):
        for value in obj:
            if isinstance(value, (list, dict)):
                yield from get_anytext_from_obj(value)
            else:
                yield value


# https://github.com/pallets/werkzeug/blob/778f482d1ac0c9e8e98f774d2595e9074e6984d7/werkzeug/utils.py#L253
def secure_filename(filename):
    r"""Pass it a filename and it will return a secure version of it.  This
    filename can then safely be stored on a regular file system and passed
    to :func:`os.path.join`.  The filename returned is an ASCII only string
    for maximum portability.

    On windows systems the function also makes sure that the file is not
    named after one of the special device files.

    >>> secure_filename("My cool movie.mov")
    'My_cool_movie.mov'
    >>> secure_filename("../../../etc/passwd")
    'etc_passwd'
    >>> secure_filename(u'i contain cool \xfcml\xe4uts.txt')
    'i_contain_cool_umlauts.txt'

    The function might return an empty filename.  It's your responsibility
    to ensure that the filename is unique and that you abort or
    generate a random filename if the function returned an empty one.

    .. versionadded:: 0.5

    :param filename: the filename to secure
    """
    if isinstance(filename, str):
        from unicodedata import normalize
        filename = normalize('NFKD', filename).encode('ascii', 'ignore')
        filename = filename.decode('ascii')
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, ' ')
    filename = str(_filename_ascii_strip_re.sub('', '_'.join(
                   filename.split()))).strip('._')

    # on nt a couple of special files are present in each folder.  We
    # have to ensure that the target file is not such a filename.  In
    # this case we prepend an underline
    if os.name == 'nt' and filename and \
       filename.split('.')[0].upper() in _windows_device_files:
        filename = '_' + filename

    return filename


def jsonify_links(links):
    """
    pycsw:Links column data handler.
    casts old or new style links into JSON objects
    """
    try:
        LOGGER.debug('JSON link')
        linkset = json.loads(links)
        return linkset
    except json.decoder.JSONDecodeError:  # try CSV parsing
        LOGGER.debug('old style CSV link')
        json_links = []
        for link in links.split('^'):
            tokens = link.split(',')
            json_links.append({
                'name': tokens[0] or None,
                'description': tokens[1] or None,
                'protocol': tokens[2] or None,
                'url': tokens[3] or None
            })
        return json_links


class EnvInterpolation(BasicInterpolation):
    """
    Interpolation which expands environment variables in values.
    from: https://stackoverflow.com/a/49529659
    """

    def before_get(self, parser, section, option, value, defaults):
        value = super().before_get(parser, section, option, value, defaults)
        return os.path.expandvars(value)


def parse_ini_config(config_path) -> ConfigParser:
    """
    Helper function to parse a .ini configuration file

    :param config_path: filepath

    :returns: ConfigParser object
    """

    config = ConfigParser(interpolation=EnvInterpolation())
    with open(config_path, encoding='utf-8') as scp:
        config.read_file(scp)
    return config


def is_none_or_empty(value):
    """
    Helper function to detect if value is None or empty

    :param value: value to evaluate

    :returns: bool of whether the value is None or empty
    """

    if value is None or len(value.strip()) == 0:
        return True

    return False


def programmatic_import(target_module: str) -> typing.Optional[typing.Any]:
    result = None
    target_module_path = Path(target_module)
    if target_module_path.is_file():
        module_name = target_module_path.stem
        # this is an adaptation of the Python docs on using importlib to import a
        # filepath:
        # https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
        spec = importlib.util.spec_from_file_location(
            module_name, target_module_path)
        if spec is not None:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            result = module
    else:
        try:
            result = importlib.import_module(target_module)
        except ModuleNotFoundError:
            pass
    return result


def load_custom_repo_mappings(repository_mappings: str) -> typing.Optional[typing.Dict]:
    imported_mappings_module = programmatic_import(repository_mappings)
    result = None
    if imported_mappings_module is not None:
        result = getattr(imported_mappings_module, "MD_CORE_MODEL", None)
    return result


def sanitize_db_connect (url):
    """
    helper function to remove user:pw from db connect for logging purposes

    :param url: value to be sanitized

    :returns: `str` sanitized
    """
    if '@' in url:
        return url.split('://')[0] + '://***:***@' + url.split('@').pop()
    else:
        return url

def str2bool(value: typing.Union[bool, str]) -> bool:
    """
    helper function to return Python boolean
    type (source: https://stackoverflow.com/a/715468)

    :param value: value to be evaluated

    :returns: `bool` of whether the value is boolean-ish
    """

    value2 = False

    if isinstance(value, bool):
        value2 = value
    else:
        value2 = value.lower() in ('yes', 'true', 't', '1', 'on')

    return value2
