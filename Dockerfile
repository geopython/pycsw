# =================================================================
#
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
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
#
# Adapted from pycsw official Dockerfile
#
# Contributors:
#   Massimo Di Stefano
#   Arnulf Heimsbakk
#
# Note in the instruction above I added some extra packages:
# git - to clone pycsw repo or install with pip directly form github
# bash - for interactive docker session
# postgresql-dev, psycopg2 - for postgres backend
# parmap - to easy parallelize routines like mmd2iso
# xmltodict - pythonic way to work on xml

FROM alpine:3.11
LABEL maintainer="massimods@met.no,aheimsbakk@met.no"

ENV PYCSW_CONFIG=/etc/pycsw/pycsw.cfg
# ENV PYCSW_VERSION=2.4.2

EXPOSE 8000
COPY docker/min-apk /usr/local/bin/min-apk
COPY docker/clean-pyc-files /usr/local/bin/clean-pyc-files

RUN min-apk \
    bash \
    ca-certificates \
    geos \
    git \
    libpq \
    libxml2 \
    libxslt \
    proj \
    proj-util \
    python3 \
    sqlite \
    wget

RUN apk add --no-cache --virtual .build-deps \
    build-base \
    geos-dev \
    libxml2-dev \
    libxslt-dev \
    postgresql-dev \
    proj-dev \
    python3-dev \
  && pip3 install --upgrade pip setuptools \
  && pip3 install wheel \
  && pip3 install \
    gunicorn \
    lxml \
    parmap \
    psycopg2 \
    sqlalchemy \
    xmltodict \
    pyproj \
  && apk del .build-deps

# this line goes before removing the apk .build-deps
# && pip3 install pycsw==${PYCSW_VERSION} \

# We are installing pycsw from pip
# I leave the lines below commented
# for when we want to build from a pycsw repo (or fork)
#

COPY \
  requirements-standalone.txt \
  requirements-pg.txt \
  requirements-dev.txt \
  requirements.txt \
  ./

RUN pip3 install --upgrade pip setuptools \
  && pip3 install --requirement requirements.txt \
  && pip3 install --requirement requirements-standalone.txt \
  && pip3 install --requirement requirements-pg.txt

COPY pycsw pycsw/
COPY bin bin/
COPY setup.py .
COPY MANIFEST.in .
COPY VERSION.txt .
COPY README.rst .

RUN pip3 install .

ADD docker/pycsw.cfg ${PYCSW_CONFIG}
ADD docker/entrypoint.py /usr/local/bin/entrypoint.py

RUN adduser -D -u 1000 pycsw \
  && mkdir -p /etc/pycsw \
  && mkdir /var/lib/pycsw \
  && chown pycsw:pycsw /var/lib/pycsw \
  && rm -rf /usr/lib/python3*/*/tests \
  && rm -rf /usr/lib/python3*/ensurepip \
  && rm -rf /usr/lib/python3*/idlelib \
  && rm -f /usr/lib/python3*/distutils/command/*exe \
  && rm -rf /usr/share/man/* \
  && clean-pyc-files /usr/lib/python3*

COPY tests /home/pycsw
RUN chown -R pycsw:pycsw /home/pycsw/

WORKDIR /home/pycsw

USER pycsw

ENTRYPOINT [ "python3", "/usr/local/bin/entrypoint.py" ]