from http import HTTPStatus

import pytest

pytestmark = [
    pytest.mark.functional,
    pytest.mark.oarec
]


@pytest.mark.parametrize("f_query_param, accept_header", [
    pytest.param("json", "text/html"),
    pytest.param(None, "text/html"),
    pytest.param("json", "application/json"),
    pytest.param(None, "application/json"),
])
def test_landing_page_renders(oarec_client, f_query_param, accept_header):
    query = {}
    if f_query_param is not None:
        query["f"] = f_query_param
    headers = {}
    if accept_header is not None:
        headers["Accept"] = accept_header
    response = oarec_client.get(
        "/", query_string=query or None, headers=headers or None)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize("f_query_param, accept_header", [
    pytest.param("json", "text/html"),
    pytest.param(None, "text/html"),
    pytest.param("json", "application/json"),
    pytest.param(None, "application/json"),
])
def test_openapi_page_renders(oarec_client, f_query_param, accept_header):
    query = {}
    if f_query_param is not None:
        query["f"] = f_query_param
    headers = {}
    if accept_header is not None:
        headers["Accept"] = accept_header
    response = oarec_client.get(
        "/openapi", query_string=query or None, headers=headers or None)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize("f_query_param, accept_header", [
    pytest.param("json", "text/html"),
    pytest.param(None, "text/html"),
    pytest.param("json", "application/json"),
    pytest.param(None, "application/json"),
])
def test_conformance_page_renders(oarec_client, f_query_param, accept_header):
    query = {}
    if f_query_param is not None:
        query["f"] = f_query_param
    headers = {}
    if accept_header is not None:
        headers["Accept"] = accept_header
    response = oarec_client.get(
        "/conformance", query_string=query or None, headers=headers or None)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize("f_query_param, accept_header", [
    pytest.param("json", "text/html"),
    pytest.param(None, "text/html"),
    pytest.param("json", "application/json"),
    pytest.param(None, "application/json"),
])
def test_collections_page_renders(oarec_client, f_query_param, accept_header):
    query = {}
    if f_query_param is not None:
        query["f"] = f_query_param
    headers = {}
    if accept_header is not None:
        headers["Accept"] = accept_header
    response = oarec_client.get(
        "/collections", query_string=query or None, headers=headers or None)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize("f_query_param, accept_header", [
    pytest.param("json", "text/html"),
    pytest.param(None, "text/html"),
    pytest.param("json", "application/json"),
    pytest.param(None, "application/json"),
])
def test_collection_page_renders(oarec_client, f_query_param, accept_header):
    query = {}
    if f_query_param is not None:
        query["f"] = f_query_param
    headers = {}
    if accept_header is not None:
        headers["Accept"] = accept_header
    response = oarec_client.get(
        "/collections/metadata:main",
        query_string=query or None,
        headers=headers or None
    )
    assert response.status_code == HTTPStatus.OK
