import json

from dateutil import parser as dparser
import logging


# Configure the logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

    
    
class QueryHandler:
    def __init__(self, adc_collection_filter="ADC NMAP CC APPL DAM DOKI"):
        # Initialize parameters for SOLR query
        #self.logger = Logger()
        self.and_append = False
        self.or_append = False
        self.OR_inside_AND = False
        self.adc_collection_filter = adc_collection_filter
        self.and_group = ["AND"]
        self.or_group = ["OR"]
        self.or_group_l2 = ["OR2"]
        self.and_group_l2 = ["AND2"]
        self.nested_level = 1
        self.nested_query = {"":""}
        self.params = {
            "q": "*:*",
            "q.op": "OR",
            "start": 0,
            "rows": 10,
            "fq": [
                f"metadata_status:Active",
                f"collection:({self.adc_collection_filter})",
            ],
        }

    def query(
        self, constraint, sortby=None, typenames=None, maxrecords=10, startposition=0
    ):
        """
        Query records from underlying repository.

        :param constraint: Dictionary containing the CSW query constraints.
        :param sortby: Optional sorting criteria.
        :param typenames: Optional type names.
        :param maxrecords: Maximum number of records to return (deprecated).
        :param startposition: Starting position for pagination.
        :return: SOLR query parameters.
        """
        logging.debug("Calling query: %s", json.dumps(constraint, indent=4))

        # Only add query constraint if we have some, else return all records
        if constraint:
            self.handle_ogc_filter(constraint["_dict"]["ogc:Filter"])
        self.format_query_param()
        return self.params

    def handle_ogc_filter(self, filter_dict):
        """
        Handle OGC filters and constraints.

        :param filter_dict: Dictionary containing the OGC filter.
        """
        logging.debug("handling filter: %s", json.dumps(filter_dict, indent=4))
        if isinstance(filter_dict, dict):
            for key in filter_dict:
                if key == "ogc:And":
                    logging.debug("Calling handle_and on: %s", json.dumps(filter_dict[key], indent=4))
                    self.handle_and(filter_dict[key])
                elif key == "ogc:Or":
                    logging.debug("Calling handle_or on: %s", json.dumps(filter_dict[key], indent=4))
                    self.handle_or(filter_dict[key])
                else:
                    logging.debug("Calling parse_constraint on: %s", json.dumps(filter_dict[key], indent=4))
                    logging.debug("parsing constraint:: %s", json.dumps(filter_dict, indent=4))
                    self.parse_constraint(filter_dict)
        elif isinstance(filter_dict, list):
            for item in filter_dict:
                self.handle_ogc_filter(item)


    def handle_or(self, or_list):
        """
        Handle OGC Or filters.

        :param or_list: List containing OGC Or constraints.
        """
        logging.debug("Handling OR group: %s", json.dumps(or_list, indent=4))
        if self.nested_level ==  1:
            self.or_group = ["OR"]
        elif self.nested_level ==  2:
            if "OR" in self.nested_query:
                self.or_group = self.or_group
                logging.debug("GOT OR INSIDE OR:: %s", json.dumps(self.nested_query, indent=4))
                # print("GOT OR INSIDE OR: ", self.nested_query)
            if "AND" in self.nested_query:
                logging.debug("GOT OR INSIDE AND:: %s", json.dumps(self.nested_query, indent=4))
                # print("GOT OR INSIDE AND: ", self.nested_query)
                self.or_group = self.and_group
        self.or_append = True
        self.and_append = False
        # self.OR_inside_AND = False
        if isinstance(or_list, dict) and len(or_list.keys()) == 1:
            key, value = next(iter(or_list.items()))
            if key == "ogc:And":
                self.handle_and(value)
            elif key == "ogc:Or":
                self.handle_or(value)
            else:
                if isinstance(or_list[key], list):
                    for i, v in enumerate(or_list[key]):
                        self.parse_constraint({key: or_list[key][i]}, append=True)
                else:
                    self.parse_constraint(or_list)
        elif isinstance(or_list, dict) and len(or_list.keys()) == 2:
            for i in or_list:
                if isinstance(or_list[i], dict):
                    key, value = next(iter(or_list[i].items()))
                    if i == "ogc:And":
                        self.handle_and(or_list[i])
                    elif i == "ogc:Or":
                        self.handle_or(or_list[i])
                    else:
                        self.parse_constraint({i: or_list[i]})
        elif isinstance(or_list, dict) and len(or_list.keys()) == 3:
            for i in or_list:
                key, value = next(iter(or_list[i].items()))
                # print('nested level', i, or_list[i], key, or_list[i], "\n")
                if i == "ogc:And":
                    self.nested_level = 2
                    self.nested_query = {"OR": 2}
                    logging.debug("got AND inside OR")
                    # print("got AND inside OR")
                    self.handle_and(or_list[i])
                elif i == "ogc:Or":
                    self.nested_level = 2
                    self.nested_query = {"OR": 2}
                    # print("got OR inside OR")
                    logging.debug("got OR inside OR")
                    self.handle_or(or_list[i])
                else:
                    self.nested_level = 1
                    # print(f"got {i} constraint inside OR")
                    logging.debug(f"got {i} constraint inside OR")
                    self.or_append = True
                    self.parse_constraint({i: or_list[i]})
                    
                # if isinstance(or_list[i][key], dict):
                #     for j in or_list[i]:
                #         if isinstance(or_list[i][j], dict):
                #             #print("handling as a dict: ", or_list[i][j])
                #             if i == "ogc:And":
                #                 self.OR_inside_AND = False
                #                 self.handle_and(or_list[i])
                #             elif i == "ogc:Or":
                #                 self.OR_inside_AND = True
                #                 self.handle_or(or_list[i])
                #             else:
                #                 self.parse_constraint({i: or_list[i]})
                #         elif isinstance(or_list[i][j], list):
                #             # self.or_group_l2 = []
                #             self.or_append = True
                #             for item in or_list[i][j]:
                #                 #print('attempt to pass items from level 2: ', key, item)
                #                 self.parse_constraint({key: item})
        elif isinstance(or_list, list):
            if self.nested_level == 2:
                if "OR" in self.nested_query:
                    self.or_group = self.or_group
                if "AND" in self.nested_query:
                    self.or_group = self.and_group
            else:
                self.or_group = []
            self.or_append = True
            for item in or_list:
                self.handle_ogc_filter(item)

                
    def handle_and(self, and_list):
        """
        Handle OGC And filters.

        :param or_list: List containing OGC Or constraints.
        """
        logging.debug("Handling AND group: %s", json.dumps(and_list, indent=4))


        if self.nested_level ==  1:
            self.and_group = ["AND"]
        elif self.nested_level ==  2:
            if "OR" in self.nested_query:
                self.and_group = self.and_group
                logging.debug("GOT OR INSIDE OR: %s", json.dumps(self.nested_query, indent=4))
                # print("GOT OR INSIDE OR: ", self.nested_query)
            if "AND" in self.nested_query:
                # print("GOT AND INSIDE OR: ", self.nested_query)
                logging.debug("GOT AND INSIDE OR: %s", json.dumps(self.nested_query, indent=4))
                self.and_group = self.or_group
        
        #if self.nested_level ==  1:
        #    self.and_group = ["AND"]
        self.and_append = True
        self.or_append = False
        if isinstance(and_list, dict) and len(and_list.keys()) == 1:
            logging.debug("LENGTH 1")
            key, value = next(iter(and_list.items()))
            if key == "ogc:And":
                self.handle_and(value)
            elif key == "ogc:Or":
                self.handle_or(value)
            else:
                if isinstance(and_list[key], list):
                    for i, v in enumerate(and_list[key]):
                        self.parse_constraint({key: and_list[key][i]}, append=True)
                else:
                    self.parse_constraint(and_list)
        elif isinstance(and_list, dict) and len(and_list.keys()) == 2:
            logging.debug("LENGTH 2")
            for i in and_list:
                if isinstance(and_list[i], dict):
                    key, value = next(iter(and_list[i].items()))
                    if i == "ogc:And":
                        self.handle_and(and_list[i])
                    elif i == "ogc:Or":
                        self.handle_or(and_list[i])
                    else:
                        self.parse_constraint({i: and_list[i]})
        elif isinstance(and_list, dict) and len(and_list.keys()) == 3:
            logging.debug("LENGTH 3")
            for i in and_list:
                key, value = next(iter(and_list[i].items()))
                # print('nested level', i, or_list[i], key, or_list[i], "\n")
                if i == "ogc:And":
                    self.nested_level = 2
                    print("got AND inside AND")
                    self.handle_and(and_list[i])
                elif i == "ogc:Or":
                    self.nested_level = 2
                    self.nested_query = {"AND": 2}
                    print("got OR inside AND")
                    self.handle_or(and_list[i])
                else:
                    self.nested_level = 1
                    print(f"got {i} constraint inside AND")
                    self.and_append = True
                    self.parse_constraint({i: and_list[i]})
                    
                # if isinstance(or_list[i][key], dict):
                #     for j in or_list[i]:
                #         if isinstance(or_list[i][j], dict):
                #             #print("handling as a dict: ", or_list[i][j])
                #             if i == "ogc:And":
                #                 self.OR_inside_AND = False
                #                 self.handle_and(or_list[i])
                #             elif i == "ogc:Or":
                #                 self.OR_inside_AND = True
                #                 self.handle_or(or_list[i])
                #             else:
                #                 self.parse_constraint({i: or_list[i]})
                #         elif isinstance(or_list[i][j], list):
                #             # self.or_group_l2 = []
                #             self.or_append = True
                #             for item in or_list[i][j]:
                #                 #print('attempt to pass items from level 2: ', key, item)
                #                 self.parse_constraint({key: item})
        elif isinstance(and_list, list):
            if self.nested_level == 2:
                self.and_group = self.and_group
            else:
                self.and_group = []
            self.and_append = True
            for item in or_list:
                self.handle_ogc_filter(item)

    def parse_constraint(self, constraint, append=False):
        """
        Parse individual OGC constraints.

        :param constraint: Dictionary containing the OGC constraint.
        """
        logging.debug("Parsing CONSTRAINT: %s", json.dumps(constraint, indent=4))
        if "ogc:PropertyIsLike" in constraint:
            self.parse_PropertyIsLike(constraint, append)
        elif "ogc:BBOX" in constraint:
            self.parse_BBOX(constraint)
        elif "ogc:PropertyIsGreaterThanOrEqualTo" in constraint:
            self.parse_PropertyIsGreaterThanOrEqualTo(constraint)
        elif "ogc:PropertyIsLessThanOrEqualTo" in constraint:
            self.parse_PropertyIsLessThanOrEqualTo(constraint)


    
    def parse_PropertyIsLike(self, constraint, append=False):
        """
        Parse PropertyIsLike constraints.

        :param constraint: Dictionary containing the PropertyIsLike constraint.
        """
        logging.debug("Found Property: %s", json.dumps(next(iter(constraint.keys())), indent=4))
        property_name = next(iter(constraint.keys()))
        qstring = constraint[property_name]["ogc:Literal"]
        name = constraint[property_name]["ogc:PropertyName"]

        # Convert wildcard characters from CSW to SOLR syntax
        qstring = qstring.replace("%", "*")
        qstring = qstring.replace("_", "?")

                
        if "title" in name.lower():
            self.add_to_params(f'title:("{qstring}")')
        elif "abstract" in name.lower():
            self.add_to_params(f'abstract:("{qstring}")')
        elif "subject" in name.lower():
            self.add_to_params(f'keywords_keyword:("{qstring}")')
        elif "creator" in name.lower():
            self.add_to_params(f'personnel_investigator_name:("{qstring}")')
        elif "contributor" in name.lower():
            self.add_to_params(
                f'(personnel_technical_name:("{qstring}") OR personnel_metadata_author_name:("{qstring}"))'
            )
        elif "dc:source" in name:
            self.add_to_params(f'related_url_landing_page:("{qstring}")')
        elif "format" in name.lower():
            self.add_to_params(f'storage_information_file_format:("{qstring}")')
        elif "language" in name.lower():
            self.add_to_params(f'dataset_language:("{qstring}")')
        elif "publisher" in name.lower():
            self.add_to_params(f'dataset_citation_publisher:("{qstring}")')
        elif "rights" in name.lower():
            self.add_to_params(
                f'(use_constraint_identifier:("{qstring}") OR use_constraint_license_text:("{qstring}"))'
            )
        elif "type" in name.lower():
            if qstring.lower() == "dataset":
                self.add_to_params("isParent:false")
            elif qstring.lower() == "series":
                self.add_to_params("isParent:true")
        elif "apiso:ParentIdentifier" in name:
            self.add_to_params(f'related_dataset:"{qstring}"')
        else:
            if name in ["apiso:AnyText", "csw:AnyText"]:
                if not append:
                    self.params["q"] = f'full_text:("{qstring}")'
                else:
                    self.add_to_params(f'full_text:"{qstring}"')



    # ADD a check on the value
    # use a default time to fall off if the date/time 
    # dtdef = parse(temporalinput, 
    # default=datetime(1000, 1, 1, 12, 0, tzinfo=timezone.utc))
    # re.match(r'^\d{4}$', temporalinput)
    def parse_PropertyIsGreaterThanOrEqualTo(self, constraint):
        """
        Parse PropertyIsGreaterThanOrEqualTo constraints.

        :param constraint: Dictionary containing the PropertyIsGreaterThanOrEqualTo constraint.
        """
        if "ogc:PropertyIsGreaterThanOrEqualTo" in constraint:
            begin = constraint["ogc:PropertyIsGreaterThanOrEqualTo"]["ogc:Literal"]
            datestring = dparser.parse(begin)
            self.add_to_params(
                f"temporal_extent_start_date:[{datestring.strftime('%Y-%m-%dT%H:%M:%SZ')} TO *]"
            )

    def parse_PropertyIsLessThanOrEqualTo(self, constraint):
        """
        Parse PropertyIsLessThanOrEqualTo constraints.

        :param constraint: Dictionary containing the PropertyIsLessThanOrEqualTo constraint.
        """
        if "ogc:PropertyIsLessThanOrEqualTo" in constraint:
            end = constraint["ogc:PropertyIsLessThanOrEqualTo"]["ogc:Literal"]
            datestring = dparser.parse(end)
            self.add_to_params(
                f"temporal_extent_end_date:[* TO {datestring.strftime('%Y-%m-%dT%H:%M:%SZ')}]"
            )

    def parse_BBOX(self, constraint):
        """
        Parse BBOX constrain3ts.

        :param constraint: Dictionary containing the BBOX constraint.
        """
        if "ogc:BBOX" in constraint:
            bbox = constraint["ogc:BBOX"]["gml:Envelope"]
            lc = [float(i) for i in bbox["gml:lowerCorner"].strip().split()]
            uc = [float(i) for i in bbox["gml:upperCorner"].strip().split()]

            min_x, max_x, min_y, max_y = lc[1], uc[1], lc[0], uc[0]
            envelope = f"ENVELOPE({min_y},{max_y},{max_x},{min_x})"
            solr_bbox_query = (
                "{!field f=bbox score=overlapRatio}" + f"Within({envelope})"
            )
            self.add_to_params(solr_bbox_query)

    def add_to_params(self, query):
        print("add_to_params: \n", query)
        if query not in self.params["fq"]:
            if self.and_append:
                if query not in self.and_group:
                    self.and_group.append(query)
                    if self.and_group not in self.params["fq"]:
                        self.params["fq"].append(self.and_group)
            elif self.or_append:
                if query not in self.or_group:
                    if self.nested_level == 2:
                        print("self.or_group_l2", self.or_group_l2, "query", query)
                        if query not in self.or_group_l2:
                            self.or_group_l2.append(query)
                            if self.or_group_l2 not in self.or_group:
                                self.or_group.append(self.or_group_l2)
                    else:
                        self.or_group.append(query)
                    if self.or_group not in self.params["fq"]:
                        self.params["fq"].append(self.or_group)
            else:
                self.params["fq"].append(query)


    def format_query_param(self):
        operators = {"OR": " OR ", "AND": " AND "}
        for i, v in enumerate(self.params["fq"]):
            if isinstance(v, list) and v[0] in operators:
                # Get the operator and the join string from the dictionary
                operator, join_str = v[0], operators[v[0]]
                # Remove the first element (the operator) and join the rest with the join string
                if operator in {"OR": " OR "}:
                    formatted_query = f"""({join_str.join(item.replace('"', '') for item in v[1:])})"""
                if operator in {"AND": " AND "}:
                    formatted_query = f"""{join_str.join(item.replace('"', '') for item in v[1:])}"""
                self.params["fq"][i] = formatted_query
    
    # def format_query_param(self):
    #     operators = {"OR": " OR ", "AND": " AND "}
    #     for i, v in enumerate(self.params["fq"]):
    #         if isinstance(v, list) and v[0] in operators:
    #             # Get the operator and the join string from the dictionary
    #             operator, join_str = v[0], operators[v[0]]
    #             # Remove the first element (the operator) and join the rest with the join string
    #             if operator in {"OR": " OR "}:
    #                 formatted_query = f"({join_str.join(item.replace('"', '') for item in v[1:])})"
    #             elif operator in {"AND": " AND "}:
    #                 formatted_query = f"{join_str.join(item.replace('"', '') for item in v[1:])}"
    #             self.params["fq"][i] = formatted_query
