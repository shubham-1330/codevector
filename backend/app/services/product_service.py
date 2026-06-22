"""
ProductService – business logic layer.

Responsibilities:
  - Decode the opaque cursor from the client.
  - Invoke the repository.
  - Detect whether a next page exists (limit + 1 trick).
  - Encode the next cursor from the last returned product.
  - Return a structured response object.
"""

import logging
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError, InvalidCursorError
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductListResponse, ProductResponse
from app.utils.cursor import decode_cursor, encode_cursor

logger = logging.getLogger("codevector.service")


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ProductRepository(session)

    async def get_products(
        self,
        *,
        limit: int,
        category: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> ProductListResponse:
        cursor_ts = None
        cursor_id = None

        if cursor is not None:
            cursor_ts, cursor_id = decode_cursor(cursor)
            logger.debug("Decoded cursor: ts=%s id=%d", cursor_ts, cursor_id)

        try:
            rows = await self._repo.list_products(
                limit=limit,
                category=category,
                cursor_ts=cursor_ts,
                cursor_id=cursor_id,
            )
        except SQLAlchemyError as exc:
            logger.exception("Database query failed: %s", exc)
            raise DatabaseError() from exc

        has_more = len(rows) > limit
        products: list[Product] = rows[:limit]

        next_cursor: Optional[str] = None
        if has_more and products:
            last = products[-1]
            next_cursor = encode_cursor(last.created_at, last.id)

        logger.debug(
            "get_products returned %d products has_more=%s",
            len(products),
            has_more,
        )

        return ProductListResponse(
            products=[ProductResponse.model_validate(p) for p in products],
            next_cursor=next_cursor,
            has_more=has_more,
        )
