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
        'pycsw:Links': 'links',
        'pycsw:Keywords': 'keywords',

        # Common profile fields
        'pycsw:Type': 'type',
        'pycsw:Classification': 'classification',
        'pycsw:AccessConstraints': 'classification',
        'pycsw:ProductId': 'product_id',
        'pycsw:Title': 'product_name',
        'pycsw:AlternateTitle': 'product_name',
        'pycsw:ProductVersion': 'product_version',
        'pycsw:ProductType': 'product_type',
        'pycsw:Abstract': 'description',
        'pycsw:CRS': 'srs',
        'pycsw:CRSName': 'srs_name',
        'pycsw:Creator': 'producer_name',
        'pycsw:Publisher': 'producer_name',
        'pycsw:Contributor': 'producer_name',
        'pycsw:CreationDate': 'creation_date',
        'pycsw:Date': 'creation_date',
        'pycsw:Format': 'type',
        'pycsw:Modified': 'update_date',
        'pycsw:UpdateDate': 'update_date',
        'pycsw:IngestionDate': 'ingestion_date',
        'pycsw:TempExtent_begin': 'source_start_date',
        'pycsw:TempExtent_end': 'source_end_date',
        'pycsw:Resolution': 'resolution',
        'pycsw:horizontalAccuracyCE90': 'horizontal_accuracy_ce_90',
        'pycsw:sensorType': 'sensor_type',
        'pycsw:Region': 'region',
        'pycsw:footprint': 'footprint_geojson',
        'pycsw:Source': 'product_name',
        
        'pycsw:Relation': '',
        'pycsw:Language': '',
        'pycsw:TopicCategory': '',

        # Added for mc3d
        # 'pycsw:Title': 'title',
        # 'pycsw:AlternateTitle': 'title',
        # 'pycsw:ProductVersion': 'version',
        # 'pycsw:TempExtent_begin': 'time_begin',
        # 'pycsw:TempExtent_end': 'time_end',
        # 'pycsw:footprint': '',
        # 'pycsw:projectName': 'project_name',
        # 'pycsw:centroid': 'centroid',
        # 'pycsw:nominalResolution': 'nominal_resolution',
        # 'pycsw:accuracyLE90': 'accuracy_le_90',
        # 'pycsw:accuracySE90': 'accuracy_se_90',
        # 'pycsw:visualAccuracy': 'visual_accuracy',
        # 'pycsw:heightRange': 'height_range',
        # 'pycsw:CRSOrigin': 'srs_origin',
        # 'pycsw:flightAlt': 'flight_alt',

        # Added for mc-raster 
        'pycsw:Rms': 'rms',
        'pycsw:Scale': 'scale',
    }
}
