.. _migration-guide:

pycsw Migration Guide
=====================

This page provides migration support across pycsw versions
over time to help with pycsw change management.

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
