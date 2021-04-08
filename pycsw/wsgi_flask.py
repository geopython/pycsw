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

from flask import Flask, Blueprint, make_response, request

from pycsw.ogc.api.records import API
from pycsw.ogc.api.util import STATIC
from pycsw.wsgi import application_dispatcher

PYCSW_CONFIG = os.environ.get('PYCSW_CONFIG')

if PYCSW_CONFIG is None:
    raise RuntimeError('PYCSW_CONFIG environment variable not set')

api_ = API(PYCSW_CONFIG)

APP = Flask(__name__, static_folder=STATIC, static_url_path='/static')
APP.url_map.strict_slashes = False

BLUEPRINT = Blueprint('pycsw', __name__, static_folder=STATIC,
                      static_url_path='/static')

APP.config['JSONIFY_PRETTYPRINT_REGULAR'] = api_.config['server'].get(
    'pretty_print', True)


def get_response(result: tuple):
    """
    Creates a Flask Response object and updates matching headers.

    :param result:  The result of the API call.
                    This should be a tuple of (headers, status, content).
    :returns:       A Response instance.
    """

    headers, status, content = result
    response = make_response(content, status)

    if headers:
        response.headers = headers
    return response


@BLUEPRINT.route('/')
def landing_page():
    """
    OGC API landing page endpoint

    :returns: HTTP response
    """

    return get_response(api_.landing_page(dict(request.headers), request.args))


@BLUEPRINT.route('/openapi')
def openapi():
    """
    OGC API OpenAPI document endpoint

    :returns: HTTP response
    """

    return get_response(api_.openapi(dict(request.headers), request.args))


@BLUEPRINT.route('/conformance')
def conformance():
    """
    OGC API conformance endpoint

    :returns: HTTP response
    """

    return get_response(api_.conformance(dict(request.headers), request.args))


@BLUEPRINT.route('/collections')
def collections():
    """
    OGC API collections endpoint

    :returns: HTTP response
    """

    return get_response(api_.collections(dict(request.headers), request.args))


@BLUEPRINT.route('/collections/metadata:main')
def collection():
    """
    OGC API collection endpoint

    :returns: HTTP response
    """

    return get_response(api_.collections(dict(request.headers),
                        request.args, True))


@BLUEPRINT.route('/collections/metadata:main/queryables')
def queryables():
    """
    OGC API collection queryables endpoint

    :returns: HTTP response
    """

    return get_response(api_.queryables(dict(request.headers), request.args))


@BLUEPRINT.route('/collections/metadata:main/items')
def items():
    """
    OGC API collection items endpoint

    :returns: HTTP response
    """

    return get_response(api_.items(dict(request.headers), request.args))


@BLUEPRINT.route('/collections/metadata:main/items/<item>')
def item(item=None):
    """
    OGC API collection items endpoint

    :param item: item identifier

    :returns: HTTP response
    """

    return get_response(api_.item(dict(request.headers), request.args, item))


@BLUEPRINT.route('/csw', methods=['GET', 'POST'])
def csw():
    """
    CSW endpoint

    :returns: HTTP response
    """

    request.environ['PYCSW_IS_CSW'] = True
    status, headers, content = application_dispatcher(request.environ)

    return get_response((headers, status, content))


APP.register_blueprint(BLUEPRINT)

if __name__ == '__main__':
    APP.run(debug=True, host='0.0.0.0', port=8000)
