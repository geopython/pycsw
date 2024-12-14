# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2024 Tom Kralidis
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
import sys

from flask import Flask, Blueprint, make_response, request

from pycsw.ogc.api.records import API
from pycsw.ogc.api.util import STATIC, yaml_load
from pycsw.stac.api import STACAPI
from pycsw.wsgi import application_dispatcher


APP = Flask(__name__, static_folder=STATIC, static_url_path='/static')
APP.url_map.strict_slashes = False

with open(os.getenv('PYCSW_CONFIG'), encoding='utf8') as fh:
    APP.config['PYCSW_CONFIG'] = yaml_load(fh)

BLUEPRINT = Blueprint('pycsw', __name__, static_folder=STATIC,
                      static_url_path='/static')

api_ = API(APP.config['PYCSW_CONFIG'])
with open(os.getenv('PYCSW_CONFIG'), encoding='utf8') as fh:
    stacapi = STACAPI(yaml_load(fh))


def get_api_type(urlpath):
    """
    Decorator to detect API type

    :param urlpath: URL path

    :returns: `str` of API typ
    """

    api_type = 'ogcapi-records'

    if 'stac' in urlpath:
        api_type = 'stac-api'

    return api_type


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
@BLUEPRINT.route('/stac')
def landing_page():
    """
    OGC API landing page endpoint

    :returns: HTTP response
    """

    if get_api_type(request.url_rule.rule) == 'stac-api':
        return get_response(stacapi.landing_page(dict(request.headers), request.args))  # noqa
    else:
        return get_response(api_.landing_page(dict(request.headers), request.args))


@BLUEPRINT.route('/openapi')
@BLUEPRINT.route('/stac/openapi')
def openapi():
    """
    OGC API OpenAPI document endpoint

    :returns: HTTP response
    """

    if get_api_type(request.url_rule.rule) == 'stac-api':
        return get_response(stacapi.openapi(dict(request.headers), request.args))
    else:
        return get_response(api_.openapi(dict(request.headers), request.args))


@BLUEPRINT.route('/conformance')
@BLUEPRINT.route('/stac/conformance')
def conformance():
    """
    OGC API conformance endpoint

    :returns: HTTP response
    """

    if get_api_type(request.url_rule.rule) == 'stac-api':
        return get_response(stacapi.conformance(dict(request.headers), request.args))
    else:
        return get_response(api_.conformance(dict(request.headers), request.args))


@BLUEPRINT.route('/collections')
@BLUEPRINT.route('/stac/collections')
def collections():
    """
    OGC API collections endpoint

    :returns: HTTP response
    """

    if get_api_type(request.url_rule.rule) == 'stac-api':
        return get_response(stacapi.collections(dict(request.headers), request.args))  # noqa
    else:
        return get_response(api_.collections(dict(request.headers), request.args))


@BLUEPRINT.route('/collections/<collection>')
@BLUEPRINT.route('/stac/collections/<collection>')
def collection(collection='metadata:main'):
    """
    OGC API collection endpoint

    :param collection: collection name

    :returns: HTTP response
    """

    if get_api_type(request.url_rule.rule) == 'stac-api':
        return get_response(stacapi.collection(dict(request.headers),
                            request.args, collection))
    else:
        return get_response(api_.collection(dict(request.headers),
                            request.args, collection))


@BLUEPRINT.route('/collections/<collection>/queryables')
@BLUEPRINT.route('/stac/queryables')
def queryables(collection='metadata:main'):
    """
    OGC API collection queryables endpoint

    :param collection: collection name

    :returns: HTTP response
    """

    if get_api_type(request.url_rule.rule) == 'stac-api':
        return get_response(stacapi.queryables(dict(request.headers), request.args,
                            collection))
    else:
        return get_response(api_.queryables(dict(request.headers), request.args,
                            collection))


@BLUEPRINT.route('/collections/<collection>/items', methods=['GET', 'POST'])
@BLUEPRINT.route('/stac/search', methods=['GET', 'POST'])
@BLUEPRINT.route('/stac/collections/<collection>/items', methods=['GET', 'POST'])
def items(collection='metadata:main'):
    """
    OGC API collection items endpoint
    STAC API items search endpoint

    :param collection: collection name

    :returns: HTTP response
    """

    if request.method == 'POST' and request.content_type not in [None, 'application/json']:  # noqa
        data = None
        if request.content_type == 'application/geo+json':  # JSON grammar
            data = request.get_json(silent=True)
        elif 'xml' in request.content_type:  # XML grammar
            data = request.data
        return get_response(api_.manage_collection_item(dict(request.headers),
                            'create', data=data))
    else:
        if get_api_type(request.url_rule.rule) == 'stac-api':
            return get_response(stacapi.items(dict(request.headers),
                                request.get_json(silent=True), dict(request.args),
                                collection))
        else:
            return get_response(api_.items(dict(request.headers),
                                request.get_json(silent=True), dict(request.args),
                                collection))


@BLUEPRINT.route('/collections/<collection>/items/<path:item>',
                 methods=['GET', 'PUT', 'DELETE'])
@BLUEPRINT.route('/stac/collections/<collection>/items/<item>')
def item(collection='metadata:main', item=None):
    """
    OGC API collection items endpoint

    :param collection: collection name
    :param item: item identifier

    :returns: HTTP response
    """

    if request.method == 'PUT':
        return get_response(
            api_.manage_collection_item(
                dict(request.headers), 'update', item,
                data=request.get_json(silent=True)))
    elif request.method == 'DELETE':
        return get_response(
            api_.manage_collection_item(dict(request.headers), 'delete', item))
    else:
        if get_api_type(request.url_rule.rule) == 'stac-api':
            return get_response(stacapi.item(dict(request.headers), request.args,
                                collection, item))
        else:
            return get_response(api_.item(dict(request.headers), request.args,
                                collection, item))


@BLUEPRINT.route('/csw', methods=['GET', 'POST'])
def csw():
    """
    CSW endpoint

    :returns: HTTP response
    """

    request.environ['PYCSW_IS_CSW'] = True
    status, headers, content = application_dispatcher(request.environ)

    return get_response((headers, status, content))


@BLUEPRINT.route('/opensearch', methods=['GET'])
def opensearch():
    """
    OpenSearch endpoint

    :returns: HTTP response
    """

    request.environ['PYCSW_IS_OPENSEARCH'] = True
    status, headers, content = application_dispatcher(request.environ)

    return get_response((headers, status, content))


@BLUEPRINT.route('/oaipmh', methods=['GET'])
def oaipmh():
    """
    OpenSearch endpoint

    :returns: HTTP response
    """

    request.environ['PYCSW_IS_OAIPMH'] = True
    status, headers, content = application_dispatcher(request.environ)

    return get_response((headers, status, content))


@BLUEPRINT.route('/sru', methods=['GET'])
def sru():
    """
    OpenSearch endpoint

    :returns: HTTP response
    """

    request.environ['PYCSW_IS_SRU'] = True
    status, headers, content = application_dispatcher(request.environ)

    return get_response((headers, status, content))


APP.register_blueprint(BLUEPRINT)

if __name__ == '__main__':
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    print(f'Serving on port {port}')
    APP.run(debug=True, host='0.0.0.0', port=port)
