# =================================================================
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
# Authors: Massimo Di Stefano <epiesasha@me.com>
# Authors: Tom Kralidis <tomkralidis@gmail.com>
# Authors: Angelos Tzotsos <gcpp.kalxas@gmail.com>
#
# Contributors: Arnulf Heimsbakk <aheimsbakk@met.no>
#               Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2020 Ricardo Garcia Silva
# Copyright (c) 2020 Massimo Di Stefano
# Copyright (c) 2025 Tom Kralidis
# Copyright (c) 2024 Angelos Tzotsos
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

FROM python:3.12-slim-bookworm
LABEL maintainer="massimods@met.no,aheimsbakk@met.no,tommkralidis@gmail.com"

# Build arguments
# add "--build-arg BUILD_DEV_IMAGE=true" to Docker build command when building with test/doc tools

ARG BUILD_DEV_IMAGE="false"

RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends ca-certificates python3-setuptools && \
    rm -rf /var/lib/apt/lists/*

RUN adduser --uid 1000 --gecos '' --disabled-password pycsw

ENV PYCSW_CONFIG=/etc/pycsw/pycsw.yml

WORKDIR /home/pycsw/pycsw

RUN chown --recursive pycsw:pycsw .

# initially copy only the requirements files
COPY --chown=pycsw \
    requirements.txt \
    requirements-standalone.txt \
    requirements-dev.txt \
    ./

RUN python3 -m venv /venv && \
    /venv/bin/pip3 install -U pip setuptools && \
    /venv/bin/pip3 install \
    --requirement requirements.txt \
    --requirement requirements-standalone.txt \
    psycopg2-binary gunicorn \
    && if [ "$BUILD_DEV_IMAGE" = "true" ] ; then /venv/bin/pip3 install -r requirements-dev.txt; fi

COPY --chown=pycsw . .

COPY docker/pycsw.yml ${PYCSW_CONFIG}
COPY docker/entrypoint.py /usr/local/bin/entrypoint.py

RUN pip install -e . --config-settings editable_mode=strict

WORKDIR /home/pycsw

EXPOSE 8000

USER pycsw

ENTRYPOINT [ "/venv/bin/python3", "/usr/local/bin/entrypoint.py" ]
