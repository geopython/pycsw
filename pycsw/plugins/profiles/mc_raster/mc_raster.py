from pycsw.plugins.profiles.base_profile.models.models import ProfileRepository, Queryable, TypenameModel
from pycsw.plugins.profiles.base_profile import base_profile


class MCRaster(base_profile.base_profile):
    ''' MCRaster class '''
    
    def __init__(self, model, namespaces, context):

        prefix = 'mc'
        typename = '%s:MCRasterRecord' % (prefix)
        main_namespace = 'http://schema.mapcolonies.com/raster'

        schemas_pathes = [[ 'plugins','profiles', 'mc_raster', 'schemas', 'mcraster-record.xsd']]

        added_namespaces = {
            prefix: main_namespace
        }

        profileRepository: ProfileRepository = {
            typename: TypenameModel(
                added_namespaces[prefix],
                {
                    'MCRasterQueryables': {
                        'mc:source': Queryable(context.md_core_model['mappings']['pycsw:Source'], 'mc:source'),
                        'mc:sourceName': Queryable(context.md_core_model['mappings']['pycsw:SourceName'], 'mc:sourceName'),
                        'mc:updateDate': Queryable(context.md_core_model['mappings']['pycsw:UpdateDate'], 'mc:updateDate'),
                        'mc:resolution': Queryable(context.md_core_model['mappings']['pycsw:Resolution'], 'mc:resolution'),
                        'mc:ep90': Queryable(context.md_core_model['mappings']['pycsw:Ep90'], 'mc:ep90'),
                        'mc:sensorType': Queryable(context.md_core_model['mappings']['pycsw:sensorType'], 'mc:sensorType'),
                        'mc:rms': Queryable(context.md_core_model['mappings']['pycsw:Rms'], 'mc:rms'),
                        'mc:scale': Queryable(context.md_core_model['mappings']['pycsw:Scale'], 'mc:scale'),
                        'mc:dsc': Queryable(context.md_core_model['mappings']['pycsw:Abstract'], 'mc:dsc'),
                        'mc:boundingBox': Queryable(context.md_core_model['mappings']['pycsw:BoundingBox'], 'mc:geometry'),
                        'mc:projectName': Queryable(context.md_core_model['mappings']['pycsw:Identifier'], 'mc:id'),
                        'mc:version': Queryable(context.md_core_model['mappings']['pycsw:version'], 'mc:version'),
                    }
                })
        }

        super().__init__(name='mcraster',
                         version='1.0.0',
                         title='Map Colonies raster profile of CSW',
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
