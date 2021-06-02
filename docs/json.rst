.. _json:

JSON Support
============

OARec
-----

pycsw fully supports the OARec JSON conformance class, which is the default
representation provided.

CSW
---

pycsw supports JSON support for ``DescribeRecord``, ``GetRecords`` and ``GetRecordById`` requests.  Adding ``outputFormat=application/json`` to your CSW request will return the response as a JSON representation.

