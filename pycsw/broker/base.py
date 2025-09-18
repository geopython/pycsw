# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2025 Tom Kralidis
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

import logging
import random
from urllib.parse import urlparse

from pycsw.core.util import remove_url_auth

LOGGER = logging.getLogger(__name__)


class BasePubSubClient:
    """Base Pub/Sub client"""

    def __init__(self, publisher_def: dict):
        """
        Initialize object

        :param publisher_def: publisher definition

        :returns: pycsw.broker.base.BasePubSubClient
        """

        self.type = None
        self.client_id = f'pycsw-pubsub-{random.randint(0, 1000)}'

        self.show_link = publisher_def.get('show_link', True)
        self.broker = publisher_def['url']
        self.broker_url = urlparse(publisher_def['url'])
        self.broker_safe_url = remove_url_auth(self.broker)

    def connect(self) -> None:
        """
        Connect to a Pub/Sub broker

        :returns: None
        """

        raise NotImplementedError()

    def pub(self, channel: str, message: str) -> bool:
        """
        Publish a message to a broker/channel

        :param channel: `str` of channel
        :param message: `str` of message

        :returns: `bool` of publish result
        """

        raise NotImplementedError()

    def __repr__(self):
        return f'<BasePubSubClient> {self.broker_safe_url}'
