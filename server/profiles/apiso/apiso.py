# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#                Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2011 Tom Kralidis
# Copyright (c) 2011 Angelos Tzotsos
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

import os
from lxml import etree
from server import profile, config, core_queryables, util

NAMESPACES = {
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd'
}

class APISO(profile.Profile):
    def __init__(self):
        profile.Profile.__init__(self, 'apiso', '1.0.0', 'ISO Metadata Application Profile', 'http://portal.opengeospatial.org/files/?artifact_id=21460', NAMESPACES['gmd'], 'gmd:MD_Metadata', NAMESPACES['gmd'])
        self.config=config.get_config(os.path.join('server', 'profiles', 'apiso', 'apiso.cfg'))
        
        self.corequeryables = core_queryables.CoreQueryables(self.config)
        

    def extend_core(self, model, namespaces, databases):
        ''' Extend core configuration '''

        # model
        model['operations']['DescribeRecord']['parameters']['typeName']['values'].append(self.typename)
        model['operations']['GetRecords']['parameters']['outputSchema']['values'].append(self.outputschema)
        model['operations']['GetRecords']['parameters']['typeNames']['values'].append(self.typename)
        model['operations']['GetRecordById']['parameters']['outputSchema']['values'].append(self.outputschema)
        model['constraints']['IsoProfiles'] = {}
        model['constraints']['IsoProfiles']['values'] = [self.namespace]
        model['operations']['GetRecords']['constraints']['SupportedISOQueryables'] = {
                        'values': ['apiso:RevisionDate','apiso:AlternateTitle','apiso:CreationDate','apiso:PublicationDate','apiso:OrganisationName','apiso:HasSecurityConstraints','apiso:Language','apiso:ResourceIdentifier','apiso:ParentIdentifier','apiso:KeywordType']
                    }
        model['operations']['GetRecords']['constraints']['AdditionalQueryables'] = {
                        'values': ['apiso:TopicCategory','apiso:ResourceLanguage','apiso:GeographicDescriptionCode','apiso:Denominator','apiso:DistanceValue','apiso:DistanceUOM','apiso:TempExtent_begin', 'apiso:TempExtent_end']
                    }

        # namespaces 
        namespaces.update(NAMESPACES)

        # databases

        databases[self.typename] = {}
        databases[self.typename]['db'] = self.config['repository']['db']
        databases[self.typename]['db_table'] = self.config['repository']['db_table']

    def get_extendedcapabilities(self):
        ''' Add child to ows:ExtendedCapabilities Element '''
        extended_capabilities = etree.Element(
                util.nspath_eval('ows:ExtendedCapabilities'))
        return extended_capabilities

    def get_schemacomponent(self):
        ''' Return schema as lxml.etree.Element '''
        schema = etree.parse(os.path.join(
                'server', 'profiles', 'apiso',
                'etc', 'schemas', 'ogc', 'iso', '19139',
                '20060504', 'gmd', 'identification.xsd')).getroot()

        return schema
