.. _migration-guide:

pycsw Migration Guide
=====================

This page provides migration support across pycsw versions
over time to help with pycsw change management.

pycsw 2.x to 3.0 Migration
--------------------------

- the default configuration is now in YAML format.  See :ref:`configuration` for more information.  A helper script (``pycsw-admin.py migrate-config``) is included for updating from the previous configuration format
- the default endpoint for standalone deployments is now powered by ``pycsw/wsgi_flask.py`` (based on Flask) which supports ALL pycsw supported APIs. Make sure to use ``requirements-standalone.txt`` on top of ``requirements.txt`` to install Flask along with other standalone requirements
- the previously used ``pycsw/wsgi.py`` can still be used for CSW only deployments or for applications that need to integrate pycsw as a library (e.g. Django applications). PyPI installations still use ``requirements.txt`` which does not install Flask by default
- the default endpoint ``/`` is now OGC API - Records
- the CSW endpoint is now ``/csw``
- the OAI-PMH endpoint is now ``/oaipmh``
- the OpenSearch endpoint is now ``/opensearch``
- the SRU endpoint is now ``/sru``
- the ``pycsw-admin.py`` syntax has been updated

  - the ``-c`` flag has been replaced by subcommands (i.e. ``pycsw-admin.py -c load_records`` -> ``pycsw-admin.py load-records``)
  - subcommands have been slugified (i.e. ``load_records`` -> ``load-records``)
  - consult ``--help`` to use the updated CLI syntax
- use the following migration script to add new model fields

.. code-block:: sql

  alter table records add column metadata TEXT;
  alter table records add column metadata_type TEXT default 'application/xml';
  alter table records add column edition TEXT;
  alter table records add column contacts TEXT;
  alter table records add column themes TEXT;
  vacuum;

pycsw 1.x to 2.0 Migration
--------------------------

- the default CSW version is now 3.0.0.  CSW clients need to explicitly specify
  ``version=2.0.2`` for CSW 2 behaviour.  Also, pycsw administrators can use a
  WSGI wrapper to the pycsw API to force ``version=2.0.2`` on init of
  ``pycsw.server.Csw`` from the server.  See :ref:`csw-support` for more information.

- ``pycsw.server.Csw.dispatch_wsgi()`` previously returned the response
  content as a string.  2.0.0 introduces a compatability break to
  additionally return the HTTP status code along with the response as a list

.. code-block:: python

  from pycsw.server import Csw
  my_csw = Csw(my_dict)  # add: env=some_environ_dict,  version='2.0.2' if preferred

  # using pycsw 1.x
  response = my_csw.dispatch_wsgi()

  # using pycsw 2.0
  http_status_code, response = my_csw.dispatch_wsgi()

  # covering either pycsw version
  content = csw.dispatch_wsgi()

  # pycsw 2.0 has an API break:
  # pycsw < 2.0: content = xml_response
  # pycsw >= 2.0: content = [http_status_code, content]
  # deal with the API break
  if isinstance(content, list):  # pycsw 2.0+
      http_response_code, response = content

See :ref:`api` for more information.
