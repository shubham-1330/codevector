<div align="center">

# CodeVector — Product Browsing API

**A production-grade backend that solves the hardest problem in pagination:**  
_browsing a live dataset that changes while you scroll._

![Python](https://img.shields.io/badge/Python-3.12-3776ab?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat-square&logo=next.js&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ed?style=flat-square&logo=docker&logoColor=white)

</div>

---

## The Problem

Most product APIs use **OFFSET pagination**:

```sql
SELECT * FROM products ORDER BY created_at DESC LIMIT 20 OFFSET 40;
```

This breaks the moment your data changes. Here's why:

```
User loads Page 1  →  [Product A, B, C, D, E ... T]   (items 1–20)

Meanwhile: 3 new products are inserted at the top

User loads Page 2  →  OFFSET 20 skips items 18, 19, 20 from Page 1
                       Products B, C, D appear AGAIN  ← duplicate
                       Products 21, 22, 23 are SKIPPED ← gap
```

On a live e-commerce platform inserting thousands of products per hour, this means users see duplicate listings and silently miss products. OFFSET pagination also gets slower as the table grows — scanning and discarding 100,000 rows to show page 5,001 is expensive.

---

## The Solution

**Cursor-based (keyset) pagination** anchors each page to the last item you saw, not a row count.

```
User loads Page 1  →  last item has (created_at=2024-06-15, id=193847)
                       cursor = base64url encode of that position

Meanwhile: 3 new products inserted — doesn't matter

User loads Page 2  →  WHERE (created_at < '2024-06-15' OR
                             (created_at = '2024-06-15' AND id < 193847))
                       ORDER BY created_at DESC, id DESC
                       LIMIT 20

Result: exactly the next 20 items after the cursor. No duplicates. No gaps.
        New products appear on page 1 if the user refreshes — as expected.
```

The cursor is encoded as an **opaque base64 string** — clients treat it as a black box and just pass it back. The server decodes it, uses it as a WHERE clause anchor, and returns the next page.

---

## Features

- **200,000 products** seeded with realistic fake data
- **Newest-first ordering** with deterministic tiebreaking on `id`
- **Category filtering** combined with cursor pagination
- **Zero duplicates** or skipped products across pages, even during concurrent inserts
- **`limit+1` trick** — detects next page existence without a COUNT query
- **Composite DESC indexes** — PostgreSQL backward index scan, O(k) per page not O(n)
- **Structured JSON logging** for all requests, queries, and errors
- **Centralized error handling** with typed application exceptions
- **20 automated tests** covering pagination correctness, concurrent inserts, and error cases
- **Next.js frontend** with category filter and "Load More" button

---

## Tech Stack

| Layer           | Technology                      |
| --------------- | ------------------------------- |
| API Framework   | FastAPI 0.111                   |
| ORM             | SQLAlchemy 2.x (async)          |
| Database Driver | asyncpg                         |
| Database        | PostgreSQL 16                   |
| Validation      | Pydantic v2                     |
| Server          | Uvicorn                         |
| Migrations      | Alembic                         |
| Seed Data       | Faker                           |
| Testing         | pytest + pytest-asyncio + httpx |
| Frontend        | Next.js 14 + Tailwind CSS       |
| Container       | Docker + Docker Compose         |

---

## Project Structure

```
codevector/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies.py          # FastAPI dependency injection
│   │   │   └── routes/
│   │   │       └── products.py          # GET /products endpoint
│   │   ├── core/
│   │   │   ├── config.py                # Environment-driven settings
│   │   │   ├── exceptions.py            # Domain errors + HTTP handlers
│   │   │   └── logging.py               # Structured stdout logging
│   │   ├── db/
│   │   │   ├── base.py                  # SQLAlchemy declarative base
│   │   │   └── session.py               # Async engine + session factory
│   │   ├── models/
│   │   │   └── product.py               # Product ORM model
│   │   ├── repositories/
│   │   │   └── product_repository.py    # Keyset pagination SQL query
│   │   ├── schemas/
│   │   │   └── product.py               # Pydantic request/response models
│   │   ├── services/
│   │   │   └── product_service.py       # Business logic, cursor handling
│   │   ├── utils/
│   │   │   └── cursor.py                # Base64url cursor encode/decode
│   │   └── main.py                      # App factory, middleware, startup
│   ├── alembic/                         # Database migrations
│   │   └── versions/
│   │       └── 001_initial_schema.py    # Products table + indexes + trigger
│   ├── seed/
│   │   └── seed.py                      # Bulk-inserts 200,000 products
│   ├── tests/
│   │   ├── conftest.py                  # Fixtures, test DB, HTTP client
│   │   └── test_products.py             # 20 API + pagination tests
│   ├── Dockerfile
│   ├── docker-compose.yml               # Backend + DB only
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example
│
├── frontend/
│   └── src/
│       ├── app/
│       │   └── page.tsx                 # Product grid with Load More
│       ├── components/
│       │   ├── CategoryFilter.tsx       # Category chip buttons
│       │   └── ProductCard.tsx          # Individual product card
│       └── lib/
│           └── api.ts                   # Typed API client
│
└── docker-compose.yml                   # Full stack (backend + frontend + DB)
```

**Request flow through the backend:**

```
HTTP Request
    ↓
FastAPI Route Handler          ← validates query params via Pydantic
    ↓
ProductService                 ← decodes cursor, applies limit+1 trick
    ↓
ProductRepository              ← executes keyset SQL query
    ↓
PostgreSQL (index scan)        ← no sequential scans, no sorts
    ↓
ProductService                 ← encodes next cursor from last row
    ↓
Pydantic serialization → JSON Response
```

---

## Quick Start — Docker (Recommended)

The fastest way to run everything with a single command.

**Prerequisites:** Docker Desktop installed and running.

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd codevector

# 2. Start all services (PostgreSQL + backend API + frontend UI)
docker compose up --build -d

# 3. Seed the database with 200,000 products
docker compose exec backend python -m seed.seed

# 4. Open in browser
#    API docs  →  http://localhost:8000/docs
#    Frontend  →  http://localhost:3000
```

To stop everything:

```bash
docker compose down
```

To wipe the database and start fresh:

```bash
docker compose down -v   # -v removes the postgres volume
docker compose up -d
docker compose exec backend python -m seed.seed
```

---

## Running Locally (Without Docker)

**Prerequisites:** Python 3.12+, Node.js 18+, PostgreSQL 14+ running locally.

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set DATABASE_URL to your local PostgreSQL
# e.g. postgresql+asyncpg://postgres:password@localhost:5432/codevector

# Start the API (auto-creates tables and indexes on first run)
uvicorn app.main:app --reload
```

API is now at **http://localhost:8000** — visit `/docs` for the interactive playground.

### Seed the database

```bash
# Still in backend/ with venv active
python -m seed.seed
```

This inserts 200,000 products in batches of 5,000. Takes about 60–90 seconds. The script is rerunnable — existing rows are left in place.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Default points to http://localhost:8000 — change if your backend is elsewhere

# Start dev server
npm run dev
```

Frontend is at **http://localhost:3000**.

---

## Environment Variables

Create `backend/.env` from `backend/.env.example`:

| Variable             | Default                                                            | Description                                   |
| -------------------- | ------------------------------------------------------------------ | --------------------------------------------- |
| `DATABASE_URL`       | `postgresql+asyncpg://postgres:password@localhost:5432/codevector` | Async PostgreSQL connection string            |
| `TEST_DATABASE_URL`  | `…/codevector_test`                                                | Separate database used by pytest              |
| `DEBUG`              | `false`                                                            | Enables SQL query logging                     |
| `LOG_LEVEL`          | `INFO`                                                             | Python log level (`DEBUG`, `INFO`, `WARNING`) |
| `MAX_PAGE_LIMIT`     | `100`                                                              | Maximum value for the `limit` query param     |
| `DEFAULT_PAGE_LIMIT` | `20`                                                               | Page size when `limit` is not provided        |
| `POSTGRES_USER`      | `postgres`                                                         | Docker Compose PostgreSQL user                |
| `POSTGRES_PASSWORD`  | `password`                                                         | Docker Compose PostgreSQL password            |
| `POSTGRES_DB`        | `codevector`                                                       | Docker Compose PostgreSQL database name       |

---

## API Reference

### `GET /products`

Returns products ordered newest-first. Supports filtering and cursor pagination.

**Query Parameters**

| Parameter  | Type    | Default | Constraints | Description                             |
| ---------- | ------- | ------- | ----------- | --------------------------------------- |
| `limit`    | integer | `20`    | 1 – 100     | Number of products to return            |
| `category` | string  | —       | 1–100 chars | Filter by category (case-sensitive)     |
| `cursor`   | string  | —       | —           | Opaque token from the previous response |

**Response Body**

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
  "next_cursor": "eyJ0cyI6IjIwMjQtMDYtMTVUMDg6MjM6MTFaIiwiaWQiOjE5Mzg0N30",
  "has_more": true
}
```

When `has_more` is `false`, `next_cursor` is `null` and you have reached the last page.

**Paginating through all results**

```bash
# Page 1
curl "http://localhost:8000/products?limit=20"

# Page 2 — pass next_cursor from the page 1 response
curl "http://localhost:8000/products?limit=20&cursor=eyJ0c..."

# With category filter
curl "http://localhost:8000/products?limit=20&category=Electronics"
curl "http://localhost:8000/products?limit=20&category=Electronics&cursor=eyJ0c..."
```

**Error Responses**

| Status | When                                        |
| ------ | ------------------------------------------- |
| `400`  | Cursor is malformed or tampered with        |
| `422`  | `limit` is 0, negative, or greater than 100 |
| `503`  | PostgreSQL is unreachable                   |

### `GET /health`

```bash
curl http://localhost:8000/health
# {"status": "ok", "service": "CodeVector Product API"}
```

---

## How Pagination Works — Deep Dive

### The cursor

The cursor encodes the position of the **last item on the current page** as a base64url string:

```
Last product: created_at = "2024-06-15T08:23:11Z", id = 193847

JSON payload:  {"ts":"2024-06-15T08:23:11+00:00","id":193847}
base64url:     eyJ0cyI6IjIwMjQtMDYtMTVUMDg6MjM6MTFaIiwiaWQiOjE5Mzg0N30
```

The client never interprets this string — it just passes it back verbatim. The server decodes it on the next request.

### The query

```sql
-- Without cursor (first page)
SELECT * FROM products
ORDER BY created_at DESC, id DESC
LIMIT 21;  -- fetch limit+1 to detect has_more

-- With cursor (subsequent pages)
SELECT * FROM products
WHERE (created_at < '2024-06-15T08:23:11Z')
   OR (created_at = '2024-06-15T08:23:11Z' AND id < 193847)
ORDER BY created_at DESC, id DESC
LIMIT 21;
```

The `id` column breaks ties when two products share an identical timestamp — common during bulk inserts.

### Detecting `has_more` without COUNT

Instead of a separate `SELECT COUNT(*)` query, the repository fetches `limit + 1` rows:

- Got **21 rows** when limit is 20 → `has_more = true`, return first 20, encode cursor from row 20
- Got **≤ 20 rows** → `has_more = false`, return all rows, `next_cursor = null`

One query, no extra round-trip.

### Why concurrent inserts don't break it

```
Timeline:

  t=0   User loads page 1 (cursor anchored at product #193847)
  t=1   5 new products inserted with created_at = NOW() (newer than anchor)
  t=2   User requests page 2 using the cursor

Page 2 query: WHERE created_at < '2024-06-15...' OR (same ts AND id < 193847)

The 5 new products have created_at > cursor timestamp → filtered OUT of page 2
Products 193848 onward appear correctly → no duplicates, no gaps
```

New products would appear on page 1 if the user refreshed — exactly the expected behaviour for "newest first".

---

## Database Index Design

```sql
-- Unfiltered newest-first traversal
CREATE INDEX idx_products_created_at_id
ON products (created_at DESC, id DESC);

-- Category-filtered newest-first traversal
CREATE INDEX idx_products_category_created_at_id
ON products (category, created_at DESC, id DESC);
```

**Why DESC indexes?** PostgreSQL stores B-tree indexes in ascending order. Declaring `DESC` lets the query planner do a **backward index scan** for `ORDER BY created_at DESC, id DESC` — no sort step needed. On 200,000 rows, this is the difference between reading 20 rows and reading 200,000.

**Why `category` first in the composite index?** When filtering by category, PostgreSQL performs an equality check on `category` and then a range scan on `(created_at, id)` — all within a single index, no separate heap scan or sort.

**Why `id` as tiebreaker?** Bulk inserts generate many rows with identical `created_at` timestamps. Without `id`, the sort order is non-deterministic and the cursor loses its uniqueness guarantee. With `id`, every row has a unique, stable position.

---

## Running Tests

**Prerequisites:** PostgreSQL running locally with a `codevector_test` database.

```bash
# Create the test database (one-time setup)
createdb codevector_test

# Run all tests
cd backend
pytest -v
```

Expected output:

```
tests/test_products.py::test_health_check                          PASSED
tests/test_products.py::test_empty_database                        PASSED
tests/test_products.py::test_default_limit                         PASSED
tests/test_products.py::test_custom_limit                          PASSED
tests/test_products.py::test_products_ordered_newest_first         PASSED
tests/test_products.py::test_exact_page_size_no_has_more           PASSED
tests/test_products.py::test_fewer_than_limit_has_no_more          PASSED
tests/test_products.py::test_category_filter                       PASSED
tests/test_products.py::test_category_filter_nonexistent           PASSED
tests/test_products.py::test_cursor_pagination_no_duplicates       PASSED
tests/test_products.py::test_cursor_pagination_ordered             PASSED
tests/test_products.py::test_cursor_pagination_covers_all_rows     PASSED
tests/test_products.py::test_cursor_pagination_with_category       PASSED
tests/test_products.py::test_new_inserts_do_not_cause_duplicates   PASSED  ← key test
tests/test_products.py::test_invalid_cursor_returns_400            PASSED
tests/test_products.py::test_limit_zero_returns_422                PASSED
tests/test_products.py::test_limit_too_large_returns_422           PASSED
tests/test_products.py::test_negative_limit_returns_422            PASSED
tests/test_products.py::test_product_schema                        PASSED
tests/test_products.py::test_cursor_is_opaque_string               PASSED

20 passed in 2.34s
```

The test `test_new_inserts_do_not_cause_duplicates` specifically validates the core guarantee: anchor page 1, insert 5 newer products, fetch page 2, assert zero overlap.

---

## Database Migrations

The app auto-creates tables and indexes on startup (suitable for development and Docker). For production, use Alembic to manage schema changes safely:

```bash
cd backend

# Apply all pending migrations
alembic upgrade head

# Check current migration state
alembic current

# Roll back one migration
alembic downgrade -1

# Auto-generate a migration after changing a model
alembic revision --autogenerate -m "add product description column"
```

The migration at `alembic/versions/001_initial_schema.py` creates the table, both composite indexes, and a PostgreSQL trigger that automatically updates `updated_at` on every row update.

---

## Design Decisions & Trade-offs

| Decision                   | Reasoning                                                     | Trade-off                                                          |
| -------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------ |
| Keyset over OFFSET         | Correct under concurrent mutations                            | Cannot jump to arbitrary page N                                    |
| `BigInteger` PK (not UUID) | Smaller index, simpler cursor, sequential access pattern      | Not suitable for distributed writes without a centralized sequence |
| `created_at` as sort key   | Immutable after insert — cursors stay valid forever           | Product updates don't change pagination order                      |
| `limit+1` for `has_more`   | Avoids a COUNT query on every request                         | Fetches one extra row per page                                     |
| Async SQLAlchemy + asyncpg | Non-blocking I/O, higher throughput under concurrent requests | Slightly more complex test setup                                   |
| `create_all` on startup    | Zero-config developer experience                              | Alembic preferred in production for controlled schema evolution    |

---

## Future Improvements

- **`GET /categories`** endpoint — currently the frontend infers categories from the first page of data
- **Full-text search** on `name` using PostgreSQL `tsvector` + GIN index
- **Cursor signing** — HMAC signature on the cursor to detect tampering (currently only base64-validated)
- **Rate limiting** — per-IP token bucket via Redis
- **Prometheus metrics** — p50/p95 query latency, error rates, cursor decode failures
- **Read replicas** — route `GET /products` to a replica for horizontal read scaling
- **Connection pooler** — PgBouncer or RDS Proxy for very high concurrency workloads
