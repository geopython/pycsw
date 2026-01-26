# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2026 Tom Kralidis
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

from datetime import datetime, UTC
import json
import uuid
from typing import Union


def publish_message(pubsub_client, action: str, url: str,
                    collection: str = None, item: str = None,
                    data: str = None) -> bool:
    """
    Publish broker message

    :param pubsub_client: `paho.mqtt.client.Client` instance
    :param url: `str` of server base URL
    :param action: `str` of action trigger name (create, update, delete)
    :param collection: `str` of collection identifier
    :param item: `str` of item identifier
    :param data: `str` of data payload

    :returns: `bool` of whether message publishing was successful
    """

    if pubsub_client.channel is not None:
        channel = f'{pubsub_client.channel}/collections/{collection}'
    else:
        channel = f'collections/{collection}'

    type_ = f'org.ogc.api.collection.item.{action}'

    if action in ['create', 'update']:
        media_type = 'application/geo+json'
        data_ = data
    elif action == 'delete':
        media_type = 'text/plain'
        data_ = item

    message = generate_ogc_cloudevent(type_, media_type, url, channel, data_)

    pubsub_client.connect()
    pubsub_client.pub(channel, json.dumps(message))


def generate_ogc_cloudevent(type_: str, media_type: str, source: str,
                            subject: str, data: Union[dict, str]) -> dict:
    """
    Generate WIS2 Monitoring Event Message of WCMP2 report

    :param type_: `str` of CloudEvents type
    :param source: `str` of source
    :param subject: `str` of subject
    :param media_type: `str` of media type
    :param data: `str` or `dict` of data

    :returns: `dict` of OGC CloudEvent payload
    """

    try:
        data2 = json.loads(data)
    except Exception:
        if isinstance(data, bytes):
            data2 = data.decode('utf-8')
        else:
            data2 = data

    message = {
        'specversion': '1.0',
        'type': type_,
        'source': source,
        'subject': subject,
        'id': str(uuid.uuid4()),
        'time': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'datacontenttype': media_type,
        # 'dataschema': 'TODO',
        'data': data2
    }

    return message
