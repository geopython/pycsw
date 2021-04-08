# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
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

# sample mappings.py
#
# use this file to bind to an existing alternate metadata database model
#
# steps:
# - update the 'mappings' dict to the column names of your existing database
# - set repository.mappings to the location of this file
# - if new fields are needed add them with the 'pycsw' prefix (to avoid collision with actual profile queryables)

MD_CORE_MODEL = {
    'typename': 'pycsw:CoreMetadata',
    'outputschema': 'http://pycsw.org/metadata',
    'mappings': {
        # Needed fot PYCSW
        'pycsw:Identifier': 'identifier',
        'pycsw:Typename': 'typename',
        'pycsw:Schema': 'schema',
        'pycsw:MdSource': 'mdsource',
        'pycsw:InsertDate': 'insert_date',
        'pycsw:XML': 'xml',
        'pycsw:AnyText': 'anytext',
        'pycsw:BoundingBox': 'wkt_geometry',

        'pycsw:Title': 'title',
        'pycsw:AlternateTitle': 'title',
        'pycsw:Creator': 'producer_name',
        'pycsw:Abstract': 'description',
        'pycsw:Publisher': 'producer_name',
        'pycsw:Contributor': 'producer_name',
        'pycsw:Modified': 'creation_date',
        'pycsw:Date': 'creation_date',
        'pycsw:Type': 'type',
        'pycsw:Format': 'type',
        'pycsw:Keywords': 'keywords',
        'pycsw:Identifier': 'identifier',
        'pycsw:Source': 'producer_name',
        'pycsw:AccessConstraints': 'classification',
        'pycsw:CRS': 'srs',
        'pycsw:BoundingBox': 'wkt_geometry',
        'pycsw:AnyText': 'anytext',

        'pycsw:Relation': '',
        'pycsw:Language': '',
        'pycsw:Keywords': '',
        'pycsw:TopicCategory': '',

        # Added for mc3d
        'pycsw:projectName': 'project_name',
        'pycsw:Identifier': 'identifier',
        'pycsw:Title': 'title',
        'pycsw:version': 'version',
        'pycsw:centroid': 'centroid',
        'pycsw:footprint': 'footprint',
        'pycsw:BoundingBox': 'wkt_geometry',
        'pycsw:Classification': 'classification',
        'pycsw:TempExtent_begin': 'time_begin',
        'pycsw:TempExtent_end': 'time_end',
        'pycsw:sensorType': 'sensor_type',
        'pycsw:region': 'region',
        'pycsw:nominalResolution': 'nominal_resolution',
        'pycsw:accuracyLE90': 'accuracy_le_90',
        'pycsw:horizontalAccuracyCE90': 'horizontal_accuracy_ce_90',
        'pycsw:relativeAccuracyLE90': 'relative_accuracy_le_90',
        'pycsw:CreationDate': 'creation_date',
        'pycsw:Creator': 'producer_name',
        'pycsw:CRS': 'srs',
        'pycsw:validationDate': 'validation_date',
        'pycsw:estimatedPrecision': 'estimated_precision',
        'pycsw:measuredPrecision': 'measured_precision',
        'pycsw:Abstract': 'description',
        'pycsw:Links': 'links',
        'pycsw:Type': 'type', 

        # Added for mc-raster 
        'pycsw:Source': 'source',
        'pycsw:SourceName': 'sourceName',
        'pycsw:UpdateDate': 'updateDate',
        'pycsw:Resolution': 'resolution',
        'pycsw:Ep90': 'ep90',
        'pycsw:sensorType': 'sensorType',
        'pycsw:Rms': 'rms',
        'pycsw:Scale': 'scale',
        'pycsw:Abstract': 'description',
        'pycsw:BoundingBox': 'wkt_geometry',
        'pycsw:Identifier': 'identifier',
        'pycsw:version': 'version',
    }
}
