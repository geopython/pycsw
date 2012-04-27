#!/bin/bash

if [ $# -ne 1 ]
then
    echo "Usage: $0 <OSGeo userid>"
    exit 1
fi

scp -rp build/html/en/* $1@projects.osgeo.osuosl.org:/osgeo/pycsw/pycsw-web
