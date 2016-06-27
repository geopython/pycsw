.. _csw-support:

CSW Support
===========

Versions
--------

pycsw supports both CSW 2.0.2 and 3.0.0 versions by default.  In alignment with
the CSW specifications, the default version returned is the latest supported
version.  That is, pycsw will always behave like a 3.0.0 CSW unless the client
explicitly requests a 2.0.2 CSW.

The sample URLs below provide examples of how requests behaves against
various/missing/default version parameters.

.. code-block:: bash

  http://localhost/csw  # returns 3.0.0 Capabilities
  http://localhost/csw?service=CSW&request=GetCapabilities  # returns 3.0.0 Capabilities
  http://localhost/csw?service=CSW&version=2.0.2&request=GetCapabilities  # returns 2.0.2 Capabilities
  http://localhost/csw?service=CSW&version=3.0.0&request=GetCapabilities  # returns 3.0.0 Capabilities

Request Examples
----------------

The best place to look for sample requests is within the `tests/` directory,
which provides numerous examples of all supported APIs and requests.

Additional examples:

- `Data.gov CSW HowTo v2.0`_
- `pycsw Quickstart on OSGeoLive`_

.. _`pycsw Quickstart on OSGeoLive`: http://live.osgeo.org/en/quickstart/pycsw_quickstart.html
.. _`Data.gov CSW HowTo v2.0`: https://gist.github.com/kalxas/6ecb06d61cdd487dc7f9
