.. _baseprofile:

Base profile class
---------------------------------------------------------

Overview
^^^^^^^^
This is an extended base class for profile implementation.

This class is meant to make profile impletention simpler and to automate record writing based on the queryables fields.

Configuration
^^^^^^^^^^^^^

In order to use this class use ``pycsw.plugins.profiles.base_profile.base_profile`` as a base class for the created profile.
In the new class create an __init__ function that will call ``super().__init__`` with the folowing params:

* name : str
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

