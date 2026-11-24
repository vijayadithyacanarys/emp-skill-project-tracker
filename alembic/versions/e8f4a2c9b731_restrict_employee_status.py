"""restrict employee status

Revision ID: e8f4a2c9b731
Revises: d1e4c8b7a609
Create Date: 2026-11-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8f4a2c9b731"
down_revision: Union[str, Sequence[str], None] = "d1e4c8b7a609"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE employees SET status = 'inactive' "
        "WHERE status IS NULL OR status NOT IN ('active', 'inactive')"
    )
    op.alter_column(
        "employees",
        "status",
        existing_type=sa.String(length=20),
        nullable=False,
        server_default=sa.text("'active'")
    )
    op.create_check_constraint(
        "check_employee_status",
        "employees",
        sa.text("status IN ('active', 'inactive')")
    )


def downgrade() -> None:
    op.drop_constraint(
        "check_employee_status",
        "employees",
        type_="check"
    )
    op.alter_column(
        "employees",
        "status",
        existing_type=sa.String(length=20),
        nullable=False,
        server_default=None
    )
