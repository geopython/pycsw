#!/bin/bash

LOCAL_PATH=build/html/en
REMOTE_HOST=pycsw.org
REMOTE_PATH=/osgeo/pycsw/pycsw-web

if [ $# -ne 1 ]
then
    echo "Usage: $0 <OSGeo userid>"
    exit 1
fi

# change privs to be group writeable
chmod -R g+w $LOCAL_PATH

# copy documentation
scp -r $LOCAL_PATH/* $1@$REMOTE_HOST:$REMOTE_PATH
