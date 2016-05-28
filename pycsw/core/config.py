# -*- coding: utf-8 -*-
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2016 Tom Kralidis
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

import logging
from pycsw.core.etree import etree
from pycsw import __version__

LOGGER = logging.getLogger(__name__)


class StaticContext(object):
    """core configuration"""
    def __init__(self, prefix='csw30'):
        """initializer"""

        LOGGER.debug('Initializing static context')
        self.version = __version__

        self.ogc_schemas_base = 'http://schemas.opengis.net'

        self.parser = etree.XMLParser(resolve_entities=False)

        self.languages = {
            'en': 'english',
            'fr': 'french',
            'el': 'greek',
        }

        self.response_codes = {
            'OK': '200 OK',
            'NotFound': '404 Not Found',
            'InvalidValue': '400 Invalid property value',
            'OperationParsingFailed': '400 Bad Request',
            'OperationProcessingFailed': '403 Server Processing Failed',
            'OperationNotSupported': '400 Not Implemented',
            'MissingParameterValue': '400 Bad Request',
            'InvalidParameterValue': '400 Bad Request',
            'VersionNegotiationFailed': '400 Bad Request',
            'InvalidUpdateSequence': '400 Bad Request',
            'OptionNotSupported': '400 Not Implemented',
            'NoApplicableCode': '400 Internal Server Error'
        }

        self.namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'csw': 'http://www.opengis.net/cat/csw/2.0.2',
            'csw30': 'http://www.opengis.net/cat/csw/3.0',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dct': 'http://purl.org/dc/terms/',
            'dif': 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/',
            'fes20': 'http://www.opengis.net/fes/2.0',
            'fgdc': 'http://www.opengis.net/cat/csw/csdgm',
            'gm03': 'http://www.interlis.ch/INTERLIS2.3',
            'gmd': 'http://www.isotc211.org/2005/gmd',
            'gml': 'http://www.opengis.net/gml',
            'ogc': 'http://www.opengis.net/ogc',
            'os': 'http://a9.com/-/spec/opensearch/1.1/',
            'ows': 'http://www.opengis.net/ows',
            'ows11': 'http://www.opengis.net/ows/1.1',
            'ows20': 'http://www.opengis.net/ows/2.0',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'soapenv': 'http://www.w3.org/2003/05/soap-envelope',
            'xlink': 'http://www.w3.org/1999/xlink',
            'xs': 'http://www.w3.org/2001/XMLSchema',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

        self.keep_ns_prefixes = [
            'csw', 'dc', 'dct', 'gmd', 'gml', 'ows', 'xs'
        ]

        self.md_core_model = {
            'typename': 'pycsw:CoreMetadata',
            'outputschema': 'http://pycsw.org/metadata',
            'mappings': {
                'pycsw:Identifier': 'identifier',
                # CSW typename (e.g. csw:Record, md:MD_Metadata)
                'pycsw:Typename': 'typename',
                # schema namespace, i.e. http://www.isotc211.org/2005/gmd
                'pycsw:Schema': 'schema',
                # origin of resource, either 'local', or URL to web service
                'pycsw:MdSource': 'mdsource',
                # date of insertion
                'pycsw:InsertDate': 'insert_date',  # date of insertion
                # raw XML metadata
                'pycsw:XML': 'xml',
                # bag of metadata element and attributes ONLY, no XML tages
                'pycsw:AnyText': 'anytext',
                'pycsw:Language': 'language',
                'pycsw:Title': 'title',
                'pycsw:Abstract': 'abstract',
                'pycsw:Keywords': 'keywords',
                'pycsw:KeywordType': 'keywordstype',
                'pycsw:Format': 'format',
                'pycsw:Source': 'source',
                'pycsw:Date': 'date',
                'pycsw:Modified': 'date_modified',
                'pycsw:Type': 'type',
                # geometry, specified in OGC WKT
                'pycsw:BoundingBox': 'wkt_geometry',
                'pycsw:CRS': 'crs',
                'pycsw:AlternateTitle': 'title_alternate',
                'pycsw:RevisionDate': 'date_revision',
                'pycsw:CreationDate': 'date_creation',
                'pycsw:PublicationDate': 'date_publication',
                'pycsw:OrganizationName': 'organization',
                'pycsw:SecurityConstraints': 'securityconstraints',
                'pycsw:ParentIdentifier': 'parentidentifier',
                'pycsw:TopicCategory': 'topicategory',
                'pycsw:ResourceLanguage': 'resourcelanguage',
                'pycsw:GeographicDescriptionCode': 'geodescode',
                'pycsw:Denominator': 'denominator',
                'pycsw:DistanceValue': 'distancevalue',
                'pycsw:DistanceUOM': 'distanceuom',
                'pycsw:TempExtent_begin': 'time_begin',
                'pycsw:TempExtent_end': 'time_end',
                'pycsw:ServiceType': 'servicetype',
                'pycsw:ServiceTypeVersion': 'servicetypeversion',
                'pycsw:Operation': 'operation',
                'pycsw:CouplingType': 'couplingtype',
                'pycsw:OperatesOn': 'operateson',
                'pycsw:OperatesOnIdentifier': 'operatesonidentifier',
                'pycsw:OperatesOnName': 'operatesoname',
                'pycsw:Degree': 'degree',
                'pycsw:AccessConstraints': 'accessconstraints',
                'pycsw:OtherConstraints': 'otherconstraints',
                'pycsw:Classification': 'classification',
                'pycsw:ConditionApplyingToAccessAndUse': 'conditionapplyingtoaccessanduse',
                'pycsw:Lineage': 'lineage',
                'pycsw:ResponsiblePartyRole': 'responsiblepartyrole',
                'pycsw:SpecificationTitle': 'specificationtitle',
                'pycsw:SpecificationDate': 'specificationdate',
                'pycsw:SpecificationDateType': 'specificationdatetype',
                'pycsw:Creator': 'creator',
                'pycsw:Publisher': 'publisher',
                'pycsw:Contributor': 'contributor',
                'pycsw:Relation': 'relation',
                # links: format "name,description,protocol,url[^,,,[^,,,]]"
                'pycsw:Links': 'links',
            }
        }

        self.model = None

        self.models = {
            'csw': {
                'operations_order': [
                    'GetCapabilities', 'DescribeRecord', 'GetDomain',
                    'GetRecords', 'GetRecordById', 'GetRepositoryItem'
                ],
                'operations': {
                    'GetCapabilities': {
                        'methods': {
                            'get': True,
                            'post': True,
                        },
                        'parameters': {
                            'sections': {
                                'values': ['ServiceIdentification', 'ServiceProvider',
                                'OperationsMetadata', 'Filter_Capabilities']
                            }
                        }
                    },
                    'DescribeRecord': {
                        'methods': {
                            'get': True,
                            'post': True,
                        },
                        'parameters': {
                            'schemaLanguage': {
                                'values': ['http://www.w3.org/XML/Schema',
                                           'http://www.w3.org/TR/xmlschema-1/',
                                           'http://www.w3.org/2001/XMLSchema']
                            },
                            'typeName': {
                                'values': ['csw:Record']
                            },
                            'outputFormat': {
                                'values': ['application/xml', 'application/json']
                            }
                        }
                    },
                    'GetRecords': {
                        'methods': {
                            'get': True,
                            'post': True,
                        },
                        'parameters': {
                            'resultType': {
                                'values': ['hits', 'results', 'validate']
                            },
                            'typeNames': {
                                'values': ['csw:Record']
                            },
                            'outputSchema': {
                                'values': ['http://www.opengis.net/cat/csw/2.0.2']
                            },
                            'outputFormat': {
                                'values': ['application/xml', 'application/json']
                            },
                            'CONSTRAINTLANGUAGE': {
                                'values': ['FILTER', 'CQL_TEXT']
                            },
                            'ElementSetName': {
                                'values': ['brief', 'summary', 'full']
                            }
                        },
                        'constraints': {
                        }
                    },
                    'GetRecordById': {
                        'methods': {
                            'get': True,
                            'post': True,
                        },
                        'parameters': {
                            'outputSchema': {
                                'values': ['http://www.opengis.net/cat/csw/2.0.2']
                            },
                            'outputFormat': {
                                'values': ['application/xml', 'application/json']
                            },
                            'ElementSetName': {
                                'values': ['brief', 'summary', 'full']
                            }
                        }
                    },
                    'GetRepositoryItem': {
                        'methods': {
                            'get': True,
                            'post': False,
                        },
                        'parameters': {
                        }
                    }
                },
                'parameters': {
                    'version': {
                        'values': ['2.0.2', '3.0.0']
                    },
                    'service': {
                        'values': ['CSW']
                    }
                },
                'constraints': {
                    'MaxRecordDefault': {
                        'values': ['10']
                    },
                    'PostEncoding': {
                        'values': ['XML', 'SOAP']
                    },
                    'XPathQueryables': {
                        'values': ['allowed']
                    }
                },
                'typenames': {
                    'csw:Record': {
                        'outputschema': 'http://www.opengis.net/cat/csw/2.0.2',
                        'queryables': {
                            'SupportedDublinCoreQueryables': {
                                # map Dublin Core queryables to core metadata model
                                'dc:title':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Title']},
                                'dc:creator':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Creator']},
                                'dc:subject':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Keywords']},
                                'dct:abstract':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Abstract']},
                                'dc:publisher':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Publisher']},
                                'dc:contributor':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Contributor']},
                                'dct:modified':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Modified']},
                                'dc:date':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Date']},
                                'dc:type':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Type']},
                                'dc:format':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Format']},
                                'dc:identifier':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Identifier']},
                                'dc:source':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Source']},
                                'dc:language':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Language']},
                                'dc:relation':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Relation']},
                                'dc:rights':
                                {'dbcol':
                                 self.md_core_model['mappings']['pycsw:AccessConstraints']},
                                # bbox and full text map to internal fixed columns
                                'ows:BoundingBox':
                                {'dbcol': self.md_core_model['mappings']['pycsw:BoundingBox']},
                                'csw:AnyText':
                                {'dbcol': self.md_core_model['mappings']['pycsw:AnyText']},
                            }
                        }
                    }
                }
            },
            'csw30': {
                'operations_order': [
                    'GetCapabilities', 'GetDomain', 'GetRecords',
                    'GetRecordById', 'GetRepositoryItem'
                ],
                'operations': {
                    'GetCapabilities': {
                        'methods': {
                            'get': True,
                            'post': True,
                        },
                        'parameters': {
                            'acceptVersions': {
                                'values': ['2.0.2', '3.0.0']
                            },
                            'acceptFormats': {
                                'values': ['text/xml', 'application/xml']
                            },
                            'sections': {
                                'values': ['ServiceIdentification', 'ServiceProvider',
                                'OperationsMetadata', 'Filter_Capabilities', 'All']
                            }
                        }
                    },
                    'GetRecords': {
                        'methods': {
                            'get': True,
                            'post': True,
                        },
                        'parameters': {
                            'typeNames': {
                                'values': ['csw:Record']
                            },
                            'outputSchema': {
                                'values': ['http://www.opengis.net/cat/csw/3.0']
                            },
                            'outputFormat': {
                                'values': ['application/xml', 'application/json', 'application/atom+xml']
                            },
                            'CONSTRAINTLANGUAGE': {
                                'values': ['FILTER', 'CQL_TEXT']
                            },
                            'ElementSetName': {
                                'values': ['brief', 'summary', 'full']
                            }
                        },
                        'constraints': {
                        }
                    },
                    'GetRecordById': {
                        'methods': {
                            'get': True,
                            'post': True,
                        },
                        'parameters': {
                            'outputSchema': {
                                'values': ['http://www.opengis.net/cat/csw/3.0']
                            },
                            'outputFormat': {
                                'values': ['application/xml', 'application/json', 'application/atom+xml']
                            },
                            'ElementSetName': {
                                'values': ['brief', 'summary', 'full']
                            }
                        }
                    },
                    'GetRepositoryItem': {
                        'methods': {
                            'get': True,
                            'post': False,
                        },
                        'parameters': {
                        }
                    }
                },
                'parameters': {
                    'version': {
                        'values': ['2.0.2', '3.0.0']
                    },
                    'service': {
                        'values': ['CSW']
                    }
                },
                'constraints': {
                    'MaxRecordDefault': {
                        'values': ['10']
                    },
                    'PostEncoding': {
                        'values': ['XML', 'SOAP']
                    },
                    'XPathQueryables': {
                        'values': ['allowed']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/OpenSearch': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/GetCapabilities-XML': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/GetRecordById-XML': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/GetRecords-Basic-XML': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/GetRecords-Distributed-XML': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/GetRecords-Distributed-KVP': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/GetRecords-Async-XML': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/GetRecords-Async-KVP': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/GetDomain-XML': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/GetDomain-KVP': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/Transaction': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/Harvest-Basic-XML': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/Harvest-Basic-KVP': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/Harvest-Async-XML': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/Harvest-Async-KVP': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/Harvest-Periodic-XML': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/Harvest-Periodic-KVP': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/Filter-CQL': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/Filter-FES-XML': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/Filter-FES-KVP-Advanced': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/SupportedGMLVersions': {
                        'values': ['http://www.opengis.net/gml']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/DefaultSortingAlgorithm': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/CoreQueryables': {
                        'values': ['TRUE']
                    },
                    'http://www.opengis.net/spec/csw/3.0/conf/CoreSortables': {
                        'values': ['TRUE']
                    }
                },
                'typenames': {
                    'csw:Record': {
                        'outputschema': 'http://www.opengis.net/cat/csw/3.0',
                        'queryables': {
                            'SupportedDublinCoreQueryables': {
                                # map Dublin Core queryables to core metadata model
                                'dc:title':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Title']},
                                'dc:creator':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Creator']},
                                'dc:subject':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Keywords']},
                                'dct:abstract':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Abstract']},
                                'dc:publisher':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Publisher']},
                                'dc:contributor':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Contributor']},
                                'dct:modified':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Modified']},
                                'dc:date':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Date']},
                                'dc:type':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Type']},
                                'dc:format':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Format']},
                                'dc:identifier':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Identifier']},
                                'dc:source':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Source']},
                                'dc:language':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Language']},
                                'dc:relation':
                                {'dbcol': self.md_core_model['mappings']['pycsw:Relation']},
                                'dc:rights':
                                {'dbcol':
                                 self.md_core_model['mappings']['pycsw:AccessConstraints']},
                                # bbox and full text map to internal fixed columns
                                'ows:BoundingBox':
                                {'dbcol': self.md_core_model['mappings']['pycsw:BoundingBox']},
                                'csw:AnyText':
                                {'dbcol': self.md_core_model['mappings']['pycsw:AnyText']},
                            }
                        }
                    }
                }
            }
        }
        self.set_model(prefix)

    def set_model(self, prefix):
        """sets model given request context"""

        self.model = self.models[prefix]

    def gen_domains(self):
        """Generate parameter domain model"""
        domain = {}
        domain['methods'] = {'get': True, 'post': True}
        domain['parameters'] = {'ParameterName': {'values': []}}
        for operation in self.model['operations'].keys():
            for parameter in self.model['operations'][operation]['parameters']:
                domain['parameters']['ParameterName']['values'].append('%s.%s' %
                                                        (operation, parameter))
        return domain

    def refresh_dc(self, mappings):
        """Refresh Dublin Core mappings"""

        LOGGER.debug('refreshing Dublin Core mappings with %s' % str(mappings))

        defaults = {
            'dc:title': 'pycsw:Title',
            'dc:creator': 'pycsw:Creator',
            'dc:subject': 'pycsw:Keywords',
            'dct:abstract': 'pycsw:Abstract',
            'dc:publisher': 'pycsw:Publisher',
            'dc:contributor': 'pycsw:Contributor',
            'dct:modified': 'pycsw:Modified',
            'dc:date': 'pycsw:Date',
            'dc:type': 'pycsw:Type',
            'dc:format': 'pycsw:Format',
            'dc:identifier': 'pycsw:Identifier',
            'dc:source': 'pycsw:Source',
            'dc:language': 'pycsw:Language',
            'dc:relation': 'pycsw:Relation',
            'dc:rights': 'pycsw:AccessConstraints',
            'ows:BoundingBox': 'pycsw:BoundingBox',
            'csw:AnyText': 'pycsw:AnyText',
        }

        for k, val in defaults.items():
            for model, params in self.models.items():
                queryables = params['typenames']['csw:Record']['queryables']
                queryables['SupportedDublinCoreQueryables'][k] = {
                    'dbcol': mappings['mappings'][val]
                }
