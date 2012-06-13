:orphan:

.. _faq:

FAQ
===

Can I use pycsw within my WSGI application?
-------------------------------------------

Yes.  pycsw can be deployed as both via traditional CGI or WSGI.  You can also integrate pycsw via `Django`_ views or `Pylons`_ controllers.

How do I perform CSW queries on FGDC metadata?
------------------------------------------------------- 

The CSW ``typename`` parameter allows a user to specify which types of metadata to query against (the default being ``csw:Record``).

To perform CSW queries against FGDC metadata, the ``typename`` parameter for FGDC metadata records must be set to ``fgdc:metadata``.  See :ref:`profiles` for valid ``typename`` parameters for all supported metadata.

How do I export my repository?
-------------------------------

Use the ``pycsw-admin.py`` utility to dump the records as XML documents to a directory:

.. code-block:: bash

  $ pycsw-admin.py -c export_records -f default.cfg -p /path/to/output_dir


.. _`Django`: https://www.djangoproject.com/
.. _`Pylons`: http://www.pylonsproject.org/

How do I add a custom metadata format?
--------------------------------------

pycsw provides a plugin framework in which you can implement a custom profile (see :ref:`profiles`)

How can I catalogue 'sets' of metadata?
---------------------------------------

Create a 'parent' metadata record from which all relevant metadata records (imagery, features) derive from via the same ``dc:source`` element of Dublin Core or ``gmd:parentIdentifier`` element of ISO 19139:2007.  Then, do a ``GetRecords`` request, filtering on the identifier of the parent metadata record.  Sample request:

.. code-block:: xml

  <?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>
  <csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" xmlns:ogc="http://www.opengis.net/ogc" service="CSW" version="2.0.2" resultType="results" startPosition="1" maxRecords="5" outputFormat="application/xml" outputSchema="http://www.opengis.net/cat/csw/2.0.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/cat/csw/2.0.2 http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd" xmlns:gml="http://www.opengis.net/gml" xmlns:gmd="http://www.isotc211.org/2005/gmd">
    <csw:Query typeNames="csw:Record">
      <csw:ElementSetName>brief</csw:ElementSetName>
      <csw:Constraint version="1.1.0">
        <ogc:Filter>
          <ogc:And>
	    <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>gmd:parentIdentifier</ogc:PropertyName>
              <ogc:PropertyName>$identifier</ogc:PropertyName>
	    </ogc:PropertyIsEqualTo>
            <ogc:BBOX>
              <ogc:PropertyName>ows:BoundingBox</ogc:PropertyName>
              <gml:Envelope>
                <gml:lowerCorner>47 -5</gml:lowerCorner>
                <gml:upperCorner>55 20</gml:upperCorner>
              </gml:Envelope>
            </ogc:BBOX>
          </ogc:And>
        </ogc:Filter>
      </csw:Constraint>
    </csw:Query>
  </csw:GetRecords>

The above query will search for all metadata records of the same ``gmd:parentIdentifier`` (identified by ``$identifier``) within a given area of interest.  The equivalent query can be done against ``dc:source`` with the same design pattern.


