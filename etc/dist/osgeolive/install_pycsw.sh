#!/bin/sh
# Copyright (c) 2011 The Open Source Geospatial Foundation.
# Licensed under the GNU LGPL.
# 
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 2.1 of the License,
# or any later version.  This library is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY, without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details, either
# in the "LICENSE.LGPL.txt" file distributed with this software or at
# web page "http://www.fsf.org/licenses/lgpl.html".

# About:
# =====
# This script will install pycsw, an OGC CSW server implementation
# written in Python.
#   http://pycsw.org
#
# Running:
# =======
# sudo ./install_pycsw.sh
#
# Requires: Apache2, python-lxml, python-shapely and python-sqlalchemy


VERSION=1.2.0

echo "Installing pycsw $VERSION"

echo 'Installing dependencies ...'

# install dependencies
apt-get install --yes apache2 python-lxml python-sqlalchemy python-shapely python-pyproj

echo 'Installing pycsw ...'

add-apt-repository --yes ppa:gcpp-kalxas/ppa-tzotsos
apt-get update
apt-get install --yes pycsw

# live disc's username is "user"
USER_NAME=user
USER_HOME=/home/$USER_NAME

cp /usr/share/applications/pycsw.desktop "$USER_HOME/Desktop/"
chown "$USER_NAME:$USER_NAME" "$USER_HOME/Desktop/pycsw.desktop"

# Reload Apache
#/etc/init.d/apache2 force-reload


