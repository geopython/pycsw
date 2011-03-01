-- =================================================================
--
-- $Id$
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

-- per OGC Catalogue Service Implementation Specification 2.0.2
-- (http://portal.opengeospatial.org/files/?artifact_id=20555)
-- subclause 10.2.5.3 (Table 53)

create table records (
    -- core metadata properties
    title text,
    creator text,
    subject text,
    abstract text,
    publisher text,
    contributor text,
    modified text,
    date text,
    type text,
    format text,
    identifier text not null primary key,
    source text,
    language text,
    relation text,
    bbox text,
    rights text,
    -- additional properties
    csw_typename text,
    csw_anytext text
);
