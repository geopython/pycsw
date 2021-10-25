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

        # Update of Nati
        # Needed fot PYCSW

        'pycsw:Identifier': 'identifier',
        'pycsw:Typename': 'typename',
        'pycsw:Schema': 'schema',
        'pycsw:MdSource': 'mdsource',
        'pycsw:InsertDate': 'insert_date',
        'pycsw:XML': 'xml',
        'pycsw:AnyText': 'anytext',
        'pycsw:BoundingBox': 'wkb_geometry',
        'pycsw:Title': 'title',
        'pycsw:AlternateTitle': 'title',
        'pycsw:Creator': 'producer_name',
        'pycsw:Abstract': 'description',
        'pycsw:Publisher': 'producer_name',
        'pycsw:Contributor': 'producer_name',
        'pycsw:Modified': 'update_date',
        'pycsw:Links': 'links',
        'pycsw:Date': 'creation_date',
        'pycsw:Type': 'type',
        'pycsw:Format': 'type',
        'pycsw:Keywords': 'keywords',
        'pycsw:Source': 'product_name',
        'pycsw:AccessConstraints': 'classification',
        'pycsw:CRS': 'srs',
        'pycsw:Relation': '',
        'pycsw:Language': '',
        'pycsw:Keywords': '',
        'pycsw:TopicCategory': '',

        # Profile 3D fields
        'pycsw:productName': 'product_name',
        'pycsw:productVersion': 'product_version',
        'pycsw:productType': 'product_type',
        'pycsw:description': 'description',
        'pycsw:creationDate': 'creation_date',
        'pycsw:sourceDateStart': 'source_date_start',
        'pycsw:sourceDateEnd': 'source_date_end',
        'pycsw:minResolutionMeter': 'min_resolution_meter',
        'pycsw:maxResolutionMeter': 'max_resolution_meter',
        'pycsw:nominalResolution': 'nominal_resolution',
        'pycsw:maxAccuracyCE90': 'max_accuracy_CE90',
        'pycsw:absoluteAccuracyLEP90': 'absolute_accuracy_LEP90',
        'pycsw:accuracySE90': 'accuracy_SE90',
        'pycsw:relativeAccuracyLEP90': 'relative_accuracy_LEP90',
        'pycsw:visualAccuracy': 'visual_accuracy',
        'pycsw:sensors': 'sensors',
        'pycsw:footprint': 'footprint',
        'pycsw:heightRangeFrom': 'height_range_from',
        'pycsw:heightRangeTo': 'height_range_to',
        'pycsw:srsId': 'srs_id',
        'pycsw:srsName': 'srs_name',
        'pycsw:srsOrigin': 'srs_origin',
        'pycsw:region': 'region',
        'pycsw:classification': 'classification',
        'pycsw:compartmentalization': 'compartmentalization',
        'pycsw:productionSystem': 'production_system',
        'pycsw:producerName': 'producer_name',
        'pycsw:productionMethod': 'production_method',
        'pycsw:minFlightAlt': 'min_flight_alt',
        'pycsw:maxFlightAlt': 'max_flight_alt',
        'pycsw:geographicArea': 'geographic_area',
        'pycsw:productBoundingBox': 'product_bounding_box'
    }
}
