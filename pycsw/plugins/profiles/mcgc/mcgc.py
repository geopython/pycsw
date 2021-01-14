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
                        'mcgc:accessRights': Queryable(context.md_core_model['mappings']['pycsw:Classification'], 'dct:accessRights'),
                        'mcgc:created': Queryable(context.md_core_model['mappings']['pycsw:CreationDate'], 'dct:created'),
                        'mcgc:creator': Queryable(context.md_core_model['mappings']['pycsw:Creator'], 'dc:creator'),
                        'mcgc:crs': Queryable(context.md_core_model['mappings']['pycsw:CRS'],'dct:spatial'),
                        'mcgc:references': Queryable(context.md_core_model['mappings']['pycsw:Links'],'dct:references'),
                        'mcgc:abstract': Queryable(context.md_core_model['mappings']['pycsw:Abstract'],'dct:abstract'),
                        'mcgc:anyText': Queryable(context.md_core_model['mappings']['pycsw:AnyText'],""),
                        'mcgc:relation': Queryable(context.md_core_model['mappings']['pycsw:Relation'],'dc:relation'),
                        'mcgc:boundingBox': Queryable(context.md_core_model['mappings']['pycsw:BoundingBox'],'ows:BoundingBox'),
                        'mcgc:format': Queryable(context.md_core_model['mappings']['pycsw:Format'],'dc:format'),
                        'mcgc:identifier': Queryable(context.md_core_model['mappings']['pycsw:Identifier'],'dc:identifier'),
                        'mcgc:dateModified': Queryable(context.md_core_model['mappings']['pycsw:Modified'], 'dct:modified'),
                        'mcgc:subject': Queryable(context.md_core_model['mappings']['pycsw:Keywords'], 'dc:subject'),
                        'mcgc:temporalExtentStart': Queryable(context.md_core_model['mappings']['pycsw:TempExtent_begin'], 'TemporalExtent/begin'),
                        'mcgc:temporalExtentEnd': Queryable(context.md_core_model['mappings']['pycsw:TempExtent_end'], 'TemporalExtent/end'),
                        'mcgc:title': Queryable(context.md_core_model['mappings']['pycsw:Title'], 'dc:title'),
                        'mcgc:type': Queryable(context.md_core_model['mappings']['pycsw:Type'], 'dc:type'),
                        'mcgc:region': Queryable(context.md_core_model['mappings']['pycsw:region'], 'mc:region'),
                        'mcgc:sensorName': Queryable(context.md_core_model['mappings']['pycsw:sensorName'], 'mc:sensor/name'),
                        'mcgc:sensorType': Queryable(context.md_core_model['mappings']['pycsw:sensorType'], 'mc:sensor/type'),
                        'mcgc:version': Queryable(context.md_core_model['mappings']['pycsw:version'], 'mc:version')
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
