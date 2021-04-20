from pycsw.plugins.profiles.base_profile.models.models import ProfileRepository, Queryable, TypenameModel
from pycsw.plugins.profiles.base_profile import base_profile


class MCGC_BASE(base_profile.base_profile):
    ''' MCGC class '''
    
    def __init__(self, model, namespaces, context):

        prefix = 'mc'
        typename = '%s:MCGCRecord' % (prefix)
        main_namespace = 'http://schema.mapcolonies.com'

        schemas_pathes = [[ 'plugins','profiles', 'mcgc', 'schemas', 'mc-record.xsd']]

        added_namespaces = {
            prefix: main_namespace
        }

        profileRepository: ProfileRepository = {
            typename: TypenameModel(
                added_namespaces[prefix],
                {
                    'MGCGQueryables': {
                        'mcgc:id': Queryable(context.md_core_model['mappings']['pycsw:Identifier'], 'mc:id'),
                        'mcgc:name': Queryable(context.md_core_model['mappings']['pycsw:Title'], 'mc:name'),
                        'mcgc:creationDate': Queryable(context.md_core_model['mappings']['pycsw:CreationDate'], 'mc:creationDate'),
                        'mcgc:description': Queryable(context.md_core_model['mappings']['pycsw:Abstract'],'mc:description'),
                        'mcgc:geojson': Queryable(context.md_core_model['mappings']['pycsw:geojson'], 'mc:geojson'),
                        'mcgc:referenceSystem': Queryable(context.md_core_model['mappings']['pycsw:CRS'],'mc:referenceSystem'),
                        'mcgc:type': Queryable(context.md_core_model['mappings']['pycsw:Type'], 'mc:type'),
                        'mcgc:source': Queryable(context.md_core_model['mappings']['pycsw:Source'], 'mc:source'),
                        'mcgc:category': Queryable(context.md_core_model['mappings']['pycsw:category'], 'mc:category'),
                        'mcgc:thumbnail': Queryable(context.md_core_model['mappings']['pycsw:thumbnail'],'mc:thumbnail'),
                        'mcgc:URI': Queryable(context.md_core_model['mappings']['pycsw:Links'],'mc:URI'),
                        'mcgc:anyText': Queryable(context.md_core_model['mappings']['pycsw:AnyText'],""),
                        'mcgc:boundingBox': Queryable(context.md_core_model['mappings']['pycsw:BoundingBox'],'ows:BoundingBox'),
                        'mcgc:imagingTimeStart': Queryable(context.md_core_model['mappings']['pycsw:TempExtent_begin'], 'imagingTime/begin'),
                        'mcgc:imagingTimeEnd': Queryable(context.md_core_model['mappings']['pycsw:TempExtent_end'], 'imagingTime/end'),
                    }
                })
        }

        super().__init__(name='mcgc',
                         version='1.0.0',
                         title='Map Colonies General profile of CSW',
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
