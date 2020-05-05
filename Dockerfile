# =================================================================
#
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#          Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2017 Ricardo Garcia Silva
# Copyright (c) 2020 Tom Kralidis
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

FROM debian:bullseye-slim

ENV DEB_PACKAGES="python3 python3-dev python3-pip libpq-dev libxslt-dev libxml2-dev libgeos-dev"

RUN apt-get update \
    && apt-get install --no-install-recommends -y ${DEB_PACKAGES}

RUN useradd -ms /bin/bash pycsw

WORKDIR /tmp/pycsw

COPY \
  requirements-standalone.txt \
  requirements-pg.txt \
  requirements-dev.txt \
  requirements.txt \
  ./

RUN pip3 install --upgrade pip setuptools \
  && pip3 install --requirement requirements.txt \
  && pip3 install --requirement requirements-standalone.txt \
  && pip3 install --requirement requirements-pg.txt \
  && pip3 install gunicorn

COPY pycsw pycsw/
COPY bin bin/
COPY setup.py .
COPY MANIFEST.in .
COPY VERSION.txt .
COPY README.rst .

RUN pip3 install .

COPY tests tests/
COPY docker docker/

ENV PYCSW_CONFIG=/etc/pycsw/pycsw.cfg

RUN mkdir /etc/pycsw \
  && mv docker/pycsw.cfg ${PYCSW_CONFIG} \
  && mkdir /var/lib/pycsw \
  && chown pycsw:pycsw /var/lib/pycsw \
  && cp docker/entrypoint.py /usr/local/bin/entrypoint.py \
  && chmod a+x /usr/local/bin/entrypoint.py \
  && cp -r tests /home/pycsw \
  && cp requirements.txt /home/pycsw \
  && cp requirements-standalone.txt /home/pycsw \
  && cp requirements-pg.txt /home/pycsw \
  && cp requirements-dev.txt /home/pycsw \
  && chown -R pycsw:pycsw /home/pycsw/* \
  && rm -rf *

WORKDIR /home/pycsw

USER pycsw

EXPOSE 8000

ENTRYPOINT [\
  "python3", \
  "/usr/local/bin/entrypoint.py" \
]
