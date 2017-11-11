# =================================================================
#
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2017 Ricardo Garcia Silva
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
FROM alpine:3.4

# There's bug in libxml2 v2.9.4 that prevents using an XMLParser with a schema
# file.
#
# https://bugzilla.gnome.org/show_bug.cgi?id=766834
#
# It seems to have been fixed upstream, but the fix has not been released into
# a new libxml2 version. As a workaround, we are sticking with the previous
# version, which works fine.
# This means that we need to use alpine's archives for version 3.1, which are
# the ones that contain the previous version of libxml2
#
# Also, for some unkwnon reason, alpine 3.1 version of libxml2 depends on
# python2. We'd rather use python3 for pycsw, so we install it too.
RUN echo 'http://dl-cdn.alpinelinux.org/alpine/v3.1/main' >> /etc/apk/repositories \
  && apk add --no-cache \
    build-base \
    ca-certificates \
    postgresql-dev \
    python3 \
    python3-dev \
    libpq \
    libxslt-dev \
    'libxml2<2.9.4' \
    'libxml2-dev<2.9.4' \
    wget \
  && apk add --no-cache \
    --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ \
    --allow-untrusted \
    geos \
    geos-dev

RUN adduser -D -u 1000 pycsw

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
