# pycsw with SOLR backend



Enable security in security.json, see also [solr documentation](https://solr.apache.org/guide/solr/latest/deployment-guide/authentication-and-authorization-plugins.html#using-security-json-with-solr)


## SOLR is used in QWC

some links from their docs

- https://github.com/qwc-services/qwc-fulltext-search-service/?tab=readme-ov-file#solr-backend

## paradedb

paradedb is a plugin to postgres introducing FTS, including facets, so maybe no solr needed?

- https://github.com/paradedb/paradedb
- https://github.com/qwc-services/qwc-base-db/pull/10
- https://docs.paradedb.com/documentation/indexing/create_index