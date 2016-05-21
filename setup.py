# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2016 Tom Kralidis
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

import os
from distutils.core import setup
import pycsw


def is_package(path):
    """Decipher whether a filepath is a Python package"""
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py'))
    )


def find_packages(path, base=''):
    """Find all packages in path"""
    packages = {}
    for item in os.listdir(path):
        directory = os.path.join(path, item)
        if is_package(directory):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = directory
            packages.update(find_packages(directory, module_name))
    return packages


def find_packages_xsd(location='.'):
    """
    Figure out which packages need to be specified as package_data
    keys (the ones with XML Schema documents
    """
    packages = []
    for root, dirs, files in os.walk(location):
        if 'schemas' in dirs:  # include as a package_data key
            packages.append(root.replace(os.sep, '.').replace('..', ''))
    return packages


def get_package_data(location='.', forced_dir=None):
    """Generate package_data dict"""
    package_data = {}
    for ploc in location:
        # turn package identifier into filepath
        filepath = ploc.replace('.', os.sep)
        if forced_dir is not None:  # force os.walk to traverse subdir
            filepath = '%s%sschemas' % (filepath, os.sep)
        for root, dirs, files in os.walk(filepath):
            if len(files) > 0:
                # find all the XML Schema documents
                xsds = [x for x in files if x.find('.xsd') != -1]
                catalog_xml = [x for x in files if x.find('catalog.xml') != -1]
                xsds.extend(catalog_xml)
                if len(xsds) > 0:
                    if ploc not in package_data:  # set key
                        package_data[ploc] = []
                    for xsd in xsds:  # add filename to list
                        root2 = root.replace(filepath, '').split(os.sep)[1:]
                        pathstr = '%s%s%s' % (os.sep.join(root2), os.sep, xsd)
                        if forced_dir is not None:
                            filename = 'schemas%s%s' % (os.sep, pathstr)
                        else:
                            filename = pathstr
                        package_data[ploc].append(filename)
    return package_data

# ensure a fresh MANIFEST file is generated
if (os.path.exists('MANIFEST')):
    os.unlink('MANIFEST')

# set setup.packages
PACKAGES = list(find_packages('.').keys())

# get package_data.keys()
PACKAGE_DATA_XSD = find_packages_xsd('pycsw')

# Because package 'pycsw' contains all other packages,
# process it last, so that it doesn't set it's package_data
# files to one already set in other packages
ROOT_PACKAGE = PACKAGE_DATA_XSD.pop(0)

# set package_data
PACKAGE_DATA = get_package_data(PACKAGE_DATA_XSD)

# update package_data for pycsw package
PACKAGE_DATA.update(get_package_data([ROOT_PACKAGE], 'schemas'))

# set the dependencies
# GeoNode, HHypermap and OpenDataCatalog do not require SQLAlchemy
with open('requirements.txt') as f:
    INSTALL_REQUIRES = f.read().splitlines()

KEYWORDS = ('pycsw csw catalogue catalog metadata discovery search'
            ' ogc iso fgdc dif ebrim inspire')

DESCRIPTION = 'pycsw is an OGC CSW server implementation written in Python'

with open('README.txt') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='pycsw',
    version=pycsw.__version__,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    license='MIT',
    platforms='all',
    keywords=KEYWORDS,
    author='Tom Kralidis',
    author_email='tomkralidis@gmail.com',
    maintainer='Tom Kralidis',
    maintainer_email='tomkralidis@gmail.com',
    url='http://pycsw.org/',
    install_requires=INSTALL_REQUIRES,
    packages=PACKAGES,
    package_data=PACKAGE_DATA,
    scripts=[os.path.join('bin', 'pycsw-admin.py')],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: GIS',
    ]
)
