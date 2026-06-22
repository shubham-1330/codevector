from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductResponse(BaseModel):
    """Serialized product returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    price: Decimal = Field(decimal_places=2)
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    """Paginated product list response."""

    products: list[ProductResponse]
    next_cursor: Optional[str] = Field(
        default=None,
        description=(
            "Opaque base64 token. Pass as `cursor` to fetch the next page. "
            "Null when there are no more results."
        ),
    )
    has_more: bool = Field(
        description="True when there is at least one more page of results."
    )


class ProductQueryParams(BaseModel):
    """Validated query parameters for GET /products."""

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of products to return (1-100).",
    )
    category: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Filter products by category (case-sensitive).",
    )
    cursor: Optional[str] = Field(
        default=None,
        description="Opaque pagination cursor returned by the previous page.",
    )
