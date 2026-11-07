"""OpenFoodFacts client: look up products by barcode or name."""
import requests

BASE = "https://world.openfoodfacts.org"
HEADERS = {"User-Agent": "InventoryAdmin/1.0 (student project)"}
TIMEOUT = 10


class OFFError(Exception):
    """Raised when the external API fails or returns bad data."""


def _normalize(p):
    return {
        "barcode": p.get("code", ""),
        "product_name": p.get("product_name", ""),
        "brands": p.get("brands", ""),
        "ingredients_text": p.get("ingredients_text", ""),
    }


def fetch_by_barcode(barcode):
    """Return a normalized product dict, or None if not found."""
    try:
        r = requests.get(f"{BASE}/api/v2/product/{barcode}.json",
                         headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        raise OFFError(f"OpenFoodFacts request failed: {e}") from e
    if data.get("status") != 1:
        return None
    product = data["product"]
    product.setdefault("code", barcode)
    return _normalize(product)


def search_by_name(name, limit=5):
    """Return a list of normalized products matching name."""
    try:
        r = requests.get(f"{BASE}/cgi/search.pl", headers=HEADERS, timeout=TIMEOUT,
                         params={"search_terms": name, "search_simple": 1,
                                 "action": "process", "json": 1, "page_size": limit})
        r.raise_for_status()
        products = r.json().get("products", [])
    except (requests.RequestException, ValueError) as e:
        raise OFFError(f"OpenFoodFacts request failed: {e}") from e
    return [_normalize(p) for p in products[:limit]]
