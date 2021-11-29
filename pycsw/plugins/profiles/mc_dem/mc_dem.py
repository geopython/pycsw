from pycsw.plugins.profiles.base_profile.models.models import ProfileRepository, Queryable, TypenameModel
from pycsw.plugins.profiles.base_profile import base_profile


class MCDEM(base_profile.base_profile):
    ''' MCDEM class '''
    
    def __init__(self, model, namespaces, context):

        prefix = 'mc'
        typename = '%s:MCDEMRecord' % (prefix)
        main_namespace = 'http://schema.mapcolonies.com/dem'

        schemas_pathes = [[ 'plugins','profiles', 'mc_dem', 'schemas', 'mcdem-record.xsd']]

        added_namespaces = {
            prefix: main_namespace
        }

        profileRepository: ProfileRepository = {
            typename: TypenameModel(
                added_namespaces[prefix],
                {
                    'MCDEMQueryables': {
                        'mc:id': Queryable(context.md_core_model['mappings']['pycsw:Identifier'], 'mc:id'),

                        'mc:imagingTimeEndUTC': Queryable(context.md_core_model['mappings']['pycsw:imagingTimeEndUTC'], 'mc:imagingTimeEndUTC'),
                        'mc:resolutionMeter': Queryable(context.md_core_model['mappings']['pycsw:resolutionMeter'], 'mc:resolutionMeter'),
                        'mc:coverageID': Queryable(context.md_core_model['mappings']['pycsw:coverageID'], 'mc:coverageID'),
                        'mc:heightRangeFrom': Queryable(context.md_core_model['mappings']['pycsw:heightRangeFrom'], 'mc:heightRangeFrom'),
                        'mc:heightRangeTo': Queryable(context.md_core_model['mappings']['pycsw:heightRangeTo'], 'mc:heightRangeTo'),
                        'mc:verticalDatum': Queryable(context.md_core_model['mappings']['pycsw:verticalDatum'], 'mc:verticalDatum'),
                        'mc:units': Queryable(context.md_core_model['mappings']['pycsw:units'], 'mc:units'),
                        'mc:geographicArea': Queryable(context.md_core_model['mappings']['pycsw:geographicArea'], 'mc:geographicArea'),
                        'mc:undulationModel': Queryable(context.md_core_model['mappings']['pycsw:undulationModel'], 'mc:undulationModel'),
                        'mc:dataType': Queryable(context.md_core_model['mappings']['pycsw:dataType'], 'mc:dataType'),
                        'mc:noDataValue': Queryable(context.md_core_model['mappings']['pycsw:noDataValue'], 'mc:noDataValue'),

                        'mc:productId': Queryable(context.md_core_model['mappings']['pycsw:ProductId'], 'mc:productId'),
                        'mc:productName': Queryable(context.md_core_model['mappings']['pycsw:Title'], 'mc:productName'),
                        'mc:productType': Queryable(context.md_core_model['mappings']['pycsw:ProductType'], 'mc:productType'),
                        'mc:description': Queryable(context.md_core_model['mappings']['pycsw:Abstract'], 'mc:description'),
                        'mc:insertDate': Queryable(context.md_core_model['mappings']['pycsw:InsertDate'], 'mc:insertDate'),
                        'mc:updateDateUTC': Queryable(context.md_core_model['mappings']['pycsw:UpdateDate'], 'mc:updateDateUTC'),
                        'mc:imagingTimeBeginUTC': Queryable(context.md_core_model['mappings']['pycsw:TempExtent_begin'], 'mc:imagingTimeBeginUTC'),
                        'mc:imagingTimeEndUTC': Queryable(context.md_core_model['mappings']['pycsw:TempExtent_end'], 'mc:imagingTimeEndUTC'),
                        'mc:resolutionDeg': Queryable(context.md_core_model['mappings']['pycsw:resolutionDeg'], 'mc:resolutionDeg'),
                        'mc:absoluteAccuracyLEP90': Queryable(context.md_core_model['mappings']['pycsw:absoluteAccuracyLEP90'], 'mc:absoluteAccuracyLEP90'),
                        'mc:relativeAccuracyLEP90': Queryable(context.md_core_model['mappings']['pycsw:relativeAccuracyLEP90'], 'mc:relativeAccuracyLEP90'),
                        'mc:sensors': Queryable(context.md_core_model['mappings']['pycsw:sensorType'], 'mc:sensors'),
                        'mc:SRS': Queryable(context.md_core_model['mappings']['pycsw:CRS'], 'mc:SRS'),
                        'mc:SRSName': Queryable(context.md_core_model['mappings']['pycsw:CRSName'], 'mc:SRSName'),
                        'mc:region': Queryable(context.md_core_model['mappings']['pycsw:Region'], 'mc:region'),
                        'mc:classification': Queryable(context.md_core_model['mappings']['pycsw:Classification'], 'mc:classification'),
                        'mc:producerName': Queryable(context.md_core_model['mappings']['pycsw:Creator'], 'mc:producerName'),
                        'mc:links': Queryable(context.md_core_model['mappings']['pycsw:Links'], 'mc:links'),
                        'mc:type': Queryable(context.md_core_model['mappings']['pycsw:Type'], 'mc:type'),
                        'mc:boundingBox': Queryable(context.md_core_model['mappings']['pycsw:BoundingBox'], 'mc:boundingBox'),
                        'mc:footprint': Queryable(context.md_core_model['mappings']['pycsw:footprint'], 'mc:footprint'),
                        'mc:layerPolygonParts': Queryable(context.md_core_model['mappings']['pycsw:layerPolygonParts'], 'mc:layerPolygonParts'),
                        'mc:keywords': Queryable(context.md_core_model['mappings']['pycsw:Keywords'], 'mc:keywords'),
                        'mc:productBBox': Queryable(context.md_core_model['mappings']['pycsw:productBBox'], 'mc:productBBox'),
                    }
                })
        }

        super().__init__(name='mcdem',
                         version='1.0.0',
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
