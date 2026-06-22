"""
Seed script – inserts ~200 000 products in efficient bulk batches.

Usage:
    cd backend
    python -m seed.seed

Environment:
    DATABASE_URL  (from .env or shell)

The script is re-runnable: existing rows are left in place and the
auto-increment sequence continues from wherever it stopped. To reset,
truncate the table first:
    psql $DATABASE_URL -c "TRUNCATE products RESTART IDENTITY;"
"""

import asyncio
import logging
import random
import sys
import time
from datetime import datetime, timedelta, timezone

from faker import Faker
from sqlalchemy import insert, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.models.product import Product  # noqa: F401 – registers the mapper

setup_logging()
logger = logging.getLogger("codevector.seed")

fake = Faker()

CATEGORIES: list[str] = [
    "Electronics",
    "Books",
    "Clothing",
    "Home & Garden",
    "Sports & Outdoors",
    "Toys & Games",
    "Food & Grocery",
    "Beauty & Personal Care",
    "Automotive",
    "Health & Wellness",
]

TOTAL_PRODUCTS: int = 200_000
BATCH_SIZE: int = 5_000

# Spread timestamps over the past two years so pagination ordering is
# interesting (many different created_at values).
_TWO_YEARS_SECONDS: int = 2 * 365 * 24 * 3600
_NOW = datetime.now(timezone.utc)


def _random_timestamp() -> datetime:
    offset = timedelta(seconds=random.randint(0, _TWO_YEARS_SECONDS))
    return _NOW - offset


def _build_batch(size: int) -> list[dict]:
    return [
        {
            "name": fake.catch_phrase(),
            "category": random.choice(CATEGORIES),
            "price": round(random.uniform(0.99, 9_999.99), 2),
            "created_at": (ts := _random_timestamp()),
            "updated_at": ts,
        }
        for _ in range(size)
    ]


async def run_seed(total: int = TOTAL_PRODUCTS, batch_size: int = BATCH_SIZE) -> None:
    logger.info("Connecting to %s", settings.DATABASE_URL.split("@")[-1])
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        logger.info("Ensuring schema exists…")
        await conn.run_sync(Base.metadata.create_all)

    batches = (total + batch_size - 1) // batch_size
    inserted = 0
    t0 = time.perf_counter()

    logger.info(
        "Seeding %d products in %d batches of %d…",
        total,
        batches,
        batch_size,
    )

    async with engine.begin() as conn:
        for batch_num in range(batches):
            size = min(batch_size, total - inserted)
            data = _build_batch(size)
            await conn.execute(insert(Product), data)
            inserted += size
            elapsed = time.perf_counter() - t0
            logger.info(
                "Batch %d/%d complete – %d/%d rows (%.1f s elapsed)",
                batch_num + 1,
                batches,
                inserted,
                total,
                elapsed,
            )

    # Report row count
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM products"))
        count = result.scalar_one()

    await engine.dispose()
    total_time = time.perf_counter() - t0
    logger.info(
        "Seed complete. Table now contains %d rows (%.1f s, %.0f rows/s).",
        count,
        total_time,
        total / total_time,
    )


if __name__ == "__main__":
    asyncio.run(run_seed())
