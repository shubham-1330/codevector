"""
Pytest configuration and shared fixtures.

The tests use a dedicated `codevector_test` database (or the URL in
TEST_DATABASE_URL) to avoid touching development data.

Create the test database once before running:
    createdb codevector_test
    # or: psql -c "CREATE DATABASE codevector_test;" postgres

Tables are created at the start of the session and dropped at the end.
Each individual test gets a clean table via TRUNCATE (autouse fixture).
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.models.product import Product  # noqa: F401

# ──────────────────────────────────────────────
#  Engine / schema
# ──────────────────────────────────────────────

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_products_created_at_id ON products (created_at DESC, id DESC)",
    "CREATE INDEX IF NOT EXISTS idx_products_category_created_at_id ON products (category, created_at DESC, id DESC)",
]


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(settings.TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        for sql in _CREATE_INDEXES_SQL:
            await conn.execute(text(sql))

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
def session_factory(test_engine):
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


# ──────────────────────────────────────────────
#  Per-test isolation
# ──────────────────────────────────────────────

@pytest_asyncio.fixture(autouse=True)
async def clean_tables(test_engine):
    """Truncate all data before each test for full isolation."""
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE products RESTART IDENTITY CASCADE"))
    yield


# ──────────────────────────────────────────────
#  DB session + HTTP client
# ──────────────────────────────────────────────

@pytest_asyncio.fixture
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient wired to the test database via dependency override."""

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = _override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ──────────────────────────────────────────────
#  Data helpers
# ──────────────────────────────────────────────

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import insert


async def insert_products(
    session: AsyncSession,
    *,
    count: int,
    category: str = "Electronics",
    base_time: datetime | None = None,
) -> list[dict]:
    """
    Insert `count` products with evenly spaced created_at timestamps.
    Returns the list of dicts that were inserted (newest first).
    """
    if base_time is None:
        base_time = datetime.now(timezone.utc)

    rows = [
        {
            "name": f"Product {i}",
            "category": category,
            "price": Decimal("9.99"),
            "created_at": base_time - timedelta(seconds=i),
            "updated_at": base_time - timedelta(seconds=i),
        }
        for i in range(count)
    ]
    await session.execute(insert(Product), rows)
    await session.commit()
    # Return newest-first (matching the API order)
    return rows
