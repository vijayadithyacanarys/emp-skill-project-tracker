"""finalize employee project allocations

Revision ID: f3a7b9c2d641
Revises: e8f4a2c9b731
Create Date: 2026-11-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a7b9c2d641"
down_revision: Union[str, Sequence[str], None] = "e8f4a2c9b731"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "check_allocation_percentage_range",
        "employee_project_allocations",
        type_="check"
    )
    op.drop_constraint(
        "check_allocation_date_range",
        "employee_project_allocations",
        type_="check"
    )
    op.alter_column(
        "employee_project_allocations",
        "start_date",
        existing_type=sa.Date(),
        nullable=False
    )
    op.alter_column(
        "employee_project_allocations",
        "end_date",
        existing_type=sa.Date(),
        nullable=False
    )
    op.create_check_constraint(
        "check_allocation_percentage_range",
        "employee_project_allocations",
        sa.text("allocation_percentage > 0 AND allocation_percentage <= 100")
    )
    op.create_check_constraint(
        "check_allocation_date_range",
        "employee_project_allocations",
        sa.text("end_date >= start_date")
    )
    op.create_check_constraint(
        "check_allocation_status",
        "employee_project_allocations",
        sa.text("status IN ('planned', 'active', 'completed', 'cancelled')")
    )


def downgrade() -> None:
    op.drop_constraint(
        "check_allocation_status",
        "employee_project_allocations",
        type_="check"
    )
    op.drop_constraint(
        "check_allocation_date_range",
        "employee_project_allocations",
        type_="check"
    )
    op.drop_constraint(
        "check_allocation_percentage_range",
        "employee_project_allocations",
        type_="check"
    )
    op.alter_column(
        "employee_project_allocations",
        "start_date",
        existing_type=sa.Date(),
        nullable=True
    )
    op.alter_column(
        "employee_project_allocations",
        "end_date",
        existing_type=sa.Date(),
        nullable=True
    )
    op.create_check_constraint(
        "check_allocation_percentage_range",
        "employee_project_allocations",
        sa.text("allocation_percentage BETWEEN 0 AND 100")
    )
    op.create_check_constraint(
        "check_allocation_date_range",
        "employee_project_allocations",
        sa.text(
            "start_date IS NULL OR end_date IS NULL OR end_date >= start_date"
        )
    )
