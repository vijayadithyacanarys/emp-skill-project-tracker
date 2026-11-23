"""add project and allocation tables

Revision ID: 9a3f1c7d2e41
Revises: c5dabb08b844
Create Date: 2026-11-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a3f1c7d2e41"
down_revision: Union[str, Sequence[str], None] = "c5dabb08b844"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("project_name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.PrimaryKeyConstraint("project_id")
    )
    op.create_table(
        "project_required_skills",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("minimum_proficiency", sa.Integer(), nullable=False),
        sa.Column(
            "is_mandatory",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False
        ),
        sa.CheckConstraint(
            "minimum_proficiency BETWEEN 1 AND 5",
            name="check_project_skill_minimum_proficiency"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.skill_id"]),
        sa.PrimaryKeyConstraint("project_id", "skill_id")
    )
    op.create_table(
        "employee_project_allocations",
        sa.Column("allocation_id", sa.Uuid(), nullable=False),
        sa.Column("employee_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("allocation_percentage", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("assigned_by", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.CheckConstraint(
            "allocation_percentage BETWEEN 0 AND 100",
            name="check_allocation_percentage_range"
        ),
        sa.CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR end_date >= start_date",
            name="check_allocation_date_range"
        ),
        sa.ForeignKeyConstraint(["assigned_by"], ["employees.employee_id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"]),
        sa.PrimaryKeyConstraint("allocation_id")
    )


def downgrade() -> None:
    op.drop_table("employee_project_allocations")
    op.drop_table("project_required_skills")
    op.drop_table("projects")
