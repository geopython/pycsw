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
# This script will install pycsw

# Running:
# =======
# sudo ./install_pycsw.sh

# Requires: Apache2, python-lxml, python-shapely and python-sqlalchemy
#
# Uninstall:
# ============
# sudo rm /etc/apache2/conf.d/pycsw
# sudo rm -rf /var/www/pycsw*

VERSION=1.0.0

echo -n 'Installing pycsw $VERSION'

echo -n 'Installing dependencies ...'

# install dependencies
apt-get install apache2 python-lxml python-sqlalchemy python-shapely

# live disc's username is "user"
USER_NAME=user
USER_HOME=/home/$USER_NAME

WEB=/var/www

# package specific settings
PYCSW_HOME=$WEB/pycsw
PYCSW_TMP=/tmp/build_pycsw
PYCSW_APACHE_CONF=/etc/apache2/conf.d/pycsw

mkdir -p "$PYCSW_TMP"

echo -n 'Downloading package ...'

# Download pycsw LiveDVD tarball.
wget -N --progress=dot:mega "https://sourceforge.net/projects/pycsw/files/$VERSION/pycsw-$VERSION.tar.gz/download" \
     -O "$PYCSW_TMP/pycsw-$VERSION.tar.gz"

echo -n 'Extracting package ...'

# Uncompress pycsw LiveDVD tarball.
tar -zxvf "$PYCSW_TMP/pycsw-$VERSION.tar.gz" -C "$PYCSW_TMP"
mv "$PYCSW_TMP/pycsw-$VERSION" "$PYCSW_TMP/pycsw"
mv "$PYCSW_TMP/pycsw" $WEB

echo -n "Updating Apache configuration ..."
# Add pycsw apache configuration
cat << EOF > "$PYCSW_APACHE_CONF"

        <Directory $PYCSW_HOME>
	    Options FollowSymLinks +ExecCGI
	    Allow from all
	    AddHandler cgi-script .py
        </Directory>

EOF

echo -n "Generating configuration files ..."
# Add pycsw configuration files

cp $PYCSW_HOME/default-sample.cfg $PYCSW_HOME/default.cfg

echo -n "Done\n"

#Add Launch icon to desktop
if [ ! -e /usr/share/applications/pycsw.desktop ] ; then
   cat << EOF > /usr/share/applications/pycsw.desktop
[Desktop Entry]
Type=Application
Encoding=UTF-8
Name=pycsw
Comment=pycsw catalog server
Categories=Application;Education;Geography;
Exec=firefox http://localhost/pycsw/tester/index.html
Icon=/var/www/pycsw/docs/_static/pycsw-logo.png
Terminal=false
StartupNotify=false
Categories=Education;Geography;
EOF
fi
cp /usr/share/applications/pycsw.desktop "$USER_HOME/Desktop/"
chown "$USER_NAME:$USER_NAME" "$USER_HOME/Desktop/pycsw.desktop"

# Reload Apache
/etc/init.d/apache2 force-reload
