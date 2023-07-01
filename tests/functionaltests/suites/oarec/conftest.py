import configparser

import pytest


@pytest.fixture()
def config():
    config = configparser.ConfigParser()
    config['server'] = {
        'home': '/var/www/pycsw',
        'url': 'http://localhost/pycsw/oarec',
        'mimetype': 'application/xml;',
        'charset': 'UTF-8',
        'encoding': 'UTF-8',
        'language': 'en-US',
        'maxrecords': '10',
        'gzip_compresslevel': '9',
        'profiles': 'apiso',
    }
    config['manager'] = {
        'transactions': 'true',
        'allowed_ips': '127.0.0.1',
    }
    config['metadata:main'] = {
        'identification_title': 'pycsw Geospatial Catalogue',
        'identification_abstract': 'pycsw is an OARec and OGC CSW server implementation written in Python',
        'identification_keywords': 'catalogue,discovery,metadata',
        'identification_keywords_type': 'theme',
        'identification_fees': 'None',
        'identification_accessconstraints': 'None',
        'provider_name': 'Organization Name',
        'provider_url': 'https://pycsw.org/',
        'contact_name': 'Lastname, Firstname',
        'contact_position': 'Position Title',
        'contact_address': 'Mailing Address',
        'contact_city': 'City',
        'contact_stateorprovince': 'Administrative Area',
        'contact_postalcode': 'Zip or Postal Code',
        'contact_country': 'Country',
        'contact_phone': '+xx-xxx-xxx-xxxx',
        'contact_fax': '+xx-xxx-xxx-xxxx',
        'contact_email': 'you@example.org',
        'contact_url': 'Contact URL',
        'contact_hours': 'Hours of Service',
        'contact_instructions': 'During hours of service.  Off on weekends.',
        'contact_role': 'pointOfContact',
    }
    config['repository'] = {
        'database': 'sqlite:///tests/functionaltests/suites/cite/data/cite.db',
        'table': 'records',
    }
    config['metadata:inspire'] = {
        'enabled': 'true',
        'languages_supported': 'eng,gre',
        'default_language': 'eng',
        'date': 'YYYY-MM-DD',
        'gemet_keywords': 'Utility and governmental services',
        'conformity_service': 'notEvaluated',
        'contact_name': 'Organization Name',
        'contact_email': 'Email Address',
        'temp_extent': 'YYYY-MM-DD/YYYY-MM-DD',
    }
    yield config


@pytest.fixture()
def config_virtual_collections(config):
    database = config['repository']['database']
    config['repository']['database'] = database.replace('cite.db', 'cite-virtual-collections.db')  # noqa
    return config


@pytest.fixture()
def sample_record():
    yield {
        "id": "record-123",
        "conformsTo": [
            "http://www.opengis.net/spec/ogcapi-records-1/1.0/req/record-core"
        ],
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-141, 42],
                [-141, 84],
                [-52, 84],
                [-52, 42],
                [-141, 42]
            ]]
        },
        "properties": {
            "identifier": "3f342f64-9348-11df-ba6a-0014c2c00eab",
            "title": "title in English",
            "description": "abstract in English",
            "themes": [
                {
                    "concepts": [
                        "kw1 in English",
                        "kw2 in English",
                        "kw3 in English"
                    ]
                },
                {
                    "concepts": [
                        "FOO",
                        "BAR"
                    ],
                    "scheme": "http://example.org/vocab"
                },
                {
                    "concepts": [
                        "kw1",
                        "kw2"
                    ]
                }
            ],
            "providers": [
                {
                    "name": "Environment Canada",
                    "individual": "Tom Kralidis",
                    "positionName": "Senior Systems Scientist",
                    "contactInfo": {
                        "phone": {
                            "office": "+01-123-456-7890"
                        },
                        "email": {
                            "office": "+01-123-456-7890"
                        },
                        "address": {
                            "office": {
                                "deliveryPoint": "4905 Dufferin Street",
                                "city": "Toronto",
                                "administrativeArea": "Ontario",
                                "postalCode": "M3H 5T4",
                                "country": "Canada"
                            },
                            "onlineResource": {
                                "href": "https://www.ec.gc.ca/"
                            }
                        },
                        "hoursOfService": "0700h - 1500h EST",
                        "contactInstructions": "email",
                        "url": {
                            "rel": "canonical",
                            "type": "text/html",
                            "href": "https://www.ec.gc.ca/"
                        }
                    },
                    "roles": [
                        {"name": "pointOfContact"}
                    ]
                },
                {
                    "name": "Environment Canada",
                    "individual": "Tom Kralidis",
                    "positionName": "Senior Systems Scientist",
                    "contactInfo": {
                        "phone": {"office": "+01-123-456-7890"},
                        "email": {"office": "+01-123-456-7890"},
                        "address": {
                            "office": {
                                "deliveryPoint": "4905 Dufferin Street",
                                "city": "Toronto",
                                "administrativeArea": "Ontario",
                                "postalCode": "M3H 5T4",
                                "country": "Canada"
                            },
                            "onlineResource": {"href": "https://www.ec.gc.ca/"}
                        },
                        "hoursOfService": "0700h - 1500h EST",
                        "contactInstructions": "email",
                        "url": {
                            "rel": "canonical",
                            "type": "text/html",
                            "href": "https://www.ec.gc.ca/"
                        }
                    },
                    "roles": [
                        {"name": "distributor"}
                    ]
                }
            ],
            "language": "en",
            "type": "dataset",
            "created": "2011-11-11",
            "recordUpdated": "2000-09-01",
            "rights": "Copyright (c) 2010 Her Majesty the Queen in Right of Canada"
        },
        "links": [
            {
                "rel": "canonical",
                "href": "https://example.org/data",
                "type": "WWW:LINK",
                "title": "my waf"
            },
            {
                "rel": "service",
                "href": "https://example.org/wms",
                "type": "OGC:WMS",
                "title": "roads"
            }
        ],
        "time": {
            "interval": [
                "1950-07-31",
                None
            ],
            "resolution": "P1Y"
        }
    }
