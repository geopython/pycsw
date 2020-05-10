# =================================================================
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
# Authors: Massimo Di Stefano <epiesasha@me.com>
#
# Contributors: Arnulf Heimsbakk <aheimsbakk@met.no>
#               Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2020 Ricardo Garcia Silva
# Copyright (c) 2020 Massimo Di Stefano
#
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

FROM python:3.8-slim-buster
LABEL maintainer="massimods@met.no,aheimsbakk@met.no"

RUN apt-get update && apt-get install --yes \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --uid 1000 --gecos '' --disabled-password pycsw

WORKDIR /home/pycsw/pycsw

RUN chown --recursive pycsw:pycsw .

# initially copy only the requirements files
COPY --chown=pycsw \
    requirements.txt \
    requirements-standalone.txt \
    ./

RUN python3 -m pip install \
    --requirement requirements.txt \
    --requirement requirements-standalone.txt \
    psycopg2-binary \
    gunicorn

COPY --chown=pycsw . .

RUN python3 -m pip install --editable .

WORKDIR /home/pycsw

EXPOSE 8000

USER pycsw
ENV PYCSW_CONFIG=/home/pycsw/pycsw/docker/pycsw.cfg

ENTRYPOINT [ "python3", "/home/pycsw/pycsw/docker/entrypoint.py" ]
