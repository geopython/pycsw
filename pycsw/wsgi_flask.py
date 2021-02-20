# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2021 Tom Kralidis
# Copyright (c) 2021 Angelos Tzotsos
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

import os
from flask import Flask, Blueprint, make_response, request, send_from_directory
from pycsw import server
from pycsw.ogc.api.records import API

CONFIG = None

api_ = API(CONFIG)

STATIC_FOLDER = 'static'
if 'templates' in CONFIG['server']:
    STATIC_FOLDER = CONFIG['server']['templates'].get('static', 'static')

APP = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/static')
APP.url_map.strict_slashes = False

BLUEPRINT = Blueprint('pycsw', __name__, static_folder=STATIC_FOLDER)

@BLUEPRINT.route('/')
def landing_page():
    """
    OGC API landing page endpoint

    :returns: HTTP response
    """
    headers, status_code, content = api_.landing_page(
        request.headers, request.args)

    response = make_response(content, status_code)

    if headers:
        response.headers = headers

    return response

@BLUEPRINT.route('/csw')
def csw():
    """
    CSW endpoint

    :returns: HTTP response
    """
    headers, status_code, content = api_.landing_page(
        request.headers, request.args)

    response = make_response(content, status_code)

    if headers:
        response.headers = headers

    return response

@BLUEPRINT.route('/openapi')
def openapi():
    """
    OpenAPI endpoint

    :returns: HTTP response
    """
    # with open(os.environ.get('PYCSW_OPENAPI'), encoding='utf8') as ff:
        # openapi = yaml_load(ff)

    headers, status_code, content = api_.openapi(request.headers, request.args,
                                                 openapi)

    response = make_response(content, status_code)

    if headers:
        response.headers = headers

    return response


@BLUEPRINT.route('/conformance')
def conformance():
    """
    OGC API conformance endpoint

    :returns: HTTP response
    """

    headers, status_code, content = api_.conformance(request.headers,
                                                     request.args)

    response = make_response(content, status_code)

    if headers:
        response.headers = headers

    return response


@BLUEPRINT.route('/collections')
@BLUEPRINT.route('/collections/<collection_id>')
def collections(collection_id=None):
    """
    OGC API collections endpoint

    :param collection_id: collection identifier

    :returns: HTTP response
    """

    headers, status_code, content = api_.describe_collections(
        request.headers, request.args, collection_id)

    response = make_response(content, status_code)

    if headers:
        response.headers = headers

    return response


@BLUEPRINT.route('/collections/<collection_id>/queryables')
def collection_queryables(collection_id=None):
    """
    OGC API collections querybles endpoint

    :param collection_id: collection identifier

    :returns: HTTP response
    """

    headers, status_code, content = api_.get_collection_queryables(
        request.headers, request.args, collection_id)

    response = make_response(content, status_code)

    if headers:
        response.headers = headers

    return response


@BLUEPRINT.route('/collections/<collection_id>/items')
@BLUEPRINT.route('/collections/<collection_id>/items/<item_id>')
def collection_items(collection_id, item_id=None):
    """
    OGC API collections items endpoint

    :param collection_id: collection identifier
    :param item_id: item identifier

    :returns: HTTP response
    """

    if item_id is None:
        headers, status_code, content = api_.get_collection_items(
            request.headers, request.args, collection_id)
    else:
        headers, status_code, content = api_.get_collection_item(
            request.headers, request.args, collection_id, item_id)

    response = make_response(content, status_code)

    if headers:
        response.headers = headers

    return response


APP.register_blueprint(BLUEPRINT)

if __name__ == '__main__':  # run locally, for testing
    # setup_logger(CONFIG['logging'])
    APP.run(debug=True, host=api_.config['server']['bind']['host'],
            port=api_.config['server']['bind']['port'])
