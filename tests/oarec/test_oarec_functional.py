from http import HTTPStatus

import pytest

pytestmark = [
    pytest.mark.functional,
    pytest.mark.oarec
]


@pytest.mark.parametrize("endpoint, f_query_param, accept_header", [
    pytest.param("/", "json", "text/html"),
    pytest.param("/", None, "text/html"),
    pytest.param("/", "json", "application/json"),
    pytest.param("/", None, "application/json"),
    pytest.param("/openapi", "json", "text/html"),
    pytest.param("/openapi", None, "text/html"),
    pytest.param("/openapi", "json", "application/json"),
    pytest.param("/openapi", None, "application/json"),
    pytest.param("/conformance", "json", "text/html"),
    pytest.param("/conformance", None, "text/html"),
    pytest.param("/conformance", "json", "application/json"),
    pytest.param("/conformance", None, "application/json"),
    pytest.param("/collections", "json", "text/html"),
    pytest.param("/collections", None, "text/html"),
    pytest.param("/collections", "json", "application/json"),
    pytest.param("/collections", None, "application/json"),
    pytest.param("/collections/metadata:main", "json", "text/html"),
    pytest.param("/collections/metadata:main", None, "text/html"),
    pytest.param("/collections/metadata:main", "json", "application/json"),
    pytest.param("/collections/metadata:main", None, "application/json"),
    pytest.param("/collections/metadata:main/queryables", "json", "text/html"),
    pytest.param("/collections/metadata:main/queryables", None, "text/html"),
    pytest.param("/collections/metadata:main/queryables", "json", "application/json"),
    pytest.param("/collections/metadata:main/queryables", None, "application/json"),
    pytest.param("/collections/metadata:main/items", "json", "text/html"),
    pytest.param("/collections/metadata:main/items", None, "text/html"),
    pytest.param("/collections/metadata:main/items", "json", "application/json"),
    pytest.param("/collections/metadata:main/items", None, "application/json"),
])
def test_page_renders(oarec_client, endpoint, f_query_param, accept_header):
    query = {}
    if f_query_param is not None:
        query["f"] = f_query_param
    headers = {}
    if accept_header is not None:
        headers["Accept"] = accept_header
    response = oarec_client.get(
        endpoint, query_string=query or None, headers=headers or None)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize("f_query_param, accept_header", [
    pytest.param(None, "application/json"),
    pytest.param("json", "application/json"),
])
def test_landing_page_includes_link_to_collections(
        oarec_client, f_query_param, accept_header):
    query = {}
    if f_query_param is not None:
        query["f"] = f_query_param
    headers = {}
    if accept_header is not None:
        headers["Accept"] = accept_header
    response = oarec_client.get(
        "/", query_string=query or None, headers=headers or None)
    collection_links = [
        link for link in response.json["links"] if link["rel"] == "data"]
    assert len(collection_links) == 1
    collections_link = collection_links[0]
    assert collections_link["type"] == "application/json"
    expected_url = (
        f"{oarec_client.application.config['PYCSW_CONFIG']['server']['url']}/"
        f"collections?f=json"
    )
    assert collections_link["href"] == expected_url
