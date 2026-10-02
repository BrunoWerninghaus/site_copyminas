import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from flask import current_app

from src.copyminas.db import DatabaseUnavailable, open_database


DATA_DIR = Path(__file__).with_name("data")
FIXTURE_PATH = DATA_DIR / "catalog_site2.json"
PRESENTATION_PATH = DATA_DIR / "catalog_presentation.json"


def _slugify(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or "produto"


def _parse_specifications(raw):
    if raw is None:
        return []

    if isinstance(raw, (list, tuple)):
        return [str(item).strip() for item in raw if str(item).strip()]

    if isinstance(raw, dict):
        return [
            f"{key}: {value}"
            for key, value in raw.items()
            if str(key).strip()
        ]

    text = str(raw).strip()
    if not text:
        return []

    if text[:1] in ("[", "{"):
        try:
            parsed = json.loads(text)
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed = None
        if parsed is not None:
            return _parse_specifications(parsed)

    return [
        line.strip(" -•\t")
        for line in text.splitlines()
        if line.strip(" -•\t")
    ]


def _image_list(row):
    images = []
    for key in ("imagem1", "imagem2", "imagem3", "imagem4", "imagem5"):
        value = (row.get(key) or "").strip()
        if not value:
            continue
        value = value.replace("\\", "/").lstrip("/")
        if value.startswith("static/"):
            value = value[len("static/"):]
        images.append(value)
    return images


@lru_cache(maxsize=1)
def _presentation_data():
    try:
        return json.loads(PRESENTATION_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {"products": {}}


def _presentation_for(product_id):
    return _presentation_data().get("products", {}).get(str(product_id), {})


def _hydrate_database_product(row):
    images = _image_list(row)
    description = (row.get("descricao") or "").strip()
    presentation = _presentation_for(row["id"])

    return {
        "id": row["id"],
        "source_id": row["id"],
        "slug": presentation.get("slug") or _slugify(row["nome"]),
        "name": row["nome"],
        "source_name": row["nome"],
        "category_id": row["categoria_id"],
        "category": row.get("categoria") or "Sem categoria",
        "description": description or "Informações do produto a confirmar.",
        "summary": description or "Informações do produto a confirmar.",
        "specifications": _parse_specifications(row.get("espec")),
        "images": images,
        "image_url": images[0] if images else None,
        "source_quantity": row.get("qtd"),
        "featured": bool(presentation.get("featured", False)),
    }


def _database_products():
    connection = open_database()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.id,
                    p.nome,
                    p.descricao,
                    p.imagem1,
                    p.imagem2,
                    p.imagem3,
                    p.imagem4,
                    p.imagem5,
                    p.espec,
                    p.qtd,
                    p.categoria_id,
                    c.nome AS categoria
                FROM produtos AS p
                INNER JOIN categorias AS c
                    ON c.id = p.categoria_id
                WHERE p.ativo = 1
                  AND c.ativo = 1
                ORDER BY c.nome ASC, p.id ASC
                """
            )
            return [_hydrate_database_product(row) for row in cursor.fetchall()]
    except Exception as exc:
        if isinstance(exc, DatabaseUnavailable):
            raise
        raise DatabaseUnavailable(
            f"MySQL main_bd catalog query failed: {exc}"
        ) from exc
    finally:
        connection.close()


def _fixture_products():
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    category_map = {
        category["id"]: category["name"]
        for category in data["categories"]
    }

    products = []
    for source in data["products"]:
        item = dict(source)
        item["id"] = item["source_id"]
        item["category"] = category_map.get(item["category_id"], "Sem categoria")
        item["summary"] = item.get("description") or "Informações do produto a confirmar."
        item["images"] = [item["image_url"]] if item.get("image_url") else []
        products.append(item)
    return products


def _products():
    source = current_app.config.get("CATALOG_SOURCE", "database")
    if source == "fixture":
        return _fixture_products()
    if source != "database":
        raise RuntimeError(f"Unsupported catalog source: {source}")
    return _database_products()


def get_public_products(limit=None):
    products = _products()

    # Product ordering is deterministic. When database-backed there is no
    # invented "featured" flag: the first records follow category + id order.
    products.sort(
        key=lambda product: (
            not product.get("featured", False),
            product["category"],
            product["id"],
        )
    )

    if limit is not None:
        return products[:limit]

    return products


def get_public_categories(products=None):
    categories = {}
    if products is None:
        products = get_public_products()

    for product in products:
        categories[product["category_id"]] = {
            "id": product["category_id"],
            "name": product["category"],
            "active": True,
        }

    return sorted(
        categories.values(),
        key=lambda category: category["name"],
    )


def get_product_by_slug(slug):
    for product in get_public_products():
        if product["slug"] == slug:
            return product
    return None
