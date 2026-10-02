"""Public catalog boundary for Copy Minas Site 3.

Real products must be migrated from Site 2. This module deliberately returns no
fabricated product records while that source migration is pending.
"""


def get_public_products(limit=None):
    products = []

    if limit is None:
        return products

    return products[:limit]
