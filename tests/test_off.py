import pytest
import requests
from unittest.mock import patch, Mock

from app import off_client


def mock_resp(json_data, status=200):
    m = Mock()
    m.json.return_value = json_data
    if status >= 400:
        m.raise_for_status.side_effect = requests.HTTPError("bad")
    return m


@patch("app.off_client.requests.get")
def test_barcode_found(mock_get):
    mock_get.return_value = mock_resp({"status": 1, "product": {
        "product_name": "Organic Almond Milk", "brands": "Silk",
        "ingredients_text": "Filtered water, almonds"}})
    p = off_client.fetch_by_barcode("999")
    assert p["product_name"] == "Organic Almond Milk" and p["barcode"] == "999"


@patch("app.off_client.requests.get")
def test_barcode_not_found(mock_get):
    mock_get.return_value = mock_resp({"status": 0})
    assert off_client.fetch_by_barcode("0") is None


@patch("app.off_client.requests.get", side_effect=requests.ConnectionError("x"))
def test_barcode_network_error(_):
    with pytest.raises(off_client.OFFError):
        off_client.fetch_by_barcode("1")


@patch("app.off_client.requests.get")
def test_search_by_name(mock_get):
    mock_get.return_value = mock_resp({"products": [
        {"code": "1", "product_name": "A", "brands": "B"},
        {"code": "2", "product_name": "C", "brands": "D"}]})
    results = off_client.search_by_name("milk")
    assert [r["barcode"] for r in results] == ["1", "2"]


@patch("app.off_client.requests.get")
def test_search_http_error(mock_get):
    mock_get.return_value = mock_resp({}, status=500)
    with pytest.raises(off_client.OFFError):
        off_client.search_by_name("milk")
