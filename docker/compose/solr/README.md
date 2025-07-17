# pycsw with SOLR backend

## metno work

@epifiano and the team at metno did amazing work in their implementation of pycsw, this work is inspired by their work

- https://github.com/epifanio/adc-pycsw
- https://github.com/geopython/pygeofilter/blob/main/.github/workflows/main.yml#L41
- https://github.com/geopython/pygeofilter/blob/main/tests/backends/solr/test_evaluate.py
- https://github.com/magnarem/metsis-solr-configset

## security

Enable security in security.json, see also [solr documentation](https://solr.apache.org/guide/solr/latest/deployment-guide/authentication-and-authorization-plugins.html#using-security-json-with-solr)

## SOLR is used in QWC

Some links from their docs

- https://github.com/qwc-services/qwc-fulltext-search-service/?tab=readme-ov-file#solr-backend

## paradedb

paradedb is a plugin to postgres introducing FTS, including facets, so maybe no solr needed?

- https://github.com/paradedb/paradedb
- https://github.com/qwc-services/qwc-base-db/pull/10
- https://docs.paradedb.com/documentation/indexing/create_index