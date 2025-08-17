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
# Copyright (c) 2020 Tom Kralidis
# Copyright (c) 2020 Angelos Tzotsos
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

FROM python:3.8-slim
LABEL maintainer="massimods@met.no,aheimsbakk@met.no,tommkralidis@gmail.com"

RUN apt-get update && apt-get install --yes \
    ca-certificates \
    build-essential \ 
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt \
    requirements-standalone.txt \
    ./

RUN python3 -m pip install \
    --requirement requirements.txt \
    --requirement requirements-standalone.txt \
    psycopg2-binary

ADD uwsgi.ini /settings/uwsgi.default.ini

ENV \
    # WSGI parameters
    PYCSW_WSGI_PROCESSES=6 \
    PYCSW_WSGI_THREADS=10 \
    PYCSW_CONFIG=/etc/pycsw/pycsw.cfg

WORKDIR /home/pycsw

COPY . .
COPY docker/pycsw.cfg ${PYCSW_CONFIG}
COPY docker/entrypoint.py /usr/local/bin/entrypoint.py

# fix cert permissions in openshift
RUN mkdir /.postgresql && chmod -R 777 /.postgresql

RUN python3 -m pip install --editable .

COPY docker/uwsgi-start.sh /usr/local/bin/uwsgi-start.sh
RUN chgrp -R 0 /home/pycsw /settings /usr/local/bin/uwsgi-start.sh && \
    chmod -R g=u /home/pycsw /settings /usr/local/bin/uwsgi-start.sh

EXPOSE 8000

RUN useradd -ms /bin/bash pycsw && usermod -a -G root pycsw
USER pycsw

ENTRYPOINT [ "/usr/local/bin/uwsgi-start.sh" ]
