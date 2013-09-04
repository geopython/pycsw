#!/bin/bash

# Publish website to live

if [ $# -ne 1 ]; then
cat <<END
Usage: `basename $0` <ssh-server-username>
END
  exit 1
fi

SITE=_site
REMOTE_HOST=demo.pycsw.org
REMOTE_PATH=/osgeo/pycsw/pycsw-web

find $SITE -type f -exec chmod 664 {} +
find $SITE -type d -exec chmod 775 {} +

scp -r $SITE/* $1@$REMOTE_HOST:$REMOTE_PATH
