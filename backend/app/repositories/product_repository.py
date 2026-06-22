"""
ProductRepository – pure database access layer.

All business logic lives in the service layer; this module only
translates Python objects into SQL and back.

Keyset pagination strategy
--------------------------
We order products by (created_at DESC, id DESC). The `id` column
acts as a stable tiebreaker when two products share the same timestamp.

Given a cursor representing position (cursor_ts, cursor_id), the next page
is the set of rows where:

    created_at < cursor_ts
    OR (created_at = cursor_ts AND id < cursor_id)

This is equivalent to the row-value comparison
    (created_at, id) < (cursor_ts, cursor_id)
in descending order, and maps directly to the composite index used by the
query planner.  No OFFSET is involved, so the result is stable even when
rows are inserted or updated concurrently.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product

logger = logging.getLogger("codevector.repository")


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_products(
        self,
        *,
        limit: int,
        category: Optional[str] = None,
        cursor_ts: Optional[datetime] = None,
        cursor_id: Optional[int] = None,
    ) -> list[Product]:
        """
        Return up to `limit + 1` products ordered newest-first.

        Requesting one extra row lets the service layer detect whether a
        next page exists without executing a separate COUNT query.
        """
        stmt = select(Product)

        if category is not None:
            stmt = stmt.where(Product.category == category)

        if cursor_ts is not None and cursor_id is not None:
            stmt = stmt.where(
                or_(
                    Product.created_at < cursor_ts,
                    and_(
                        Product.created_at == cursor_ts,
                        Product.id < cursor_id,
                    ),
                )
            )

        stmt = (
            stmt.order_by(Product.created_at.desc(), Product.id.desc())
            .limit(limit + 1)
        )

        logger.debug(
            "list_products limit=%d category=%r cursor=(%s, %s)",
            limit,
            category,
            cursor_ts,
            cursor_id,
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())
