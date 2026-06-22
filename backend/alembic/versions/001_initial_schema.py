"""Initial schema – products table with keyset-pagination indexes.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Unfiltered newest-first keyset pagination
    # Query pattern: ORDER BY created_at DESC, id DESC
    op.execute(
        """
        CREATE INDEX idx_products_created_at_id
        ON products (created_at DESC, id DESC)
        """
    )

    # Category-filtered newest-first keyset pagination
    # Query pattern: WHERE category = $1 ORDER BY created_at DESC, id DESC
    op.execute(
        """
        CREATE INDEX idx_products_category_created_at_id
        ON products (category, created_at DESC, id DESC)
        """
    )

    # Trigger function to auto-update updated_at on every row update
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_products_updated_at
        BEFORE UPDATE ON products
        FOR EACH ROW
        EXECUTE FUNCTION fn_set_updated_at()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_products_updated_at ON products")
    op.execute("DROP FUNCTION IF EXISTS fn_set_updated_at")
    op.drop_table("products")
