"""Simulated storage: an in-memory list shaped like OpenFoodFacts products."""
import copy

SEED_ITEMS = [
    {"id": 1, "barcode": "5449000000996", "product_name": "Coca-Cola",
     "brands": "Coca-Cola", "ingredients_text": "Carbonated water, sugar, caramel colour, phosphoric acid",
     "price": 1.50, "stock": 40},
    {"id": 2, "barcode": "3017620422003", "product_name": "Nutella",
     "brands": "Ferrero", "ingredients_text": "Sugar, palm oil, hazelnuts, skimmed milk powder, cocoa",
     "price": 4.25, "stock": 18},
    {"id": 3, "barcode": "0000000000001", "product_name": "Organic Almond Milk",
     "brands": "Silk", "ingredients_text": "Filtered water, almonds, cane sugar, sea salt",
     "price": 3.99, "stock": 25},
]

inventory = copy.deepcopy(SEED_ITEMS)


def reset():
    """Restore seed data (used by tests)."""
    inventory[:] = copy.deepcopy(SEED_ITEMS)


def next_id():
    return max((i["id"] for i in inventory), default=0) + 1


def find(item_id):
    return next((i for i in inventory if i["id"] == item_id), None)
