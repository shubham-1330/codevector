import logging
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from faker import Faker
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import insert, text

from app.api.routes import products as products_router
from app.core.config import settings
from app.core.exceptions import (
    AppError,
    app_error_handler,
    unhandled_exception_handler,
)
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine

setup_logging()

logger = logging.getLogger("codevector.main")

# ──────────────────────────────────────────────
#  Startup / shutdown
# ──────────────────────────────────────────────

_CREATE_INDEXES_SQL = [
    # Unfiltered newest-first traversal
    """
    CREATE INDEX IF NOT EXISTS idx_products_created_at_id
    ON products (created_at DESC, id DESC)
    """,
    # Category-filtered newest-first traversal
    """
    CREATE INDEX IF NOT EXISTS idx_products_category_created_at_id
    ON products (category, created_at DESC, id DESC)
    """,
]


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN001
    logger.info("Starting up %s", settings.APP_NAME)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for sql in _CREATE_INDEXES_SQL:
            await conn.execute(text(sql))
    logger.info("Database tables and indexes are ready")
    yield
    logger.info("Shutting down – disposing connection pool")
    await engine.dispose()


# ──────────────────────────────────────────────
#  Application
# ──────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Product browsing API with keyset (cursor-based) pagination. "
        "Correctly handles concurrent inserts without duplicates or gaps."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS – allow_credentials must be False when allow_origins=["*"] (browser spec)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):  # noqa: ANN001
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s → %d (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


# ──────────────────────────────────────────────
#  Routes
# ──────────────────────────────────────────────

@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "service": settings.APP_NAME}


@app.post("/seed", tags=["seed"])
async def seed_database(count: int = 500) -> dict:
    """Insert sample products. Max 1000 per call to avoid timeouts."""
    from app.models.product import Product

    _fake = Faker()
    _categories = [
        "Electronics", "Books", "Clothing", "Home & Garden",
        "Sports & Outdoors", "Toys & Games", "Food & Grocery",
        "Beauty & Personal Care", "Automotive", "Health & Wellness",
    ]
    _now = datetime.now(timezone.utc)
    count = min(count, 1000)

    rows = [
        {
            "name": _fake.catch_phrase(),
            "category": random.choice(_categories),
            "price": round(random.uniform(0.99, 9999.99), 2),
            "created_at": (ts := _now - timedelta(seconds=random.randint(0, 63072000))),
            "updated_at": ts,
        }
        for _ in range(count)
    ]

    async with engine.begin() as conn:
        await conn.execute(insert(Product), rows)
        result = await conn.execute(text("SELECT COUNT(*) FROM products"))
        total = result.scalar_one()

    return {"inserted": count, "total_in_db": total}


app.include_router(products_router.router, prefix="/products", tags=["products"])
