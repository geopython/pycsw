from pycsw.plugins.profiles.base_profile.models.models import ProfileRepository, Queryable, TypenameModel
from pycsw.plugins.profiles.base_profile import base_profile


class MC3D(base_profile.base_profile):
    ''' MC3D class '''

    def __init__(self, model, namespaces, context):

        prefix = 'mc'
        typename = '%s:MC3DRecord' % (prefix)
        main_namespace = 'http://schema.mapcolonies.com/3d'

        schemas_pathes = [['plugins', 'profiles',
                           'mc3d', 'schemas', 'mc3d-record.xsd']]

        added_namespaces = {
            prefix: main_namespace
        }

        profileRepository: ProfileRepository = {
            typename: TypenameModel(
                added_namespaces[prefix],
                {
                    'MC3DQueryables': {
                        'mc:id': Queryable(context.md_core_model['mappings']['pycsw:Identifier'], 'mc:id'),
                        'mc:productId': Queryable(context.md_core_model['mappings']['pycsw:productId'], 'mc:productId'),
                        'mc:productName': Queryable(context.md_core_model['mappings']['pycsw:title'], 'mc:productName'),
                        'mc:productVersion': Queryable(context.md_core_model['mappings']['pycsw:productVersion'], 'mc:productVersion'),
                        'mc:productType': Queryable(context.md_core_model['mappings']['pycsw:productType'], 'mc:productType'),
                        'mc:description': Queryable(context.md_core_model['mappings']['pycsw:abstract'], 'mc:description'),
                        'mc:creationDateUTC': Queryable(context.md_core_model['mappings']['pycsw:creationDate'], 'mc:creationDateUTC'),
                        'mc:imagingTimeBeginUTC': Queryable(context.md_core_model['mappings']['pycsw:tempExtentBegin'], 'mc:imagingTimeBeginUTC'),
                        'mc:imagingTimeEndUTC': Queryable(context.md_core_model['mappings']['pycsw:tempExtentEnd'], 'mc:imagingTimeEndUTC'),
                        'mc:minResolutionMeter': Queryable(context.md_core_model['mappings']['pycsw:minResolution'], 'mc:minResolutionMeter'),
                        'mc:maxResolutionMeter': Queryable(context.md_core_model['mappings']['pycsw:maxResolution'], 'mc:maxResolutionMeter'),
                        'mc:nominalResolution': Queryable(context.md_core_model['mappings']['pycsw:nominalResolution'], 'mc:nominalResolution'),
                        'mc:maxHorizontalAccuracyCE90': Queryable(context.md_core_model['mappings']['pycsw:horizontalAccuracyCE90'], 'mc:maxHorizontalAccuracyCE90'),
                        'mc:accuracyLEP90': Queryable(context.md_core_model['mappings']['pycsw:accuracyLE90'], 'mc:accuracyLEP90'),
                        'mc:accuracySE90': Queryable(context.md_core_model['mappings']['pycsw:accuracySE90'], 'mc:accuracySE90'),
                        'mc:relativeAccuracyLE90': Queryable(context.md_core_model['mappings']['pycsw:relativeAccuracyLE90'], 'mc:relativeAccuracyLE90'),
                        'mc:visualAccuracy': Queryable(context.md_core_model['mappings']['pycsw:visualAccuracy'], 'mc:visualAccuracy'),
                        'mc:sensors': Queryable(context.md_core_model['mappings']['pycsw:sensorType'], 'mc:sensors'),
                        'mc:footprint': Queryable(context.md_core_model['mappings']['pycsw:footprint'], 'mc:footprint'),
                        'mc:heightRangeFrom': Queryable(context.md_core_model['mappings']['pycsw:heightRangeFrom'], 'mc:heightRangeFrom'),
                        'mc:heightRangeTo': Queryable(context.md_core_model['mappings']['pycsw:heightRangeTo'], 'mc:heightRangeTo'),
                        'mc:SRS': Queryable(context.md_core_model['mappings']['pycsw:CRS'], 'mc:SRS'),
                        'mc:SRSName': Queryable(context.md_core_model['mappings']['pycsw:CRSName'], 'mc:SRSName'),
                        'mc:SRSOrigin': Queryable(context.md_core_model['mappings']['pycsw:CRSOrigin'], 'mc:SRSOrigin'),
                        'mc:region': Queryable(context.md_core_model['mappings']['pycsw:region'], 'mc:region'),
                        'mc:classification': Queryable(context.md_core_model['mappings']['pycsw:classification'], 'mc:classification'),
                        'mc:compartmentalization': Queryable(context.md_core_model['mappings']['pycsw:compartmentalization'], 'mc:compartmentalization'),
                        'mc:productionSystem': Queryable(context.md_core_model['mappings']['pycsw:productionSystem'], 'mc:productionSystem'),
                        'mc:productionSystemVersion': Queryable(context.md_core_model['mappings']['pycsw:productionSystemVersion'], 'mc:productionSystemVersion'),
                        'mc:producerName': Queryable(context.md_core_model['mappings']['pycsw:creator'], 'mc:producerName'),
                        'mc:productionMethod': Queryable(context.md_core_model['mappings']['pycsw:productionMethod'], 'mc:productionMethod'),
                        'mc:minFlightAlt': Queryable(context.md_core_model['mappings']['pycsw:minFlightAlt'], 'mc:minFlightAlt'),
                        'mc:maxFlightAlt': Queryable(context.md_core_model['mappings']['pycsw:maxFlightAlt'], 'mc:maxFlightAlt'),
                        'mc:geographicArea': Queryable(context.md_core_model['mappings']['pycsw:geographicArea'], 'mc:geographicArea'),
                        'mc:productBBox': Queryable(context.md_core_model['mappings']['pycsw:productBBox'], 'mc:productBBox'),

                        'mc:links': Queryable(context.md_core_model['mappings']['pycsw:Links'], 'mc:links'),
                        'mc:type': Queryable(context.md_core_model['mappings']['pycsw:Type'], 'mc:type'),
                        'mc:boundingBox': Queryable(context.md_core_model['mappings']['pycsw:BoundingBox'], 'mc:boundingBox'),
                        'mc:keywords': Queryable(context.md_core_model['mappings']['pycsw:Keywords'], 'mc:keywords'),
                    }
                })
        }

        super().__init__(name='mc3d',
                         version='1.0.0',
                         title='Map Colonies 3D profile of CSW',
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
