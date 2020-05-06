# =================================================================
#
# Authors: Massimo Di Stefano <epiesasha@me.com>
#
#
# Copyright (c) 2020 Massimo Di Stefano
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
#
# =================================================================
FROM alpine:3.11
LABEL maintainer="massimods@met.no,aheimsbakk@met.no"

ENV PYCSW_CONFIG=/etc/pycsw/pycsw.cfg

EXPOSE 8000
COPY docker/min-apk /usr/local/bin/min-apk

RUN apk add binutils \
  && min-apk \
    bash \
    ca-certificates \
    geos \
    libpq \
    libxml2 \
    libxslt \
    proj \
    proj-util \
    python3 \
    sqlite \
    wget \
  && apk del binutils

COPY \
  requirements-standalone.txt \
  requirements-pg.txt \
  requirements-dev.txt \
  requirements.txt \
  ./

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
  && pip3 install gunicorn \
  && pip3 install --requirement requirements.txt \
  && pip3 install --requirement requirements-standalone.txt \
  && pip3 install --requirement requirements-pg.txt \
  && apk del .build-deps

COPY pycsw pycsw/
COPY bin bin/
COPY setup.py .
COPY MANIFEST.in .
COPY VERSION.txt .
COPY README.rst .

RUN pip3 install ./

COPY tests tests/

ADD docker/pycsw.cfg ${PYCSW_CONFIG}
ADD docker/entrypoint.py /usr/local/bin/entrypoint.py

RUN adduser -D -u 1000 pycsw \
  && mkdir -p /etc/pycsw \
  && mkdir /var/lib/pycsw \
  && cp -r tests /home/pycsw \
  && chown pycsw:pycsw /var/lib/pycsw \
  && chown -R pycsw:pycsw /home/pycsw/* \
  && rm -rf /usr/lib/python3*/*/tests \
  && rm -rf /usr/lib/python3*/ensurepip \
  && rm -rf /usr/lib/python3*/idlelib \
  && rm -f /usr/lib/python3*/distutils/command/*exe \
  && rm -rf /usr/share/man/* \
  && find /usr/lib -name  "*.pyc" -o -name "*.pyo" -delete

WORKDIR /home/pycsw

EXPOSE 8000

USER pycsw

ENTRYPOINT [ "python3", "/usr/local/bin/entrypoint.py” ]
