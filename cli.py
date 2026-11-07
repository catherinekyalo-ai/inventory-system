"""CLI for the inventory API. Usage: python cli.py --help"""
import argparse
import os
import sys

import requests

BASE_URL = os.environ.get("INVENTORY_API_URL", "http://127.0.0.1:5000")


class CLIError(Exception):
    pass


def call(method, path, **kwargs):
    """Send a request to the API; raise CLIError on network/HTTP errors."""
    try:
        resp = requests.request(method, BASE_URL + path, timeout=15, **kwargs)
    except requests.RequestException as e:
        raise CLIError(f"Cannot reach API at {BASE_URL}: {e}")
    try:
        body = resp.json()
    except ValueError:
        raise CLIError("API returned invalid JSON")
    if resp.status_code >= 400:
        raise CLIError(body.get("error", f"HTTP {resp.status_code}"))
    return body


def show(item):
    print(f"[{item['id']}] {item['product_name']} | brand: {item.get('brands') or '-'} | "
          f"price: {item['price']:.2f} | stock: {item['stock']} | barcode: {item.get('barcode') or '-'}")
    if item.get("ingredients_text"):
        print(f"     ingredients: {item['ingredients_text']}")


def cmd_list(args):
    items = call("GET", "/inventory")
    if not items:
        print("Inventory is empty.")
    for i in items:
        show(i)


def cmd_view(args):
    show(call("GET", f"/inventory/{args.id}"))


def cmd_add(args):
    payload = {"product_name": args.name, "price": args.price, "stock": args.stock}
    if args.barcode:
        payload["barcode"] = args.barcode
    body = call("POST", "/inventory", json=payload)
    print("Added:")
    show(body["item"])
    if body.get("warning"):
        print(f"Warning: {body['warning']}")


def cmd_update(args):
    payload = {}
    if args.price is not None:
        payload["price"] = args.price
    if args.stock is not None:
        payload["stock"] = args.stock
    if not payload:
        raise CLIError("Provide --price and/or --stock")
    print("Updated:")
    show(call("PATCH", f"/inventory/{args.id}", json=payload))


def cmd_delete(args):
    print(call("DELETE", f"/inventory/{args.id}")["message"])


def cmd_find(args):
    params = {"barcode": args.barcode} if args.barcode else {"name": args.name}
    results = call("GET", "/lookup", params=params)["results"]
    if not results:
        print("No products found.")
    for p in results:
        print(f"{p['barcode']} | {p['product_name']} | {p['brands']}")


def build_parser():
    p = argparse.ArgumentParser(description="Inventory admin CLI")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all items").set_defaults(func=cmd_list)

    s = sub.add_parser("view", help="View one item")
    s.add_argument("id", type=int)
    s.set_defaults(func=cmd_view)

    s = sub.add_parser("add", help="Add an item")
    s.add_argument("--name", required=True)
    s.add_argument("--price", type=float, required=True)
    s.add_argument("--stock", type=int, required=True)
    s.add_argument("--barcode", help="Enrich details from OpenFoodFacts")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("update", help="Update price and/or stock")
    s.add_argument("id", type=int)
    s.add_argument("--price", type=float)
    s.add_argument("--stock", type=int)
    s.set_defaults(func=cmd_update)

    s = sub.add_parser("delete", help="Delete an item")
    s.add_argument("id", type=int)
    s.set_defaults(func=cmd_delete)

    s = sub.add_parser("find", help="Find a product on OpenFoodFacts")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--barcode")
    g.add_argument("--name")
    s.set_defaults(func=cmd_find)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except CLIError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
