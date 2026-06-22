# CodeVector — Product Browsing API

A production-quality REST API for browsing ~200 000 products, ordered newest-first, with **cursor-based (keyset) pagination** that remains correct while data is inserted or updated concurrently.

---

## Architecture

```
backend/
├── app/
│   ├── api/
│   │   ├── dependencies.py      # FastAPI Depends wiring
│   │   └── routes/
│   │       └── products.py      # GET /products
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (env-driven)
│   │   ├── exceptions.py        # Domain errors + FastAPI handlers
│   │   └── logging.py           # Structured stdout logging
│   ├── db/
│   │   ├── base.py              # SQLAlchemy DeclarativeBase
│   │   └── session.py           # Async engine + session factory
│   ├── models/
│   │   └── product.py           # Product ORM model
│   ├── repositories/
│   │   └── product_repository.py  # Pure DB access (keyset query)
│   ├── schemas/
│   │   └── product.py           # Pydantic v2 request/response models
│   ├── services/
│   │   └── product_service.py   # Business logic, cursor encoding
│   ├── utils/
│   │   └── cursor.py            # Base64url cursor encode / decode
│   └── main.py                  # FastAPI app, middleware, startup
├── alembic/                     # Database migrations
├── seed/
│   └── seed.py                  # Bulk-insert 200 000 products
└── tests/
    ├── conftest.py              # Fixtures, test DB, HTTP client
    └── test_products.py         # Full API + pagination test suite
```

**Request flow:**

```
Client → FastAPI route handler
       → Pydantic query param validation
       → ProductService (cursor decode, has_more logic)
       → ProductRepository (async SQLAlchemy query)
       → PostgreSQL (index scan, no seq scan)
       → ProductService (encode next cursor)
       → Pydantic serialization → JSON response
```

---

## Technology Stack

| Layer | Choice |
|-------|--------|
| Web framework | FastAPI 0.111 |
| ORM | SQLAlchemy 2.x (async) |
| Database driver | asyncpg |
| Database | PostgreSQL 16 |
| Validation | Pydantic v2 |
| Server | Uvicorn |
| Migrations | Alembic |
| Fake data | Faker |
| Tests | pytest + pytest-asyncio + httpx |
| Container | Docker / Docker Compose |

---

## Environment Variables

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:password@localhost:5432/codevector` | Async SQLAlchemy connection string |
| `TEST_DATABASE_URL` | `…/codevector_test` | Used by pytest |
| `DEBUG` | `false` | Enables SQL echo + debug log level |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `MAX_PAGE_LIMIT` | `100` | Maximum allowed `limit` query param |
| `DEFAULT_PAGE_LIMIT` | `20` | Default page size when `limit` is omitted |
| `POSTGRES_USER` | `postgres` | Docker Compose PostgreSQL user |
| `POSTGRES_PASSWORD` | `password` | Docker Compose PostgreSQL password |
| `POSTGRES_DB` | `codevector` | Docker Compose PostgreSQL database |

---

## Running with Docker (recommended)

```bash
cd backend
cp .env.example .env          # adjust credentials if needed

docker compose up --build -d  # starts PostgreSQL + FastAPI

# Verify it's up
curl http://localhost:8000/health

# Seed 200 000 products (run once)
docker compose exec backend python -m seed.seed
```

The API will be available at **http://localhost:8000**.  
Interactive docs: **http://localhost:8000/docs**

---

## Running Locally

### Prerequisites

- Python 3.12+
- PostgreSQL 14+

### Setup

```bash
cd backend

# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env to match your local PostgreSQL credentials

# 4. Start the API (auto-creates tables and indexes on first run)
uvicorn app.main:app --reload
```

### Database migrations (Alembic)

The app auto-creates tables and indexes on startup via `Base.metadata.create_all`.
For controlled migrations in production, use Alembic instead:

```bash
# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Generate a new migration after model changes
alembic revision --autogenerate -m "describe change"
```

---

## Seed Script

Inserts exactly 200 000 products in batches of 5 000 using SQLAlchemy Core's
`insert()` (bulk, not one-by-one).  Timestamps are randomised over a 2-year
window so the ordering is interesting.

```bash
# Local
python -m seed.seed

# Docker
docker compose exec backend python -m seed.seed
```

The script is re-runnable; existing rows are left in place. To start fresh:

```sql
TRUNCATE products RESTART IDENTITY;
```

Expected output:

```
2024-01-01T12:00:00 | codevector.seed | INFO     | Seeding 200000 products in 40 batches of 5000…
2024-01-01T12:00:02 | codevector.seed | INFO     | Batch 1/40 complete – 5000/200000 rows (2.1 s elapsed)
…
2024-01-01T12:01:10 | codevector.seed | INFO     | Seed complete. Table now contains 200000 rows (70.4 s, 2842 rows/s).
```

---

## API Reference

### `GET /products`

Returns products ordered newest-first with cursor-based pagination.

**Query Parameters**

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `limit` | integer | `20` | 1–100 | Products per page |
| `category` | string | — | 1–100 chars | Filter by category (case-sensitive) |
| `cursor` | string | — | — | Opaque pagination token from previous response |

**Response**

```json
{
  "products": [
    {
      "id": 193847,
      "name": "Networked disintermediate portal",
      "category": "Electronics",
      "price": "149.99",
      "created_at": "2024-06-15T08:23:11.000000Z",
      "updated_at": "2024-06-15T08:23:11.000000Z"
    }
  ],
  "next_cursor": "eyJ0cyI6ICIyMDI0LTA2LTE1VDA4OjIzOjExWiIsICJpZCI6IDE5Mzg0N30",
  "has_more": true
}
```

**Paginating through results**

```bash
# Page 1
curl "http://localhost:8000/products?limit=20"

# Page 2 (pass next_cursor from page 1)
curl "http://localhost:8000/products?limit=20&cursor=<next_cursor>"

# Category filter with pagination
curl "http://localhost:8000/products?limit=20&category=Electronics"
curl "http://localhost:8000/products?limit=20&category=Electronics&cursor=<next_cursor>"
```

**Error responses**

| Status | Condition |
|--------|-----------|
| `400` | Cursor is malformed or tampered |
| `422` | `limit` is out of range (0 or >100) |
| `503` | Database unreachable |

### `GET /health`

Returns `{"status": "ok"}` with HTTP 200.

---

## Pagination Design

### Why not OFFSET?

`LIMIT 20 OFFSET 100` on a table with 200 000 rows requires PostgreSQL to
scan and discard 100 rows before returning 20.  Worse, if a new product is
inserted between page 1 and page 2 requests, the entire result set shifts:
the last item on page 1 reappears at the top of page 2 (duplicate), or an
item between pages is skipped entirely.

### Keyset (cursor) pagination

We order by `(created_at DESC, id DESC)`.  The `id` column breaks ties when
two products share an identical timestamp—which is common in bulk inserts.

**Cursor encoding**

The cursor is a base64url-encoded JSON object containing the `created_at`
timestamp and `id` of the last product on the current page:

```
{"ts": "2024-06-15T08:23:11+00:00", "id": 193847}
→ base64url → eyJ0cyI6ICIyMDI0LTA2LTE1VDA4OjIzOjExWiIsICJpZCI6IDE5Mzg0N30
```

The client treats this string as completely opaque.  The server decodes it
and constructs the WHERE clause:

```sql
WHERE (created_at < $cursor_ts)
   OR (created_at = $cursor_ts AND id < $cursor_id)
ORDER BY created_at DESC, id DESC
LIMIT $limit + 1          -- fetch one extra to detect has_more
```

**Correctness under concurrent inserts**

- A newly inserted product has `created_at = NOW()`, which is *newer* than
  the cursor anchor.
- It will **not** appear in the next-page query (the WHERE clause filters it
  out).
- It would appear on page 1 if the user refreshed, or on earlier pages—which
  is the expected behaviour.
- Products already seen on page 1 are anchored below the cursor and will
  **never** appear again.

This eliminates both duplicates and gaps regardless of how many rows are
inserted or updated concurrently.

**`has_more` detection**

Instead of a COUNT query, the repository fetches `limit + 1` rows.  If
the result set has more than `limit` items, the service sets `has_more = true`
and trims the extra row before returning.  This costs a single index scan
with no additional round-trips.

---

## Index Design

Two composite indexes are created at startup (and in the Alembic migration):

```sql
-- Unfiltered newest-first traversal
CREATE INDEX idx_products_created_at_id
ON products (created_at DESC, id DESC);

-- Category-filtered newest-first traversal
CREATE INDEX idx_products_category_created_at_id
ON products (category, created_at DESC, id DESC);
```

**Why DESC?**

PostgreSQL stores B-tree indexes in ascending order by default.  Defining the
index with `DESC` allows the query planner to perform a pure *backward
index scan* for `ORDER BY created_at DESC, id DESC` without any sort step.
This is critical for large tables: a forward index scan followed by a sort
would be O(n log n); a backward scan is O(k) where k is the page size.

**Why a composite index with `category` first?**

When a `category` filter is present, the query adds `WHERE category = $1`.
PostgreSQL can use the composite index
`(category, created_at DESC, id DESC)` to perform an equality filter on
`category` and then a range scan on `(created_at, id)` in a single
index operation.  Without this index, the engine would need a separate
bitmap heap scan plus a sort.

**Why `id` as tiebreaker?**

`created_at` has microsecond resolution, but bulk inserts can generate
thousands of rows per second with identical timestamps.  Adding `id` (an
auto-incrementing integer) as the secondary sort key guarantees a fully
deterministic order and a unique cursor position for every row.

---

## Design Trade-offs

| Decision | Trade-off |
|----------|-----------|
| Keyset over OFFSET | Correct under concurrent mutations; cannot jump to arbitrary page n |
| `BigInteger` id (not UUID) | Smaller index footprint, simpler cursor; not suitable for distributed write paths without a sequence server |
| `created_at` as sort key | Immutable once inserted, so cursors remain valid indefinitely; product updates do not change pagination position |
| `limit + 1` trick for `has_more` | Avoids a COUNT query; slight over-fetch of one row |
| Auto-create tables on startup | Simple for demos and Docker; Alembic migration preferred for production schema management |
| CORS `allow_origins=["*"]` | Suitable for development; restrict to known origins in production |

---

## Testing

### Prerequisites

Create the test database:

```bash
createdb codevector_test
# or via psql:
psql -c "CREATE DATABASE codevector_test;" postgres
```

### Running tests

```bash
cd backend
pytest -v
```

### Test coverage

| Test | What it verifies |
|------|-----------------|
| `test_empty_database` | Returns empty list gracefully |
| `test_default_limit` | 20 products returned by default |
| `test_custom_limit` | Respects `limit` parameter |
| `test_products_ordered_newest_first` | Descending timestamp order |
| `test_exact_page_size_no_has_more` | `has_more=false` when count equals limit |
| `test_fewer_than_limit_has_no_more` | `has_more=false` when fewer than limit rows |
| `test_category_filter` | Only matching category returned |
| `test_category_filter_nonexistent` | Empty result for missing category |
| `test_cursor_pagination_no_duplicates` | Zero duplicates across all pages |
| `test_cursor_pagination_ordered` | Global sort order maintained across pages |
| `test_cursor_pagination_covers_all_rows` | All rows reachable via cursor traversal |
| `test_cursor_pagination_with_category` | Category + cursor combination |
| `test_new_inserts_do_not_cause_duplicates` | Concurrent insert stability |
| `test_invalid_cursor_returns_400` | Tampered cursor rejected |
| `test_limit_zero_returns_422` | Validation catches `limit=0` |
| `test_limit_too_large_returns_422` | Validation catches `limit=101` |
| `test_negative_limit_returns_422` | Validation catches `limit=-1` |
| `test_product_schema` | Response shape contains all required fields |
| `test_cursor_is_opaque_string` | Cursor is base64, not a raw integer |

---

## Future Improvements

- **Search**: Full-text search on `name` using PostgreSQL `tsvector` + GIN index.
- **Dedicated `/categories` endpoint**: Eliminate the client-side inference hack in the frontend.
- **Cursor expiry**: Sign cursors with a HMAC to detect tampering; optionally add a TTL.
- **Rate limiting**: Per-IP throttling via a Redis token bucket.
- **Observability**: Prometheus metrics (`/metrics`) for p50/p95 query latency, cursor decode failures, and error rates.
- **Read replicas**: Route `GET /products` to a read replica for horizontal read scaling.
- **Connection pooling**: Use PgBouncer or RDS Proxy in front of PostgreSQL for very high concurrency.
- **Partial index**: `WHERE category = 'Electronics'` partial indexes if certain categories dominate query volume.
