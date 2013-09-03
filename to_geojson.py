# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#          Ryan Clark <ryan.clark@azgs.az.gov>
#
# Copyright (c) 2013 Tom Kralidis
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

import csv
import json
from StringIO import StringIO
from urllib2 import urlopen

def build_live_deployments_geojson():
    """Convert Live Deployments wiki page to GeoJSON for GitHub to render"""
    dep_url = 'https://raw.github.com/wiki/geopython/pycsw/Live-Deployments.md'
    geojson = { 'type': 'FeatureCollection', 'features': [] }

    # grab Markdown file of Live Deployments from GitHub
    content = urlopen(dep_url).read()

    # serialize as GeoJSON
    dep_reader = csv.reader(StringIO(content), delimiter='|')
    next(dep_reader)  # skip fields row
    next(dep_reader)  # skip dashed line row
    for row in dep_reader:
        xycoords = row[3].split(',')

        feature = {
            'type': 'Feature',
            'properties': {
                'url': '<a href="%s">%s</a>' % (row[2].strip(), row[1].strip())
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [ float(xycoords[1]), float(xycoords[0]) ] }
        }

        geojson['features'].append(feature)

    with open('live-deployments.geojson', 'w') as output_file:
        output_file.write(json.dumps(geojson))

if __name__ == '__main__':
    build_live_deployments_geojson()
