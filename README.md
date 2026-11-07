# Inventory Management System

Flask REST API + CLI for managing retail inventory, enriched with product data from the
[OpenFoodFacts API](https://openfoodfacts.github.io/openfoodfacts-server/api/).
Storage is a simulated in-memory array (resets on server restart).

## Setup
```bash
git clone https://github.com/catherinekyalo-ai/inventory-system.git && cd inventory-system
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run.py   # http://127.0.0.1:5000
```

## API
| Method | Endpoint | Description | Body / Params |
|---|---|---|---|
| GET | `/inventory` | All items | - |
| GET | `/inventory/<id>` | One item | - |
| POST | `/inventory` | Add item (enriches via OpenFoodFacts if `barcode` given) | `product_name`, `price`, `stock`, optional `barcode`, `brands`, `ingredients_text` |
| PATCH | `/inventory/<id>` | Update item | any of the above fields |
| DELETE | `/inventory/<id>` | Delete item | - |
| GET | `/lookup` | Search OpenFoodFacts | `?barcode=...` or `?name=...` |

Status codes: 200/201 success, 400 invalid input, 404 not found, 502 external API failure.

## CLI (server must be running)
```bash
python cli.py list
python cli.py view 1
python cli.py add --name "Nutella" --price 4.25 --stock 10 --barcode 3017620422003
python cli.py update 1 --price 2.10 --stock 30
python cli.py delete 2
python cli.py find --barcode 3017620422003
python cli.py find --name "almond milk"
```

## Tests
```bash
pytest -v
```
External API calls are mocked with `unittest.mock`; no network needed.
