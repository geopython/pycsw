import os
import traceback
from abc import abstractmethod
from typing import Dict, List
from pycsw.plugins.profiles.profile import Profile
from pycsw.ogc.csw.csw2 import Csw2, write_boundingbox
from pycsw.plugins.profiles.base_profile.models.models import ProfileRepository, Queryable, QueryablesObject
from pycsw.core.etree import etree
from pycsw.core import util

import constants


class base_profile(Profile):

    def __init__(self, name: str, version: str, title: str, url: str, prefix: str, typename: str, main_namespace: str,
         model, core_namespaces: Dict[str,str], repositories: ProfileRepository,
        schemas_paths: List[List[str]], context, added_namespaces: Dict[str,str] = {}, prefixes: List[str] = []):
        """base_profile constructor

        Parameters
        ----------
        name : str
            Name of the profile.  

        version : str
            Version of the profile.

        title : str
            Title of the profile.

        url : str
            URL to the description of the profile.

        prefix : str
            Prefix of the typename.

        typename : str
            Typename of the profile (name of the record type).

        main_namespace : str
            Main namespace of the profile.

        model : Any
            Pycsw model object as it is passed to the profile constructor.

        core_namespaces : Dict[str,str]
            Pycsw core namespaces as they are passed to the profile constructor.

        repositories : ProfileRepository
            Object representing the typenames of the repository including the queryables the xpath an the db columns.

        schemas_paths : List[List[str]]
            List of pathes to the schema files (.xsd) of the typename.

        context : Any
            Pycsw context as it is passed to the profile constructor.

        added_namespaces : Dict[str,str], optional
            Dictionary containing the xml namespaces of the profile, by default {}

        prefixes : List[str], optional
            List of optional prefixes of the profile, by default []
        """

        if prefixes == []:
            prefixes = [prefix]

        if name not in added_namespaces.keys():
            added_namespaces[name] = main_namespace

        self.schemas_paths = schemas_paths
        self.context = context
        self.namespaces = added_namespaces
     
        super().__init__(name, version, title, url, added_namespaces[prefix], typename, added_namespaces[prefix], prefixes, model, core_namespaces, added_namespaces, repositories[typename])

    def extend_core(self, model, namespaces, config):
        ''' Extend core configuration '''
        return None

    def check_parameters(self, kvp):
        '''Check for Language parameter in GetCapabilities request'''
        return None

    def get_extendedcapabilities(self):
        ''' Add child to ows:OperationsMetadata Element '''
        return None

    def get_schemacomponents(self):
        ''' Return schema components as lxml.etree.Element list '''

        schema_nodes = []

        for schema_path in self.schemas_paths:
            
            node = etree.Element(
                util.nspath_eval('csw:SchemaComponent', self.context.namespaces),
                schemaLanguage='XMLSCHEMA', targetNamespace=self.namespace)
            
            schema_file = os.path.join(self.context.pycsw_home, *schema_path)

            schema = etree.parse(schema_file, self.context.parser).getroot()

            node.append(schema)
            
            schema_nodes.append(node)

        return schema_nodes

    def check_getdomain(self, kvp):
        '''Perform extra profile specific checks in the GetDomain request'''
        return None

    def write_record(self, result, esn, outputschema, queryables):
        ''' Return csw:SearchResults child as lxml.etree.Element '''

        
        specialPycswKeys = [constants.PYCSW_BOUNDING_BOX,constants.PYCSW_KEYWORDS,constants.PYCSW_LINKS]
        
        specialDbcols = [queryables[x] for x in specialPycswKeys]

        typename = util.getqattr(
            result, self.context.md_core_model['mappings'][constants.PYCSW_TYPENAME])

        if typename == self.typename:
            # dump record as is and exit
            return etree.fromstring(util.getqattr(result, queryables[constants.PYCSW_XML]), self.context.parser)

        else:
            dbcol2xpath = _get_dbcol_to_xpath_dict(self.repository['queryables'])

            record = etree.Element(util.nspath_eval(
                self.typename, self.namespaces))

            # Sorted for consistency
            for dbcol in sorted(vars(result).keys()):

                value = util.getqattr(result, dbcol)

                if not dbcol.startswith('_') and value is not None:
                    elementName = dbcol2xpath.get(dbcol, None)

                    if elementName is not None:
                        if dbcol not in specialDbcols:  

                            _build_xpath(record, elementName, self.context.namespaces, value)

                        elif dbcol == queryables[constants.PYCSW_KEYWORDS]:

                            for keyword in value.split(','):
                                etree.SubElement(record, util.nspath_eval(elementName, self.context.namespaces)).text = keyword

                        elif dbcol == queryables[constants.PYCSW_LINKS]:
                            for link in value.split('^'):
                                linkComponents = link.split(',')
                                scheme = linkComponents[2]
                                uri = linkComponents[-1]
                                etree.SubElement(record, util.nspath_eval(elementName, self.context.namespaces), scheme=scheme).text = uri
                        
                        elif dbcol == queryables[constants.PYCSW_BOUNDING_BOX]:
                            bbox = write_boundingbox(value, self.context.namespaces)
                            record.append(bbox)
            return record
        
    
def _get_dbcol_to_xpath_dict(queryables: QueryablesObject):  
    flatQueryables: Dict[str,Queryable] = {}

    for qblsCategory in queryables.values():
        flatQueryables.update(qblsCategory)

    dbcol2xpath = {}

    for qbl in flatQueryables.values():
        if qbl.xpath and qbl.dbcol:
            dbcol2xpath[qbl.dbcol] = qbl.xpath

    return dbcol2xpath

def _build_xpath(node, path, namespaces, text):

    components = path.split("/")
    if util.nspath_eval(components[0],namespaces) == node.tag:
        components.pop(0)
    while components:

        # take in account positional  indexes in the form /path/para[3] or /path/para[location()=3]
        if "[" in components[0]:
            component, trail = components[0].split("[",1)
            target_index = int(trail.split("=")[-1].strip("]"))
        else:
            component = components[0]
            target_index = 0

        components.pop(0)
        found_index = -1

        for child in node.getchildren():
            if child.tag == util.nspath_eval(component,namespaces):
                found_index += 1
                if found_index == target_index:
                    node = child
                    break

        if found_index < target_index:
            new_node = None

            for i in range(target_index - found_index):
                new_node = etree.Element(util.nspath_eval(component,namespaces))
                node.append(new_node)

            node = new_node

    node.text = str(text)
    return node
    
