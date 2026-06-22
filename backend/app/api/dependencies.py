from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.product_service import ProductService


async def get_product_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProductService:
    return ProductService(session)
