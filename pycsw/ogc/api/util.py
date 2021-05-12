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

import base64
from datetime import date, datetime, time
from decimal import Decimal
import json
import logging
import mimetypes
import os
import re

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
import yaml

from pycsw import __version__

LOGGER = logging.getLogger(__name__)

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

TEMPLATES = '{}{}templates'.format(os.path.dirname(
    os.path.realpath(__file__)), os.sep)

STATIC = '{}/static'.format(TEMPLATES)

mimetypes.add_type('text/plain', '.yaml')
mimetypes.add_type('text/plain', '.yml')


def get_typed_value(value):
    """
    Derive true type from data value
    :param value: value
    :returns: value as a native Python data type
    """

    try:
        if '.' in value:  # float?
            value2 = float(value)
        elif len(value) > 1 and value.startswith('0'):
            value2 = value
        else:  # int?
            value2 = int(value)
    except ValueError:  # string (default)?
        value2 = value

    return value2


def json_serial(obj):
    """
    helper function to convert to JSON non-default
    types (source: https://stackoverflow.com/a/22238613)
    :param obj: `object` to be evaluated
    :returns: JSON non-default type to `str`
    """

    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    elif isinstance(obj, bytes):
        try:
            LOGGER.debug('Returning as UTF-8 decoded bytes')
            return obj.decode('utf-8')
        except UnicodeDecodeError:
            LOGGER.debug('Returning as base64 encoded JSON object')
            return base64.b64encode(obj)
    elif isinstance(obj, Decimal):
        return float(obj)

    msg = '{} type {} not serializable'.format(obj, type(obj))
    LOGGER.error(msg)
    raise TypeError(msg)


def match_env_var(value):
    path_matcher = re.compile(r'.*\$\{([^}^{]+)\}.*')
    env_var = path_matcher.match(value).group(1)
    if env_var not in os.environ:
        raise EnvironmentError('Undefined environment variable in config')

    return env_var


def yaml_load(fh):
    """
    serializes a YAML files into a pyyaml object

    :param fh: file handle

    :returns: `dict` representation of YAML
    """

    # support environment variables in config
    # https://stackoverflow.com/a/55301129
    path_matcher = re.compile(r'.*\$\{([^}^{]+)\}.*')

    def path_constructor(loader, node):
        env_var = path_matcher.match(node.value).group(1)
        if env_var not in os.environ:
            raise EnvironmentError('Undefined environment variable in config')
        return get_typed_value(os.path.expandvars(node.value))

    class EnvVarLoader(yaml.SafeLoader):
        pass

    EnvVarLoader.add_implicit_resolver('!path', path_matcher, None)
    EnvVarLoader.add_constructor('!path', path_constructor)

    return yaml.load(fh, Loader=EnvVarLoader)


def to_json(dict_, pretty=False):
    """
    Serialize dict to json

    :param dict_: `dict` of JSON representation
    :param pretty: `bool` of whether to prettify JSON (default is `False`)

    :returns: JSON string representation
    """

    if pretty:
        indent = 4
    else:
        indent = None

    return json.dumps(dict_, default=json_serial,
                      indent=indent)


def render_j2_template(config, template, data):
    """
    render Jinja2 template

    :param config: dict of configuration
    :param template: template (relative path)
    :param data: dict of data

    :returns: string of rendered template
    """

    custom_templates = False
    try:
        templates_path = config['server']['templates']['path']
        env = Environment(loader=FileSystemLoader(templates_path))
        custom_templates = True
        LOGGER.debug('using custom templates: {}'.format(templates_path))
    except (KeyError, TypeError):
        env = Environment(loader=FileSystemLoader(TEMPLATES))
        LOGGER.debug('using default templates: {}'.format(TEMPLATES))

    env.filters['to_json'] = to_json
    env.globals.update(to_json=to_json)

    try:
        template = env.get_template(template)
    except TemplateNotFound as err:
        if custom_templates:
            LOGGER.debug(err)
            LOGGER.debug('Custom template not found; using default')
            env = Environment(loader=FileSystemLoader(TEMPLATES))
            template = env.get_template(template)
        else:
            raise

    return template.render(config=config, data=data, version=__version__)
