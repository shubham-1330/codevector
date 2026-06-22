"""
Tests for GET /products.

Covers:
  - Default listing
  - Custom limit
  - Category filtering
  - Cursor pagination (multi-page traversal)
  - No duplicates across pages
  - No skipped products after concurrent inserts
  - Invalid cursor → 400
  - Limit out of range → 422
  - has_more / next_cursor semantics
  - Empty result set
"""

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from tests.conftest import insert_products


# ──────────────────────────────────────────────
#  Helper
# ──────────────────────────────────────────────

async def fetch_all_pages(
    client: AsyncClient,
    *,
    limit: int = 10,
    category: str | None = None,
) -> list[dict]:
    """Traverse all pages and collect every product id in order."""
    params: dict = {"limit": limit}
    if category:
        params["category"] = category

    all_products = []
    while True:
        resp = await client.get("/products", params=params)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        all_products.extend(body["products"])
        if not body["has_more"]:
            break
        params["cursor"] = body["next_cursor"]

    return all_products


# ──────────────────────────────────────────────
#  Basic listing
# ──────────────────────────────────────────────

async def test_health_check(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_empty_database(client: AsyncClient):
    resp = await client.get("/products")
    assert resp.status_code == 200
    body = resp.json()
    assert body["products"] == []
    assert body["has_more"] is False
    assert body["next_cursor"] is None


async def test_default_limit(client: AsyncClient, db_session: AsyncSession):
    await insert_products(db_session, count=30)
    resp = await client.get("/products")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["products"]) == 20  # default limit
    assert body["has_more"] is True
    assert body["next_cursor"] is not None


async def test_custom_limit(client: AsyncClient, db_session: AsyncSession):
    await insert_products(db_session, count=15)
    resp = await client.get("/products", params={"limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["products"]) == 5
    assert body["has_more"] is True


async def test_products_ordered_newest_first(
    client: AsyncClient, db_session: AsyncSession
):
    base = datetime.now(timezone.utc)
    await insert_products(db_session, count=10, base_time=base)

    resp = await client.get("/products", params={"limit": 10})
    assert resp.status_code == 200
    products = resp.json()["products"]

    timestamps = [p["created_at"] for p in products]
    assert timestamps == sorted(timestamps, reverse=True), (
        "Products should be ordered newest-first"
    )


async def test_exact_page_size_no_has_more(
    client: AsyncClient, db_session: AsyncSession
):
    await insert_products(db_session, count=5)
    resp = await client.get("/products", params={"limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["products"]) == 5
    assert body["has_more"] is False
    assert body["next_cursor"] is None


async def test_fewer_than_limit_has_no_more(
    client: AsyncClient, db_session: AsyncSession
):
    await insert_products(db_session, count=3)
    resp = await client.get("/products", params={"limit": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["products"]) == 3
    assert body["has_more"] is False
    assert body["next_cursor"] is None


# ──────────────────────────────────────────────
#  Category filtering
# ──────────────────────────────────────────────

async def test_category_filter(client: AsyncClient, db_session: AsyncSession):
    await insert_products(db_session, count=10, category="Electronics")
    await insert_products(db_session, count=5, category="Books")

    resp = await client.get("/products", params={"limit": 100, "category": "Books"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["products"]) == 5
    assert all(p["category"] == "Books" for p in body["products"])


async def test_category_filter_nonexistent(
    client: AsyncClient, db_session: AsyncSession
):
    await insert_products(db_session, count=5, category="Electronics")
    resp = await client.get("/products", params={"category": "Unicorns"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["products"] == []
    assert body["has_more"] is False


# ──────────────────────────────────────────────
#  Cursor pagination
# ──────────────────────────────────────────────

async def test_cursor_pagination_no_duplicates(
    client: AsyncClient, db_session: AsyncSession
):
    await insert_products(db_session, count=25)

    all_products = await fetch_all_pages(client, limit=10)
    ids = [p["id"] for p in all_products]

    assert len(ids) == 25, "All 25 products should be returned"
    assert len(set(ids)) == len(ids), "No duplicate products across pages"


async def test_cursor_pagination_ordered(
    client: AsyncClient, db_session: AsyncSession
):
    await insert_products(db_session, count=25)

    all_products = await fetch_all_pages(client, limit=10)
    timestamps = [p["created_at"] for p in all_products]
    assert timestamps == sorted(timestamps, reverse=True)


async def test_cursor_pagination_covers_all_rows(
    client: AsyncClient, db_session: AsyncSession
):
    await insert_products(db_session, count=55)

    all_products = await fetch_all_pages(client, limit=20)
    assert len(all_products) == 55


async def test_cursor_pagination_with_category(
    client: AsyncClient, db_session: AsyncSession
):
    await insert_products(db_session, count=15, category="Electronics")
    await insert_products(db_session, count=10, category="Books")

    all_electronics = await fetch_all_pages(
        client, limit=7, category="Electronics"
    )
    assert len(all_electronics) == 15
    assert all(p["category"] == "Electronics" for p in all_electronics)


# ──────────────────────────────────────────────
#  Concurrent-insert stability
# ──────────────────────────────────────────────

async def test_new_inserts_do_not_cause_duplicates(
    client: AsyncClient, db_session: AsyncSession
):
    """
    Simulate a user paginating while new products are inserted between
    page requests.  New products are NEWER than the cursor anchor so they
    appear only on earlier pages (or a hypothetical refresh), not on
    subsequent pages already fetched.
    """
    base = datetime(2020, 1, 1, tzinfo=timezone.utc)
    await insert_products(db_session, count=20, base_time=base)

    # Load page 1
    resp1 = await client.get("/products", params={"limit": 10})
    assert resp1.status_code == 200
    body1 = resp1.json()
    page1_ids = {p["id"] for p in body1["products"]}
    cursor = body1["next_cursor"]

    # Insert newer products while user holds the cursor
    newer_base = datetime.now(timezone.utc)
    await insert_products(db_session, count=5, base_time=newer_base)

    # Load page 2 with the original cursor
    resp2 = await client.get("/products", params={"limit": 10, "cursor": cursor})
    assert resp2.status_code == 200
    body2 = resp2.json()
    page2_ids = {p["id"] for p in body2["products"]}

    assert page1_ids.isdisjoint(page2_ids), "No duplicates between page 1 and page 2"
    assert len(page2_ids) == 10, "Page 2 should still return the original 10 older products"


# ──────────────────────────────────────────────
#  Error handling
# ──────────────────────────────────────────────

async def test_invalid_cursor_returns_400(client: AsyncClient):
    resp = await client.get("/products", params={"cursor": "not-a-valid-cursor!!"})
    assert resp.status_code == 400
    body = resp.json()
    assert "error" in body


async def test_limit_zero_returns_422(client: AsyncClient):
    resp = await client.get("/products", params={"limit": 0})
    assert resp.status_code == 422


async def test_limit_too_large_returns_422(client: AsyncClient):
    resp = await client.get("/products", params={"limit": 101})
    assert resp.status_code == 422


async def test_negative_limit_returns_422(client: AsyncClient):
    resp = await client.get("/products", params={"limit": -1})
    assert resp.status_code == 422


# ──────────────────────────────────────────────
#  Response shape
# ──────────────────────────────────────────────

async def test_product_schema(client: AsyncClient, db_session: AsyncSession):
    await insert_products(db_session, count=1)
    resp = await client.get("/products", params={"limit": 1})
    assert resp.status_code == 200
    product = resp.json()["products"][0]

    assert "id" in product
    assert "name" in product
    assert "category" in product
    assert "price" in product
    assert "created_at" in product
    assert "updated_at" in product


async def test_cursor_is_opaque_string(client: AsyncClient, db_session: AsyncSession):
    await insert_products(db_session, count=5)
    resp = await client.get("/products", params={"limit": 3})
    assert resp.status_code == 200
    cursor = resp.json()["next_cursor"]
    # Must be a non-empty string that doesn't expose raw integers directly
    assert isinstance(cursor, str)
    assert len(cursor) > 10
    assert cursor.isdigit() is False
