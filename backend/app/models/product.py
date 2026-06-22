from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Numeric, String
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Product(Base):
    """
    Product model.

    Ordered by (created_at DESC, id DESC) for newest-first browsing.
    The primary key `id` serves as a stable tiebreaker when two products
    share the same `created_at` timestamp, which guarantees a deterministic
    cursor position across concurrent inserts.

    Indexes (created via migration / startup SQL):
      - idx_products_created_at_id       ON (created_at DESC, id DESC)
      - idx_products_category_created_at_id ON (category, created_at DESC, id DESC)
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<Product id={self.id} name={self.name!r} category={self.category!r}>"
        )
