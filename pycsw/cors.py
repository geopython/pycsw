import os
from pycsw.wsgi import application
from wsgicors import CORS

if(os.environ.get('CORS_ENABLED', 'false').lower() == 'true'):
    allowed_headers = os.environ.get('CORS_ALLOWED_HEADERS')
    allowed_origin = os.environ.get('CORS_ALLOWED_ORIGIN')
    application = CORS(application, headers=allowed_headers, methods="GET,POST,OPTIONS", origin=allowed_origin)
