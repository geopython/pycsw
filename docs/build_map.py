# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
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
import os
from urllib2 import urlopen

def build_live_deployments_map():
    dep_url = 'https://raw.github.com/wiki/geopython/pycsw/Live-Deployments.md'
    dep_file = 'build%sLive-Deployments.md' % os.sep
    
    leaflet = '''
.. raw:: html
    
   <link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet-0.5/leaflet.css" />
   <!--[if lte IE 8]>
     <link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet-0.5/leaflet.ie.css" />
   <![endif]-->
   <script src="http://cdn.leafletjs.com/leaflet-0.5/leaflet.js"></script>
   <style type="text/css">#map { width: 530px; height: 300px; }</style>
   <div id="map"></div>
   <script type="text/javascript">
     var map = L.map('map').setView([10, 0], 1);
     var pycswIcon = L.icon({
         iconUrl: './_images/pycsw-logo.png',
         iconSize: [15, 15]
     });
     L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
         attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
     }).addTo(map);
'''
    # cache Markdown file of Live Deployments from GitHub
    if not os.path.exists(dep_file):
        content = urlopen(dep_url).read()
        with open(dep_file, 'w') as df:
            df.write(content)
    
    # serialize Leaflet marker objects
    with open(dep_file) as csvfile:
        count = 0
        dep_reader = csv.reader(csvfile, delimiter='|')
        next(dep_reader)  # skip fields row
        next(dep_reader)  # skip dashed line row
        for row in dep_reader:
            xy = row[3].split(',')
            leaflet = leaflet + '''
    var marker%s = L.marker([%s,%s], {icon: pycswIcon})
    marker%s.bindPopup('<a href="%s">%s</a>');
    marker%s.addTo(map);''' % \
           (count, xy[0], xy[1], count, row[2].strip(), row[1].strip(), count)
            count += 1
    
    leaflet += '</script>'
    return leaflet

if __name__ == '__main__':
    print build_live_deployments_map()
