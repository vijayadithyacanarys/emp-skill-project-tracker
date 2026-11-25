"""add RBAC association tables

Revision ID: e2b4d791c6a5
Revises: c73a9f1e4b26
Create Date: 2026-11-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e2b4d791c6a5"
down_revision: Union[str, Sequence[str], None] = "c73a9f1e4b26"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("permission_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.CheckConstraint(
            "name ~ '^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$'",
            name="check_permission_name_format",
        ),
        sa.PrimaryKeyConstraint("permission_id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "employee_roles",
        sa.Column("employee_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.employee_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.role_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("employee_id", "role_id"),
    )
    op.create_index(
        "ix_employee_roles_role_id",
        "employee_roles",
        ["role_id"],
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.permission_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.role_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )
    op.create_index(
        "ix_role_permissions_permission_id",
        "role_permissions",
        ["permission_id"],
    )
    op.create_table(
        "project_managers",
        sa.Column("project_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("manager_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["manager_id"],
            ["employees.employee_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.project_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("project_id", "manager_id"),
    )
    op.create_index(
        "ix_project_managers_manager_id",
        "project_managers",
        ["manager_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_project_managers_manager_id", table_name="project_managers")
    op.drop_table("project_managers")
    op.drop_index(
        "ix_role_permissions_permission_id",
        table_name="role_permissions",
    )
    op.drop_table("role_permissions")
    op.drop_index("ix_employee_roles_role_id", table_name="employee_roles")
    op.drop_table("employee_roles")
    op.drop_table("permissions")
