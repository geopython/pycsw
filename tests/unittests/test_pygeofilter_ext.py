"""Axis order of GML geometries in CSW filters for repositories without a database."""

import pytest
from shapely import wkt
from shapely.geometry import shape

from pycsw.core.etree import etree
from pycsw.core.pygeofilter_ext import PycswCSWFES11Parser, gml_to_xy
from pycsw.ogc.gml import gml3

pytestmark = pytest.mark.unit

NS = 'xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml"'


def bbox_filter(lower, upper, srs=None):
    srs_attr = f' srsName="{srs}"' if srs else ''
    return f'''<ogc:Filter {NS}><ogc:BBOX><ogc:PropertyName>ows:BoundingBox</ogc:PropertyName>
      <gml:Envelope{srs_attr}><gml:lowerCorner>{lower}</gml:lowerCorner>
      <gml:upperCorner>{upper}</gml:upperCorner></gml:Envelope></ogc:BBOX></ogc:Filter>'''


def parsed_bounds(filter_xml):
    """(minx, miny, maxx, maxy) of the geometry pygeofilter parsed."""
    node = PycswCSWFES11Parser().parse(filter_xml)
    stack = [node]
    while stack:
        node = stack.pop()
        geometry = getattr(node, 'geometry', None)
        if isinstance(geometry, dict):
            return tuple(round(v, 6) for v in shape(geometry).bounds)
        stack.extend(v for v in vars(node).values() if hasattr(v, '__dict__'))
    raise AssertionError('no geometry in the parsed filter')


@pytest.mark.parametrize('srs', [
    None,                                  # pycsw's default: EPSG:4326, latitude first
    'urn:ogc:def:crs:EPSG::4326',          # what QGIS MetaSearch sends
    'urn:x-ogc:def:crs:EPSG:6.11:4326',
    'http://www.opengis.net/def/crs/EPSG/0/4326',
    'EPSG:4326',
])
def test_latitude_first_crs_is_swapped(srs):
    # 76-80 N, 10-20 E written latitude first
    assert parsed_bounds(bbox_filter('76 10', '80 20', srs)) == (10, 76, 20, 80)


@pytest.mark.parametrize('srs', ['urn:ogc:def:crs:OGC:1.3:CRS84', 'urn:ogc:def:crs:OGC::CRS84'])
def test_longitude_first_crs_is_kept(srs):
    assert parsed_bounds(bbox_filter('10 76', '20 80', srs)) == (10, 76, 20, 80)


def test_polygon_without_srsname_is_latitude_first():
    xml = f'''<ogc:Filter {NS}><ogc:Within><ogc:PropertyName>ows:BoundingBox</ogc:PropertyName>
      <gml:Polygon><gml:exterior><gml:LinearRing>
      <gml:posList>76 10 76 20 80 20 80 10 76 10</gml:posList>
      </gml:LinearRing></gml:exterior></gml:Polygon></ogc:Within></ogc:Filter>'''
    assert parsed_bounds(xml) == (10, 76, 20, 80)


def test_same_box_as_database_repositories():
    """The parsed box matches gml3.Geometry, used by database repositories."""
    for srs in (None, 'urn:ogc:def:crs:EPSG::4326', 'urn:ogc:def:crs:OGC:1.3:CRS84'):
        lower, upper = ('10 76', '20 80') if srs and 'CRS84' in srs else ('76 10', '80 20')
        xml = bbox_filter(lower, upper, srs)
        envelope = etree.fromstring(xml).find('.//{http://www.opengis.net/ogc}BBOX')
        sql_bounds = wkt.loads(gml3.Geometry(envelope, {'gml': 'http://www.opengis.net/gml'}).wkt).bounds
        assert parsed_bounds(xml) == tuple(round(v, 6) for v in sql_bounds)


def test_polygon_poslist_is_swapped():
    xml = f'''<ogc:Filter {NS}><ogc:Intersects><ogc:PropertyName>ows:BoundingBox</ogc:PropertyName>
      <gml:Polygon srsName="urn:ogc:def:crs:EPSG::4326"><gml:exterior><gml:LinearRing>
      <gml:posList>76 10 76 20 80 20 80 10 76 10</gml:posList>
      </gml:LinearRing></gml:exterior></gml:Polygon></ogc:Intersects></ogc:Filter>'''
    assert parsed_bounds(xml) == (10, 76, 20, 80)


def test_gml2_coordinates_are_swapped():
    xml = f'''<ogc:Filter {NS}><ogc:BBOX><ogc:PropertyName>ows:BoundingBox</ogc:PropertyName>
      <gml:Box srsName="EPSG:4326"><gml:coordinates>76,10 80,20</gml:coordinates></gml:Box>
      </ogc:BBOX></ogc:Filter>'''
    root = gml_to_xy(xml)
    assert root.find('.//{http://www.opengis.net/gml}coordinates').text == '10,76 20,80'


def test_input_element_is_not_modified():
    element = etree.fromstring(bbox_filter('76 10', '80 20'))
    gml_to_xy(element)
    assert element.find('.//{http://www.opengis.net/gml}lowerCorner').text == '76 10'
    assert element.find('.//{http://www.opengis.net/gml}Envelope').get('srsName') is None
