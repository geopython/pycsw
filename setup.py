# -*- coding: iso-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2012 Tom Kralidis
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
        dir = os.path.join(path, item)
        if is_package( dir ):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = dir
            packages.update(find_packages(dir, module_name))
    return packages

def find_packages_xsd(location='.'):
    """
    Figure out which packages need to be specified as package_data
    keys (the ones with XML Schema documents
    """
    packages = []
    for root, dirs, files in os.walk(location):
        if 'schemas' in dirs:  # include as a package_data key
            packages.append(root.replace(os.sep, '.').replace('..',''))
    return packages

def get_package_data(location='.', forced_dir=None):
    """Generate package_data dict"""
    package_data = {}
    for p in location:
        # turn package identifier into filepath
        filepath = p.replace('.', os.sep)
        if forced_dir is not None:  # force os.walk to traverse subdir
            filepath = '%s%sschemas' % (filepath, os.sep)
        for root, dirs, files in os.walk(filepath):
            if len(files) > 0:
                # find all the XML Schema documents
                xsds = filter(lambda x: x.find('.xsd') != -1, files)
                if len(xsds) > 0:
                    if not package_data.has_key(p):  # set key
                        package_data[p] = []
                    for x in xsds:  # add filename to list
                        root2 = root.replace(filepath, '')
                        if forced_dir is not None:
                            filename = 'schemas%s%s%s%s' % (os.sep, os.sep.join(root2.split(os.sep)[1:]), os.sep, x)
                        else:
                            filename = '%s%s%s' % (os.sep.join(root2.split(os.sep)[1:]), os.sep, x)
                        package_data[p].append(filename)
    return package_data

# ensure a fresh MANIFEST file is generated
if (os.path.exists('MANIFEST')):
    os.unlink('MANIFEST')

# set setup.packages
packages = find_packages('.').keys()

# get package_data.keys()
package_data_xsd = find_packages_xsd('pycsw')

# Because package 'pycsw' contains all other packages,
# process it last, so that it doesn't set it's package_data
# files to one already set in other packages
root_package = package_data_xsd.pop(0)

# set package_data
package_data = get_package_data(package_data_xsd)

# update package_data for pycsw package
package_data.update(get_package_data([root_package], 'schemas'))

# set the dependencies
# GeoNode and OpenDataCatalog do not require SQLAlchemy
install_requires= [
    'lxml>=2.2.3',
    'Shapely>=1.2.15',
    'pyproj>=1.8.9',
    'OWSLib>=0.5.1'
]

setup(name='pycsw',
    version=pycsw.__version__,
    description='pycsw is an OGC CSW server implementation written in Python',
    long_description=open('README.txt').read(),
    license='MIT',
    platforms='all',
    keywords='pycsw csw catalogue catalog metadata discovery search ogc iso fgdc dif ebrim inspire',
    author='Tom Kralidis',
    author_email='tomkralidis@hotmail.com',
    maintainer='Tom Kralidis',
    maintainer_email='tomkralidis@hotmail.com',
    url='http://pycsw.org/',
    install_requires=install_requires,
    packages=packages,
    package_data=package_data,
    scripts=[os.path.join('sbin', 'pycsw-admin.py')],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: GIS',
        ],
)
