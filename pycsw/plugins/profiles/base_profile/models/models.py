from typing import Dict

class ClassDict(object):
    """A base class that adds dictionary style access to objects"""
    def __getitem__(self, key): 
        return self.__dict__[key]

class Queryable(ClassDict):
    """A class that represents the link between a column in the db and its target xpath inside the record"""
    def __init__(self, dbcol: str, xpath: str):
        self.dbcol: str = dbcol
        self.xpath: str = xpath


"""Dictionary where the key is a queryable exposed by the profile e.g. "apiso:Title" and the value is the correspondong Queryable object """
QueryablesCategory = Dict[str, Queryable]


QueryablesObject = Dict[str, QueryablesCategory]

MappingsObject = Dict[str,Dict[str,str]]

class TypenameModel(ClassDict):
    def __init__(self, outputschema: str, queryables: QueryablesObject, mappings: MappingsObject = { 'csw:Record': {} }) -> None:
        self.outputschema = outputschema
        self.queryables = queryables
        self.mappings = mappings

ProfileRepository = Dict[str, TypenameModel]
