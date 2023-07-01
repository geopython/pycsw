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
