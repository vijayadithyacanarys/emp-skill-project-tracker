"""add employee credentials

Revision ID: 8d1c5f3a6b27
Revises: 05a1b40fcf5d
Create Date: 2026-11-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8d1c5f3a6b27"
down_revision: Union[str, Sequence[str], None] = "05a1b40fcf5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "emp_credentials",
        sa.Column("emp_email", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["emp_email"],
            ["employees.email"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.PrimaryKeyConstraint("emp_email"),
    )


def downgrade() -> None:
    op.drop_table("emp_credentials")
