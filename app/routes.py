"""REST routes for inventory CRUD plus external lookup."""
from flask import Blueprint, jsonify, request

from . import data, off_client

bp = Blueprint("inventory", __name__)


def error(msg, code):
    return jsonify({"error": msg}), code


def validate(body, partial=False):
    """Return (clean_dict, error_message). Partial=True for PATCH."""
    clean = {}
    if "product_name" in body or not partial:
        name = body.get("product_name")
        if not isinstance(name, str) or not name.strip():
            return None, "product_name is required and must be a non-empty string"
        clean["product_name"] = name.strip()
    if "price" in body or not partial:
        price = body.get("price")
        if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
            return None, "price is required and must be a number >= 0"
        clean["price"] = round(float(price), 2)
    if "stock" in body or not partial:
        stock = body.get("stock")
        if isinstance(stock, bool) or not isinstance(stock, int) or stock < 0:
            return None, "stock is required and must be an integer >= 0"
        clean["stock"] = stock
    for key in ("barcode", "brands", "ingredients_text"):
        if key in body:
            if not isinstance(body[key], str):
                return None, f"{key} must be a string"
            clean[key] = body[key]
    return clean, None


@bp.get("/inventory")
def list_items():
    return jsonify(data.inventory), 200


@bp.get("/inventory/<int:item_id>")
def get_item(item_id):
    item = data.find(item_id)
    return jsonify(item) if item else error("Item not found", 404)


@bp.post("/inventory")
def add_item():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error("Body must be a JSON object", 400)
    clean, err = validate(body)
    if err:
        return error(err, 400)
    item = {"id": data.next_id(), "barcode": "", "brands": "", "ingredients_text": "", **clean}
    warning = None
    # Enrich from OpenFoodFacts when a barcode is given
    if item["barcode"]:
        try:
            found = off_client.fetch_by_barcode(item["barcode"])
            if found:
                item["brands"] = item["brands"] or found["brands"]
                item["ingredients_text"] = item["ingredients_text"] or found["ingredients_text"]
            else:
                warning = "Barcode not found on OpenFoodFacts"
        except off_client.OFFError as e:
            warning = str(e)
    data.inventory.append(item)
    resp = {"item": item}
    if warning:
        resp["warning"] = warning
    return jsonify(resp), 201


@bp.patch("/inventory/<int:item_id>")
def update_item(item_id):
    item = data.find(item_id)
    if not item:
        return error("Item not found", 404)
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not body:
        return error("Body must be a non-empty JSON object", 400)
    clean, err = validate(body, partial=True)
    if err:
        return error(err, 400)
    item.update(clean)
    return jsonify(item), 200


@bp.delete("/inventory/<int:item_id>")
def delete_item(item_id):
    item = data.find(item_id)
    if not item:
        return error("Item not found", 404)
    data.inventory.remove(item)
    return jsonify({"message": f"Item {item_id} deleted"}), 200


@bp.get("/lookup")
def lookup():
    """GET /lookup?barcode=... or /lookup?name=... -> OpenFoodFacts results."""
    barcode, name = request.args.get("barcode"), request.args.get("name")
    if not barcode and not name:
        return error("Provide barcode or name query parameter", 400)
    try:
        if barcode:
            product = off_client.fetch_by_barcode(barcode)
            if not product:
                return error("Product not found on OpenFoodFacts", 404)
            return jsonify({"results": [product]}), 200
        return jsonify({"results": off_client.search_by_name(name)}), 200
    except off_client.OFFError as e:
        return error(str(e), 502)
