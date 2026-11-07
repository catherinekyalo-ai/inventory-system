import pytest
from unittest.mock import patch

from app import create_app, data, off_client


@pytest.fixture
def client():
    data.reset()
    return create_app().test_client()


def test_get_all(client):
    r = client.get("/inventory")
    assert r.status_code == 200 and len(r.get_json()) == 3


def test_get_one(client):
    assert client.get("/inventory/1").get_json()["product_name"] == "Coca-Cola"


def test_get_missing(client):
    assert client.get("/inventory/999").status_code == 404


def test_post_valid(client):
    r = client.post("/inventory", json={"product_name": "Bread", "price": 2, "stock": 5})
    assert r.status_code == 201
    assert r.get_json()["item"]["id"] == 4
    assert len(client.get("/inventory").get_json()) == 4


@pytest.mark.parametrize("body", [
    {}, {"product_name": "", "price": 1, "stock": 1},
    {"product_name": "A", "price": -1, "stock": 1},
    {"product_name": "A", "price": 1, "stock": 1.5},
    {"product_name": "A", "price": "x", "stock": 1},
])
def test_post_invalid(client, body):
    assert client.post("/inventory", json=body).status_code == 400


def test_post_non_json(client):
    assert client.post("/inventory", data="nope").status_code == 400


@patch("app.routes.off_client.fetch_by_barcode")
def test_post_enriches_from_api(mock_fetch, client):
    mock_fetch.return_value = {"barcode": "123", "product_name": "X",
                               "brands": "BrandX", "ingredients_text": "water"}
    r = client.post("/inventory", json={"product_name": "X", "price": 1, "stock": 1, "barcode": "123"})
    item = r.get_json()["item"]
    assert item["brands"] == "BrandX" and item["ingredients_text"] == "water"


@patch("app.routes.off_client.fetch_by_barcode", side_effect=off_client.OFFError("down"))
def test_post_survives_api_failure(_, client):
    r = client.post("/inventory", json={"product_name": "X", "price": 1, "stock": 1, "barcode": "123"})
    assert r.status_code == 201 and "warning" in r.get_json()


def test_patch(client):
    r = client.patch("/inventory/1", json={"price": 9.99, "stock": 3})
    assert r.status_code == 200
    assert r.get_json()["price"] == 9.99 and r.get_json()["stock"] == 3


def test_patch_errors(client):
    assert client.patch("/inventory/999", json={"price": 1}).status_code == 404
    assert client.patch("/inventory/1", json={"price": -5}).status_code == 400
    assert client.patch("/inventory/1", json={}).status_code == 400


def test_delete(client):
    assert client.delete("/inventory/1").status_code == 200
    assert client.get("/inventory/1").status_code == 404
    assert client.delete("/inventory/1").status_code == 404


def test_lookup_requires_param(client):
    assert client.get("/lookup").status_code == 400


@patch("app.routes.off_client.fetch_by_barcode", return_value=None)
def test_lookup_not_found(_, client):
    assert client.get("/lookup?barcode=0").status_code == 404


@patch("app.routes.off_client.search_by_name", side_effect=off_client.OFFError("down"))
def test_lookup_api_failure(_, client):
    assert client.get("/lookup?name=milk").status_code == 502
