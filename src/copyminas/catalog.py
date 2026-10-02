import json
from functools import lru_cache
from pathlib import Path


CATALOG_PATH = Path(__file__).with_name("data") / "catalog_site2.json"


@lru_cache(maxsize=1)
def _load_catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _category_map():
    return {
        category["id"]: category
        for category in _load_catalog()["categories"]
    }


def _hydrate_product(product):
    item = dict(product)
    category = _category_map().get(item["category_id"], {})
    item["id"] = item["source_id"]
    item["category"] = category.get("name", "Sem categoria")
    item["summary"] = item["description"] or "Informações do produto a confirmar."
    return item


def get_public_products(limit=None):
    products = [
        _hydrate_product(product)
        for product in _load_catalog()["products"]
    ]

    products.sort(
        key=lambda product: (
            not product.get("featured", False),
            product["category"],
            product["source_id"],
        )
    )

    if limit is not None:
        return products[:limit]

    return products


def get_public_categories():
    used = {product["category_id"] for product in _load_catalog()["products"]}

    return [
        dict(category)
        for category in _load_catalog()["categories"]
        if category["active"] and category["id"] in used
    ]


def get_product_by_slug(slug):
    for product in get_public_products():
        if product["slug"] == slug:
            return product

    return None
