import os
from pycsw import wsgi
from pycsw.core import util
from pycsw.ogc.api.util import yaml_load
import dateutil.parser as dparser
import requests

def get_solr_mapping(core_queriables):
    #with open("test.yaml") as stream:
    #    core_queriables_solr = yaml.safe_load(stream)
    
    # core_queriables = core_queriables_solr['solr_mapping']
    # csw_config = get_config()
    schema_url = f"http://157.249.78.203/solr/adc/schema/fields?"
    # Make the request and get JSON response
    response = requests.get(schema_url, headers={"Accept": "application/json"})
    response.raise_for_status()
    data = response.json()
    fields_dict = {field["name"]: field["type"] for field in data.get("fields", [])}
    
    mapping_dict = {}
    for i in core_queriables:
        if type(core_queriables[i]) is not list:
            if core_queriables[i] in fields_dict:
                # print(i, "SOLR:", core_queriables[i], fields_dict[core_queriables[i]])
                mapping_dict[i] = fields_dict[core_queriables[i]]
        else:
            for k, j in enumerate(core_queriables[i]):
                if j in fields_dict:
                    # print(j, "SOLR:", fields_dict[core_queriables[i][k]])
                    mapping_dict[j] = fields_dict[core_queriables[i][k]]
    return mapping_dict

def get_solr_connection():
    return [get_config_parser("login", "username"), get_config_parser("login", "password")]


def get_config():
    pycsw_root = wsgi.get_pycsw_root_path(os.environ, os.environ)
    configuration_path = wsgi.get_configuration_path(os.environ, os.environ, pycsw_root)

    with open(configuration_path, encoding="utf-8") as scp:
        return yaml_load(scp)


def get_config_parser(section, entry):
    return get_config().get(section, entry)


def get_iso_transformer():
    mmd_to_iso = get_config_parser("repository", "xslt_iso_transformer")
    return get_config_parser("xslt", mmd_to_iso)


def get_collection_filter():
    pycsw_root = wsgi.get_pycsw_root_path(os.environ, os.environ)
    configuration_path = wsgi.get_configuration_path(os.environ, os.environ, pycsw_root)

    with open(configuration_path, encoding="utf-8") as scp:
        config = yaml_load(scp)
        collection_filter = config['repository'].get("adc_collection", '')

    return collection_filter.replace(",", " ")


def parse_bbox_OR_query(constraint, right_hand_envelope=False):
    if "ogc:BBOX" in constraint:
        print("Got bbox filter query")
        lc = constraint["ogc:BBOX"]["gml:Envelope"]["gml:lowerCorner"].strip().split()
        uc = constraint["ogc:BBOX"]["gml:Envelope"]["gml:upperCorner"].strip().split()
        lc = [float(i) for i in lc]
        uc = [float(i) for i in uc]
        # Right hand polygon
        if right_hand_envelope:
            envelope = (",").join(
                [
                    f"POLYGON(({lc[0]} {lc[1]}",
                    f"{uc[0]} {lc[1]}",
                    f"{uc[0]} {uc[1]}",
                    f"{lc[0]} {uc[1]}",
                    f"{lc[0]} {lc[1]}))",
                ]
            )
            # return envelope
        else:
            min_x, max_x, min_y, max_y = lc[1], uc[1], lc[0], uc[0]
            envelope = f"ENVELOPE({min_y},{max_y},{max_x},{min_x})"
            # envelope = f"ENVELOPE({min_x},{max_x},{max_y},{min_y})"
            # return  envelope
        solr_bbox_query = "{!field f=bbox score=overlapRatio}" + f"Within({envelope})"
        # params['fq'].append(solr_bbox_query)
        return solr_bbox_query.strip()


def parse_bbox_query(constraint, params, right_hand_envelope=False, or_flag=False):
    # first check if there is a key: "ogc:Filter"
    if or_flag: 
        print('got the following OR constrasint: ', constraint)
        return parse_bbox_OR_query(constraint)
    else:
        constraint = constraint["_dict"]["ogc:Filter"]
    if "ogc:And" in constraint:
        constraint = constraint["ogc:And"]
    if "ogc:BBOX" in constraint:
        print("Got bbox filter query")
        lc = constraint["ogc:BBOX"]["gml:Envelope"]["gml:lowerCorner"].strip().split()
        uc = constraint["ogc:BBOX"]["gml:Envelope"]["gml:upperCorner"].strip().split()
        lc = [float(i) for i in lc]
        uc = [float(i) for i in uc]
        # Right hand polygon
        if right_hand_envelope:
            envelope = (",").join(
                [
                    f"POLYGON(({lc[0]} {lc[1]}",
                    f"{uc[0]} {lc[1]}",
                    f"{uc[0]} {uc[1]}",
                    f"{lc[0]} {uc[1]}",
                    f"{lc[0]} {lc[1]}))",
                ]
            )
            # return envelope
        else:
            min_x, max_x, min_y, max_y = lc[1], uc[1], lc[0], uc[0]
            envelope = f"ENVELOPE({min_y},{max_y},{max_x},{min_x})"
            # envelope = f"ENVELOPE({min_x},{max_x},{max_y},{min_y})"
            # return  envelope
        solr_bbox_query = "{!field f=bbox score=overlapRatio}" + f"Within({envelope})"
        params["fq"].append(solr_bbox_query)
        return params
    else:
        return params


def get_bbox(query, right_hand_envelope=False):
    if "ogc:BBOX" in query["_dict"]["ogc:Filter"]:
        print("Got bbox filter query")
        lc = (
            query["_dict"]["ogc:Filter"]["ogc:BBOX"]["gml:Envelope"]["gml:lowerCorner"]
            .strip()
            .split()
        )
        uc = (
            query["_dict"]["ogc:Filter"]["ogc:BBOX"]["gml:Envelope"]["gml:upperCorner"]
            .strip()
            .split()
        )
        lc = [float(i) for i in lc]
        uc = [float(i) for i in uc]
        # Right hand polygon
        if right_hand_envelope:
            envelope = (",").join(
                [
                    f"POLYGON(({lc[0]} {lc[1]}",
                    f"{uc[0]} {lc[1]}",
                    f"{uc[0]} {uc[1]}",
                    f"{lc[0]} {uc[1]}",
                    f"{lc[0]} {lc[1]}))",
                ]
            )
            return envelope
        else:
            min_x, max_x, min_y, max_y = lc[1], uc[1], lc[0], uc[0]
            envelope = f"ENVELOPE({min_y},{max_y},{max_x},{min_x})"
            # envelope = f"ENVELOPE({min_x},{max_x},{max_y},{min_y})"
            print(envelope)
            return envelope
    if "ogc:And" in query["_dict"]["ogc:Filter"]:
        if "ogc:BBOX" in query["_dict"]["ogc:Filter"]["ogc:And"]:
            print("Got bbox AND filter query")
            lc = (
                query["_dict"]["ogc:Filter"]["ogc:And"]["ogc:BBOX"]["gml:Envelope"][
                    "gml:lowerCorner"
                ]
                .strip()
                .split()
            )
            uc = (
                query["_dict"]["ogc:Filter"]["ogc:And"]["ogc:BBOX"]["gml:Envelope"][
                    "gml:upperCorner"
                ]
                .strip()
                .split()
            )
            lc = [float(i) for i in lc]
            uc = [float(i) for i in uc]
            # Right hand polygon
            if right_hand_envelope:
                envelope = (",").join(
                    [
                        f"POLYGON(({lc[0]} {lc[1]}",
                        f"{uc[0]} {lc[1]}",
                        f"{uc[0]} {uc[1]}",
                        f"{lc[0]} {uc[1]}",
                        f"{lc[0]} {lc[1]}))",
                    ]
                )
                return envelope
            else:
                min_x, max_x, min_y, max_y = lc[1], uc[1], lc[0], uc[0]
                envelope = f"ENVELOPE({min_y},{max_y},{max_x},{min_x})"
                # envelope = f"ENVELOPE({min_x},{max_x},{max_y},{min_y})"
                print(envelope)
                return envelope

        else:
            print(f"ogc:BBOX not found in {query}")
            return False
    else:
        return False



def parse_PropertyIsLike():
    pass

def parse_PropertyIsGreaterThanOrEqualTo():
    pass

def parse_PropertyIsLessThanOrEqualTo():
    pass

def parse_BBOX():
    pass


def parse_time_query(constraint, params, and_flag=False):
    # print('#################')
    # print('calling parse_time_query with: \n', constraint, params, and_flag)
    dateformat = "%Y-%m-%dT%H:%M:%SZ"
    if not and_flag:
        qstring = constraint["_dict"]["ogc:Filter"]
    else:
        qstring = constraint["_dict"]["ogc:Filter"]["ogc:And"]
    if "ogc:PropertyIsGreaterThanOrEqualTo" in qstring:
        tempBegin = qstring.get("ogc:PropertyIsGreaterThanOrEqualTo", False)
        # print("tempBegin", type(tempBegin), tempBegin)
        if tempBegin:
            begin = qstring["ogc:PropertyIsGreaterThanOrEqualTo"]["ogc:Literal"]
            # print('begin:', begin)
            datestring = dparser.parse(begin)
            # print(datestring)
            params["fq"].append(
                "temporal_extent_start_date:[%s TO *]" % datestring.strftime(dateformat)
            )
            # print(params)
    if "ogc:PropertyIsLessThanOrEqualTo" in qstring:
        tempEnd = qstring.get("ogc:PropertyIsLessThanOrEqualTo", False)
        # print(tempEnd)
        # print("tempEnd", type(tempEnd), tempEnd)
        if tempEnd:
            end = qstring["ogc:PropertyIsLessThanOrEqualTo"]["ogc:Literal"]
            # print('end:', end)
            datestring = dparser.parse(end)
            # print(datestring)
            params["fq"].append(
                "temporal_extent_end_date:[* TO %s]" % datestring.strftime(dateformat)
            )
            # print(params)
    # print('######## PARAMS just after calling time query #########')
    # print(params)
    # print('######## completed time query #########')
    return params


def parse_field_OR_query(constraint, and_flag=False, or_flag=False):
    print("#### got the following constraint: ", constraint)
    if or_flag:
        property_name = list(constraint.keys())[0]
        print("property_name: ", property_name)
        qstring = constraint[property_name]["ogc:Literal"]
        name = constraint[property_name]["ogc:PropertyName"].split(":")[-1]
        print("name: ", name)
        print("qstring: ", qstring)
        return f"({name}:{qstring})"


def parse_apiso_query(constraint, params, and_flag=False, or_flag=False):
    # apiso:Type
    print("#### got the following constraint: ", constraint)
    print("#### got the following params: ", params)
    print("#### and_flag: ", and_flag)
    print("#### or_flag: ", or_flag)
    if not and_flag and or_flag:
        print("GOT: not and_flag and or_flag")
        property_name = list(constraint.keys())[0]
        print("property_name: ", property_name)
        qstring = constraint[property_name]["ogc:Literal"]
        name = constraint[property_name]["ogc:PropertyName"]
        print("name: ", name)
        print("qstring: ", qstring)
    if not and_flag and not or_flag:
        print("GOT: not and_flag and not or_flag")
        property_name = list(constraint["_dict"]["ogc:Filter"].keys())[0]
        print("property_name: ", property_name)
        qstring = constraint["_dict"]["ogc:Filter"][property_name]["ogc:Literal"]
        name = constraint["_dict"]["ogc:Filter"][property_name]["ogc:PropertyName"]
        print("name: ", name)
        print("qstring: ", qstring)
    if not or_flag and and_flag:
        property_name = list(constraint["_dict"]["ogc:Filter"]["ogc:And"].keys())[0]
        print("property_name: ", property_name)
        qstring = constraint["_dict"]["ogc:Filter"]["ogc:And"][property_name][
            "ogc:Literal"
        ]
        name = constraint["_dict"]["ogc:Filter"]["ogc:And"][property_name][
            "ogc:PropertyName"
        ]
        print("name: ", name)
        print("qstring: ", qstring)
    qstring = qstring.replace("%", "*")
    # print()
    if "type" in name.lower():
        print(f"got APISO type query with {name} set to {qstring}")
        if qstring.lower() == "dataset":
            params["fq"].append("isParent:false")
        elif qstring.lower() == "series":
            params["fq"].append("isParent:true")
    if "apiso:Anytext" in name:
            params["q"] = "full_text:(%s)" % qstring
    if "apiso:ParentIdentifier" in name:
        params["fq"].append(f'related_dataset:"{qstring}"')
        print(params)
    return params


def parse_property_is_like(params, qstring, name):
    print("name: ", name)
    print("qstring: ", qstring)
    qstring = qstring.replace("%", "*")
    if "title" in name.lower():
        params["fq"].append("title:(%s)" % qstring)
    elif "abstract" in name.lower():
        params["fq"].append("abstract:(%s)" % qstring)
    elif "subject" in name.lower():
        params["fq"].append("keywords_keyword:(%s)" % qstring)
    elif "creator" in name.lower():
        params["fq"].append("personnel_investigator_name:(%s)" % qstring)
    elif "contributor" in name.lower():
        params["fq"].append(
            "personnel_technical_name:(%s) OR personnel_metadata_author_name:(%s)"
            % (qstring, qstring)
            )
    elif "dc:source" in name:
        params["fq"].append("related_url_landing_page:(%s)" % qstring)
    elif "format" in name.lower():
        params["fq"].append("storage_information_file_format:(%s)" % qstring)
    elif "language" in name.lower():
        params["fq"].append("dataset_language:(%s)" % qstring)
    elif "publisher" in name.lower():
        params["fq"].append("dataset_citation_publisher:(%s)" % qstring)
    elif "rights" in name.lower():
        params["fq"].append(
            "use_constraint_identifier:(%s) OR use_constraint_license_text:(%s)"
            % (qstring, qstring)
        )

    elif "type" in name.lower():
        print(f"got APISO type query with {name} set to {qstring}")
        if qstring.lower() == "dataset":
            params["fq"].append("isParent:false")
        elif qstring.lower() == "series":
            params["fq"].append("isParent:true")
 
    elif "apiso:ParentIdentifier" in name:
        params["fq"].append(f'related_dataset:"{qstring}"')
    else:
        if name in ["apiso:Anytext",'csw:AnyText']:
            params["q"] = "full_text:(%s)" % qstring
    return params

def parse_field_query(constraint, params, and_flag=False, or_flag=False):
    print("executing: parse_field_query")
    print("#### got the following constraint: ", constraint)
    print("#### got the following params: ", params)
    print("#### and_flag: ", and_flag)
    print("#### or_flag: ", or_flag)
    if not and_flag and or_flag:
        print("GOT: not and_flag and or_flag")
        property_name = list(constraint.keys())[0]
        print("property_name: ", property_name)
        if property_name == 'ogc:PropertyIsLike':
            qstring = constraint["_dict"]["ogc:Filter"][property_name]["ogc:Literal"]
            name = constraint["_dict"]["ogc:Filter"][property_name]["ogc:PropertyName"]
            print("name: ", name)
            print("qstring: ", qstring)
            params = parse_property_is_like(params, qstring, name)

    if not and_flag and not or_flag:
        print("GOT: not and_flag and not or_flag")
        property_name = list(constraint["_dict"]["ogc:Filter"].keys())[0]
        print("property_name: ", property_name)
        if property_name == 'ogc:PropertyIsLike':
            qstring = constraint["_dict"]["ogc:Filter"][property_name]["ogc:Literal"]
            name = constraint["_dict"]["ogc:Filter"][property_name]["ogc:PropertyName"]
            print("name: ", name)
            print("qstring: ", qstring)
            params = parse_property_is_like(params, qstring, name)
        
    if not or_flag and and_flag:
        print("GOT: not or_flag and and_flag")
        for property_name in list(constraint["_dict"]["ogc:Filter"]["ogc:And"].keys()):
            # property_name = list(constraint["_dict"]["ogc:Filter"]["ogc:And"].keys())[0]
            print("property_name: ", property_name)
            if property_name == 'ogc:BBOX':
                params = parse_bbox_query(constraint, params)
                print('PARAMS after parse_bbox_query ', params)
            if property_name == 'ogc:PropertyIsLike':
                qstring = constraint["_dict"]["ogc:Filter"]["ogc:And"][property_name][
                    "ogc:Literal"
                ]
                name = constraint["_dict"]["ogc:Filter"]["ogc:And"][property_name][
                    "ogc:PropertyName"
                ]
                print("name: ", name)
                print("qstring: ", qstring)
                qstring = qstring.replace("%", "*")
                params = parse_property_is_like(params, qstring, name)
    return params

def parse_field_query_(constraint, params, and_flag=False, or_flag=False):
    print("executing: parse_field_query")
    print("#### got the following constraint: ", constraint)
    print("#### got the following params: ", params)
    print("#### and_flag: ", and_flag)
    print("#### or_flag: ", or_flag)
    if not and_flag and or_flag:
        print("GOT: not and_flag and or_flag")
        property_name = list(constraint.keys())[0]
        print("property_name: ", property_name)
        qstring = constraint[property_name]["ogc:Literal"]
        name = constraint[property_name]["ogc:PropertyName"]
        print("name: ", name)
        print("qstring: ", qstring)
    if not and_flag and not or_flag:
        print("GOT: not and_flag and not or_flag")
        property_name = list(constraint["_dict"]["ogc:Filter"].keys())[0]
        print("property_name: ", property_name)
        qstring = constraint["_dict"]["ogc:Filter"][property_name]["ogc:Literal"]
        name = constraint["_dict"]["ogc:Filter"][property_name]["ogc:PropertyName"]
        print("name: ", name)
        print("qstring: ", qstring)
    if not or_flag and and_flag:
        print("GOT: not or_flag and and_flag")
        for property_name in list(constraint["_dict"]["ogc:Filter"]["ogc:And"].keys()):
            # property_name = list(constraint["_dict"]["ogc:Filter"]["ogc:And"].keys())[0]
            print("property_name: ", property_name)
            if property_name == 'ogc:BBOX':
                params = parse_bbox_query(constraint, params)
                print('PARAMS after parse_bbox_query ', params)
            if property_name == 'ogc:PropertyIsLike':
                qstring = constraint["_dict"]["ogc:Filter"]["ogc:And"][property_name][
                    "ogc:Literal"
                ]
                name = constraint["_dict"]["ogc:Filter"]["ogc:And"][property_name][
                    "ogc:PropertyName"
                ]
                print("name: ", name)
                print("qstring: ", qstring)
                qstring = qstring.replace("%", "*")
                if "title" in name.lower():
                    params["fq"].append("title:(%s)" % qstring)
                elif "abstract" in name.lower():
                    params["fq"].append("abstract:(%s)" % qstring)
                elif "subject" in name.lower():
                    params["fq"].append("keywords_keyword:(%s)" % qstring)
                elif "creator" in name.lower():
                    params["fq"].append("personnel_investigator_name:(%s)" % qstring)
                elif "contributor" in name.lower():
                    params["fq"].append(
                        "personnel_technical_name:(%s) OR personnel_metadata_author_name:(%s)"
                        % (qstring, qstring)
                    )
                elif "dc:source" in name:
                    params["fq"].append("related_url_landing_page:(%s)" % qstring)
                elif "format" in name.lower():
                    params["fq"].append("storage_information_file_format:(%s)" % qstring)
                elif "language" in name.lower():
                    params["fq"].append("dataset_language:(%s)" % qstring)
                elif "publisher" in name.lower():
                    params["fq"].append("dataset_citation_publisher:(%s)" % qstring)
                elif "rights" in name.lower():
                    params["fq"].append(
                        "use_constraint_identifier:(%s) OR use_constraint_license_text:(%s)"
                        % (qstring, qstring)
                    )

                elif "type" in name.lower():
                    print(f"got APISO type query with {name} set to {qstring}")
                    if qstring.lower() == "dataset":
                        params["fq"].append("isParent:false")
                    elif qstring.lower() == "series":
                        params["fq"].append("isParent:true")
 
                elif "apiso:ParentIdentifier" in name:
                    params["fq"].append(f'related_dataset:"{qstring}"')
                else:
                    if name in ["apiso:Anytext",'csw:AnyText']:
                        params["q"] = "full_text:(%s)" % qstring
    return params
