import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_product_service
from app.core.config import settings
from app.schemas.product import ProductListResponse
from app.services.product_service import ProductService

logger = logging.getLogger("codevector.routes.products")

router = APIRouter()


@router.get(
    "",
    response_model=ProductListResponse,
    summary="List products",
    description=(
        "Returns products ordered newest-first with cursor-based pagination. "
        "Pass the `next_cursor` from one response as the `cursor` parameter "
        "in the next request to advance through pages without duplicates."
    ),
)
async def list_products(
    service: Annotated[ProductService, Depends(get_product_service)],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=settings.MAX_PAGE_LIMIT,
            description="Products per page (1-100).",
        ),
    ] = settings.DEFAULT_PAGE_LIMIT,
    category: Annotated[
        Optional[str],
        Query(min_length=1, max_length=100, description="Filter by category name."),
    ] = None,
    cursor: Annotated[
        Optional[str],
        Query(description="Opaque pagination cursor from the previous response."),
    ] = None,
) -> ProductListResponse:
    logger.info(
        "GET /products limit=%d category=%r cursor=%r",
        limit,
        category,
        cursor[:8] + "..." if cursor else None,
    )
    return await service.get_products(
        limit=limit,
        category=category,
        cursor=cursor,
    )
