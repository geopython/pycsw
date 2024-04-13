.. _json:

JSON Support
============

OGC API - Records
-----------------

pycsw fully supports the OGC API - Records JSON conformance class, which is the default
representation provided.

CSW
---

pycsw supports JSON support for ``DescribeRecord``, ``GetRecords`` and ``GetRecordById`` requests.  Adding ``outputFormat=application/json`` to your CSW request will return the response as a JSON representation.

