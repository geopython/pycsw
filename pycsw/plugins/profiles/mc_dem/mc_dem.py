from pycsw.plugins.profiles.base_profile.models.models import ProfileRepository, Queryable, TypenameModel
from pycsw.plugins.profiles.base_profile import base_profile


class MCDEM(base_profile.base_profile):
    ''' MCDEM class '''

    def __init__(self, model, namespaces, context):

        prefix = 'mc'
        typename = '%s:MCDEMRecord' % (prefix)
        main_namespace = 'http://schema.mapcolonies.com/dem'

        schemas_pathes = [[ 'plugins', 'profiles', 'mc_dem', 'schemas', 'mcdem-record.xsd']]

        added_namespaces = {
            prefix: main_namespace
        }

        profileRepository: ProfileRepository = {
            typename: TypenameModel(
                added_namespaces[prefix],
                {
                    'MCDEMQueryables': {
                        'mc:id': Queryable(context.md_core_model['mappings']['pycsw:Identifier'], 'mc:id'),
                        'mc:productId': Queryable(context.md_core_model['mappings']['pycsw:ProductId'], 'mc:productId'),
                        'mc:productType': Queryable(context.md_core_model['mappings']['pycsw:ProductType'], 'mc:productType'),
                        'mc:productSubType': Queryable(context.md_core_model['mappings']['pycsw:productSubType'], 'mc:productSubType'),
                        'mc:productName': Queryable(context.md_core_model['mappings']['pycsw:Title'], 'mc:productName'),
                        'mc:productVersion': Queryable(context.md_core_model['mappings']['pycsw:ProductVersion'], 'mc:productVersion'),
                        'mc:ingestionDateUTC': Queryable(context.md_core_model['mappings']['pycsw:ingestionDateUTC'], 'mc:ingestionDateUTC'),
                        'mc:acquisitionTimeBeginUTC': Queryable(context.md_core_model['mappings']['pycsw:TempExtent_begin'], 'mc:acquisitionTimeBeginUTC'),
                        'mc:acquisitionTimeEndUTC': Queryable(context.md_core_model['mappings']['pycsw:TempExtent_end'], 'mc:acquisitionTimeEndUTC'),
                        'mc:minResolutionDegree': Queryable(context.md_core_model['mappings']['pycsw:minResolutionDegree'], 'mc:minResolutionDegree'),
                        'mc:maxResolutionDegree': Queryable(context.md_core_model['mappings']['pycsw:maxResolutionDegree'], 'mc:maxResolutionDegree'),
                        'mc:minResolutionMeter': Queryable(context.md_core_model['mappings']['pycsw:minResolutionMeter'], 'mc:minResolutionMeter'),
                        'mc:maxResolutionMeter': Queryable(context.md_core_model['mappings']['pycsw:maxResolutionMeter'], 'mc:maxResolutionMeter'),
                        'mc:minAbsoluteAccuracyLEP90': Queryable(context.md_core_model['mappings']['pycsw:minAbsoluteAccuracyLEP90'], 'mc:minAbsoluteAccuracyLEP90'),
                        'mc:maxAbsoluteAccuracyLEP90': Queryable(context.md_core_model['mappings']['pycsw:maxAbsoluteAccuracyLEP90'], 'mc:maxAbsoluteAccuracyLEP90'),
                        'mc:minRelativeAccuracyLEP90': Queryable(context.md_core_model['mappings']['pycsw:minRelativeAccuracyLEP90'], 'mc:minRelativeAccuracyLEP90'),
                        'mc:maxRelativeAccuracyLEP90': Queryable(context.md_core_model['mappings']['pycsw:maxRelativeAccuracyLEP90'], 'mc:maxRelativeAccuracyLEP90'),
                        'mc:minHorizontalAccuracyCEP90': Queryable(context.md_core_model['mappings']['pycsw:minHorizontalAccuracyCEP90'], 'mc:minHorizontalAccuracyCEP90'),
                        'mc:maxHorizontalAccuracyCEP90': Queryable(context.md_core_model['mappings']['pycsw:maxHorizontalAccuracyCEP90'], 'mc:maxHorizontalAccuracyCEP90'),
                        'mc:verticalType': Queryable(context.md_core_model['mappings']['pycsw:verticalType'], 'mc:verticalType'),
                        'mc:verticalSrsId': Queryable(context.md_core_model['mappings']['pycsw:verticalSrsId'], 'mc:verticalSrsId'),
                        'mc:verticalSrsName': Queryable(context.md_core_model['mappings']['pycsw:verticalSrsName'], 'mc:verticalSrsName'),
                        'mc:sensors': Queryable(context.md_core_model['mappings']['pycsw:sensorType'], 'mc:sensors'),
                        'mc:srsId': Queryable(context.md_core_model['mappings']['pycsw:CRS'], 'mc:srsId'),
                        'mc:srsName': Queryable(context.md_core_model['mappings']['pycsw:CRSName'], 'mc:srsName'),
                        'mc:region': Queryable(context.md_core_model['mappings']['pycsw:region'], 'mc:region'),
                        'mc:dataType': Queryable(context.md_core_model['mappings']['pycsw:dataType'], 'mc:dataType'),
                        'mc:noDataValue': Queryable(context.md_core_model['mappings']['pycsw:noDataValue'], 'mc:noDataValue'),
                        'mc:classification': Queryable(context.md_core_model['mappings']['pycsw:Classification'], 'mc:classification'),
                        'mc:description': Queryable(context.md_core_model['mappings']['pycsw:Abstract'], 'mc:description'),
                        'mc:areaOrPoint': Queryable(context.md_core_model['mappings']['pycsw:areaOrPoint'], 'mc:areaOrPoint'),
                        'mc:footprint': Queryable(context.md_core_model['mappings']['pycsw:footprint'], 'mc:footprint'),
                        'mc:links': Queryable(context.md_core_model['mappings']['pycsw:Links'], 'mc:links'),
                        'mc:updateDateUTC': Queryable(context.md_core_model['mappings']['pycsw:updateDateUTC'], 'mc:updateDateUTC'),
                        'mc:producerName': Queryable(context.md_core_model['mappings']['pycsw:Creator'], 'mc:producerName'),
                        'mc:type': Queryable(context.md_core_model['mappings']['pycsw:Type'], 'mc:type'),
                        'mc:insertDateUTC': Queryable(context.md_core_model['mappings']['pycsw:InsertDate'], 'mc:insertDateUTC'),
                        'mc:keywords': Queryable(context.md_core_model['mappings']['pycsw:Keywords'], 'mc:keywords'),
                        'mc:boundingBox': Queryable(context.md_core_model['mappings']['pycsw:BoundingBox'], 'mc:boundingBox')
                    }
                })
        }

        super().__init__(name='mcdem',
                         version='2.0.0',
                         title='Map Colonies DEM profile of CSW',
                         url='https://github.com/MapColonies',
                         typename=typename,
                         model=model,
                         core_namespaces=namespaces,
                         added_namespaces=added_namespaces,
                         repositories=profileRepository,
                         schemas_paths=schemas_pathes,
                         context=context,
                         prefix=prefix,
                         main_namespace=main_namespace
                         )
