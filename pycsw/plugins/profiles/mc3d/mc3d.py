from pycsw.plugins.profiles.base_profile.models.models import ProfileRepository, Queryable, TypenameModel
from pycsw.plugins.profiles.base_profile import base_profile


class MC3D(base_profile.base_profile):
    ''' MC3D class '''
    
    def __init__(self, model, namespaces, context):

        prefix = 'mc'
        typename = '%s:MC3DRecord' % (prefix)
        main_namespace = 'http://schema.mapcolonies.com/3d'

        schemas_pathes = [[ 'plugins','profiles', 'mc3d', 'schemas', 'mc3d-record.xsd']]

        added_namespaces = {
            prefix: main_namespace
        }

        profileRepository: ProfileRepository = {
            typename: TypenameModel(
                added_namespaces[prefix],
                {
                    'MC3DQueryables': {
                        'mc:projectName': Queryable(context.md_core_model['mappings']['pycsw:projectName'], 'mc:projectName'),
                        'mc:id': Queryable(context.md_core_model['mappings']['pycsw:Identifier'], 'mc:id'),
                        'mc:name': Queryable(context.md_core_model['mappings']['pycsw:Title'], 'mc:name'),
                        'mc:version': Queryable(context.md_core_model['mappings']['pycsw:version'], 'mc:version'),
                        'mc:centroid': Queryable(context.md_core_model['mappings']['pycsw:centroid'], 'mc:centroid'),
                        'mc:footprint': Queryable(context.md_core_model['mappings']['pycsw:footprint'], 'mc:footprint'),
                        'mc:boundingBox': Queryable(context.md_core_model['mappings']['pycsw:BoundingBox'], 'mc:boundingBox'),
                        'mc:classification': Queryable(context.md_core_model['mappings']['pycsw:Classification'], 'mc:classification'),
                        'mc:imagingTime_begin': Queryable(context.md_core_model['mappings']['pycsw:TempExtent_begin'], 'mc:imagingTime_begin'),
                        'mc:imagingTime_end': Queryable(context.md_core_model['mappings']['pycsw:TempExtent_end'], 'mc:imagingTime_end'),
                        'mc:sensorType': Queryable(context.md_core_model['mappings']['pycsw:sensorType'], 'mc:sensorType'),
                        'mc:region': Queryable(context.md_core_model['mappings']['pycsw:region'], 'mc:region'),
                        'mc:nominalResolution': Queryable(context.md_core_model['mappings']['pycsw:nominalResolution'], 'mc:nominalResolution'),
                        'mc:accuracyLE90': Queryable(context.md_core_model['mappings']['pycsw:accuracyLE90'], 'mc:accuracyLE90'),
                        'mc:horizontalAccuracyCE90': Queryable(context.md_core_model['mappings']['pycsw:horizontalAccuracyCE90'], 'mc:horizontalAccuracyCE90'),
                        'mc:relativeAccuracyLE90': Queryable(context.md_core_model['mappings']['pycsw:relativeAccuracyLE90'], 'mc:relativeAccuracyLE90'),
                        'mc:creationDate': Queryable(context.md_core_model['mappings']['pycsw:CreationDate'], 'mc:creationDate'),
                        'mc:producerName': Queryable(context.md_core_model['mappings']['pycsw:Creator'], 'mc:producerName'),
                        'mc:SRS': Queryable(context.md_core_model['mappings']['pycsw:CRS'], 'mc:SRS'),
                        'mc:validationDate': Queryable(context.md_core_model['mappings']['pycsw:validationDate'], 'mc:validationDate'),
                        'mc:estimatedPrecision': Queryable(context.md_core_model['mappings']['pycsw:estimatedPrecision'], 'mc:estimatedPrecision'),
                        'mc:measuredPrecision': Queryable(context.md_core_model['mappings']['pycsw:measuredPrecision'], 'mc:measuredPrecision'),
                        'mc:description': Queryable(context.md_core_model['mappings']['pycsw:Abstract'], 'mc:description'),
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
