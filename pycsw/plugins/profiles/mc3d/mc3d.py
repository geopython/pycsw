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
                        'mc:product_name': Queryable(context.md_core_model['mappings']['pycsw:productName'], 'mc:product_name'),
                        'mc:product_version': Queryable(context.md_core_model['mappings']['pycsw:productVersion'], 'mc:product_version'),
                        'mc:product_type': Queryable(context.md_core_model['mappings']['pycsw:productType'], 'mc:product_type'),
                        'mc:description': Queryable(context.md_core_model['mappings']['pycsw:description'], 'mc:description'),
                        'mc:creation_date': Queryable(context.md_core_model['mappings']['pycsw:creationDate'], 'mc:creation_date'),
                        'mc:source_date_start': Queryable(context.md_core_model['mappings']['pycsw:sourceDateStart'], 'mc:source_date_start'),
                        'mc:source_date_end': Queryable(context.md_core_model['mappings']['pycsw:sourceDateEnd'], 'mc:source_date_end'),
                        'mc:min_resolution_meter': Queryable(context.md_core_model['mappings']['pycsw:minResolutionMeter'], 'mc:min_resolution_meter'),
                        'mc:max_resolution_meter': Queryable(context.md_core_model['mappings']['pycsw:maxResolutionMeter'], 'mc:max_resolution_meter'),
                        'mc:nominal_resolution': Queryable(context.md_core_model['mappings']['pycsw:nominalResolution'], 'mc:nominal_resolution'),
                        'mc:max_accuracy_CE90': Queryable(context.md_core_model['mappings']['pycsw:maxAccuracyCE90'], 'mc:max_accuracy_CE90'),
                        'mc:absolute_accuracy_LEP90': Queryable(context.md_core_model['mappings']['pycsw:absoluteAccuracyLEP90'], 'mc:absolute_accuracy_LEP90'),
                        'mc:accuracy_SE90': Queryable(context.md_core_model['mappings']['pycsw:accuracySE90'], 'mc:accuracy_SE90'),
                        'mc:relative_accuracy_LEP90': Queryable(context.md_core_model['mappings']['pycsw:relativeAccuracyLEP90'], 'mc:relative_accuracy_LEP90'),
                        'mc:visual_accuracy': Queryable(context.md_core_model['mappings']['pycsw:visualAccuracy'], 'mc:visual_accuracy'),
                        'mc:sensors': Queryable(context.md_core_model['mappings']['pycsw:sensors'], 'mc:sensors'),
                        'mc:footprint': Queryable(context.md_core_model['mappings']['pycsw:footprint'], 'mc:footprint'),
                        'mc:height_range_from': Queryable(context.md_core_model['mappings']['pycsw:heightRangeFrom'], 'mc:height_range_from'),
                        'mc:height_range_to': Queryable(context.md_core_model['mappings']['pycsw:heightRangeTo'], 'mc:height_range_to'),
                        'mc:srs_id': Queryable(context.md_core_model['mappings']['pycsw:srsId'], 'mc:srs_id'),
                        'mc:srs_name': Queryable(context.md_core_model['mappings']['pycsw:srsName'], 'mc:srs_name'),
                        'mc:srs_origin': Queryable(context.md_core_model['mappings']['pycsw:srsOrigin'], 'mc:srs_origin'),
                        'mc:region': Queryable(context.md_core_model['mappings']['pycsw:region'], 'mc:region'),
                        'mc:classification': Queryable(context.md_core_model['mappings']['pycsw:classification'], 'mc:classification'),
                        'mc:compartmentalization': Queryable(context.md_core_model['mappings']['pycsw:compartmentalization'], 'mc:compartmentalization'),
                        'mc:production_system': Queryable(context.md_core_model['mappings']['pycsw:productionSystem'], 'mc:production_system'),
                        'mc:producer_name': Queryable(context.md_core_model['mappings']['pycsw:producerName'], 'mc:producer_name'),
                        'mc:production_method': Queryable(context.md_core_model['mappings']['pycsw:productionMethod'], 'mc:production_method'),
                        'mc:min_flight_alt': Queryable(context.md_core_model['mappings']['pycsw:minFlightAlt'], 'mc:min_flight_alt'),
                        'mc:max_flight_alt': Queryable(context.md_core_model['mappings']['pycsw:maxFlightAlt'], 'mc:max_flight_alt'),
                        'mc:geographic_area': Queryable(context.md_core_model['mappings']['pycsw:geographicArea'], 'mc:geographic_area'),
                        'mc:product_bounding_box': Queryable(context.md_core_model['mappings']['pycsw:productBoundingBox'], 'mc:product_bounding_box'),

                        'mc:URI': Queryable(context.md_core_model['mappings']['pycsw:Links'], 'mc:URI'),
                        'mc:type': Queryable(context.md_core_model['mappings']['pycsw:Type'], 'mc:type'),
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
