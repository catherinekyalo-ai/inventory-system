import requests
from unittest.mock import patch, Mock

import cli

ITEM = {"id": 1, "product_name": "Coca-Cola", "brands": "Coca-Cola",
        "price": 1.5, "stock": 40, "barcode": "123", "ingredients_text": ""}


def resp(body, status=200):
    m = Mock(status_code=status)
    m.json.return_value = body
    return m


@patch("cli.requests.request")
def test_list(mock_req, capsys):
    mock_req.return_value = resp([ITEM])
    assert cli.main(["list"]) == 0
    assert "Coca-Cola" in capsys.readouterr().out


@patch("cli.requests.request")
def test_view(mock_req, capsys):
    mock_req.return_value = resp(ITEM)
    assert cli.main(["view", "1"]) == 0
    assert mock_req.call_args[0][0] == "GET"


@patch("cli.requests.request")
def test_add_sends_payload(mock_req, capsys):
    mock_req.return_value = resp({"item": ITEM, "warning": "careful"}, 201)
    assert cli.main(["add", "--name", "Cola", "--price", "1.5", "--stock", "4", "--barcode", "123"]) == 0
    assert mock_req.call_args[1]["json"] == {"product_name": "Cola", "price": 1.5, "stock": 4, "barcode": "123"}
    assert "Warning: careful" in capsys.readouterr().out


@patch("cli.requests.request")
def test_update(mock_req):
    mock_req.return_value = resp(ITEM)
    assert cli.main(["update", "1", "--price", "2"]) == 0
    assert mock_req.call_args[0][0] == "PATCH"
    assert mock_req.call_args[1]["json"] == {"price": 2.0}


def test_update_needs_field(capsys):
    assert cli.main(["update", "1"]) == 1
    assert "Provide" in capsys.readouterr().err


@patch("cli.requests.request")
def test_delete(mock_req, capsys):
    mock_req.return_value = resp({"message": "Item 1 deleted"})
    assert cli.main(["delete", "1"]) == 0
    assert "deleted" in capsys.readouterr().out


@patch("cli.requests.request")
def test_find_by_name(mock_req, capsys):
    mock_req.return_value = resp({"results": [{"barcode": "1", "product_name": "Milk", "brands": "X"}]})
    assert cli.main(["find", "--name", "milk"]) == 0
    assert mock_req.call_args[1]["params"] == {"name": "milk"}
    assert "Milk" in capsys.readouterr().out


@patch("cli.requests.request")
def test_api_error_shown(mock_req, capsys):
    mock_req.return_value = resp({"error": "Item not found"}, 404)
    assert cli.main(["view", "99"]) == 1
    assert "Item not found" in capsys.readouterr().err


@patch("cli.requests.request", side_effect=requests.ConnectionError("refused"))
def test_server_down(_, capsys):
    assert cli.main(["list"]) == 1
    assert "Cannot reach API" in capsys.readouterr().err
