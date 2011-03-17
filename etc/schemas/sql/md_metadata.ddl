-- =================================================================
--
-- $Id: md_metadata.ddl 51 2011-03-17 18:20:18Z kalxas $
--
-- Authors: Tom Kralidis <tomkralidis@hotmail.com>
--
-- Copyright (c) 2011 Tom Kralidis
--
-- Permission is hereby granted, free of charge, to any person
-- obtaining a copy of this software and associated documentation
-- files (the "Software"), to deal in the Software without
-- restriction, including without limitation the rights to use,
-- copy, modify, merge, publish, distribute, sublicense, and/or sell
-- copies of the Software, and to permit persons to whom the
-- Software is furnished to do so, subject to the following
-- conditions:
--
-- The above copyright notice and this permission notice shall be
-- included in all copies or substantial portions of the Software.
--
-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
-- EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
-- OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
-- NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
-- HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
-- WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
-- FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
-- OTHER DEALINGS IN THE SOFTWARE.
--
-- =================================================================

-- per ISO19115, ISO19139 and INSPIRE Discovery Services Specifications
-- (http://portal.opengeospatial.org/files/?artifact_id=21460)
-- (http://inspire.jrc.ec.europa.eu/documents/Network_Services/Technical_Guidance_Discovery_Services_v2.12.pdf)

create table md_metadata ( 
    title                   text,
    abstract                text,
    type                    text,
    identifier              text not null primary key,
    topic_category          text,
    service_type            text,
    subject                 text,
    bbox                    text,
    publication_date        text,
    revision_date           text,
    creation_date           text,
    organization_name       text,
    lineage                 text,
    temporal_extend_begin   text,
    temporal_extend_end     text,
    language                text,
    distance_value          text,
    distance_unit           text,
    scale_denominator       text,
    specification_title     text,
    specification_date      text,
    specification_date_type text,
    degree                  text,
    access_constraints      text,
    other_constraints       text,
    classification          text,
    conditions_access_use   text,
    responsible_party_role  text,
    csw_typename            text,
    csw_anytext             text,
    -- additional iso queryables that are not required from INSPIRE
    format                  text,
    crs                     text 
);

