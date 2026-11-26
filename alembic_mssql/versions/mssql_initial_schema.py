"""Create the current application schema for Microsoft SQL Server.

Revision ID: mssql_initial_0001
Revises:
Create Date: 2026-11-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql


revision: str = "mssql_initial_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = ("mssql",)
depends_on: Union[str, Sequence[str], None] = None

MSSQL_TEXT_COLLATION = "Latin1_General_100_CS_AS_SC"


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column(
            "role_name",
            mssql.NVARCHAR(length=50, collation=MSSQL_TEXT_COLLATION),
            nullable=False,
        ),
        sa.Column(
            "role_name_binary_key",
            mssql.VARBINARY(length=100),
            sa.Computed("CONVERT(varbinary(100), role_name)", persisted=True),
            nullable=True,
        ),
        sa.Column(
            "role_name_data_length",
            mssql.INTEGER(),
            sa.Computed("DATALENGTH(role_name)", persisted=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("role_id"),
        sa.UniqueConstraint(
            "role_name_binary_key",
            "role_name_data_length",
            name="uq_roles_role_name_exact",
        ),
    )
    op.create_table(
        "skills",
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column(
            "skill_name",
            mssql.NVARCHAR(length=100, collation=MSSQL_TEXT_COLLATION),
            nullable=False,
        ),
        sa.Column(
            "skill_name_binary_key",
            mssql.VARBINARY(length=200),
            sa.Computed("CONVERT(varbinary(200), skill_name)", persisted=True),
            nullable=True,
        ),
        sa.Column(
            "skill_name_data_length",
            mssql.INTEGER(),
            sa.Computed("DATALENGTH(skill_name)", persisted=True),
            nullable=True,
        ),
        sa.Column(
            "description",
            mssql.NVARCHAR(length=500, collation=MSSQL_TEXT_COLLATION),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("skill_id"),
        sa.UniqueConstraint(
            "skill_name_binary_key",
            "skill_name_data_length",
            name="uq_skills_skill_name_exact",
        ),
    )
    op.create_table(
        "projects",
        sa.Column("project_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "project_name",
            mssql.NVARCHAR(length=200, collation=MSSQL_TEXT_COLLATION),
            nullable=False,
        ),
        sa.Column(
            "description",
            mssql.NVARCHAR(length=None, collation=MSSQL_TEXT_COLLATION),
            nullable=True,
        ),
        sa.Column("start_date", mssql.DATE(), nullable=True),
        sa.Column("end_date", mssql.DATE(), nullable=True),
        sa.Column(
            "status",
            mssql.NVARCHAR(length=30, collation=MSSQL_TEXT_COLLATION),
            nullable=False,
        ),
        sa.CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR end_date >= start_date",
            name="check_project_date_range",
        ),
        sa.PrimaryKeyConstraint("project_id"),
    )
    op.create_table(
        "employees",
        sa.Column("employee_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "name",
            mssql.NVARCHAR(length=100, collation=MSSQL_TEXT_COLLATION),
            nullable=False,
        ),
        sa.Column(
            "email",
            mssql.NVARCHAR(length=150, collation=MSSQL_TEXT_COLLATION),
            nullable=False,
        ),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("experience_years", sa.Numeric(precision=4, scale=1), nullable=False),
        sa.Column(
            "status",
            mssql.NVARCHAR(length=20, collation=MSSQL_TEXT_COLLATION),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "experience_years >= 0",
            name="check_experience_nonnegative",
        ),
        sa.CheckConstraint(
            "((status COLLATE Latin1_General_100_BIN2) "
            "IN (N'active', N'inactive') "
            "AND DATALENGTH(status) = DATALENGTH(RTRIM(status)))",
            name="check_employee_status",
        ),
        sa.CheckConstraint(
            "DATALENGTH(email) = DATALENGTH(RTRIM(email))",
            name="check_employee_email_no_trailing_spaces",
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"]),
        sa.PrimaryKeyConstraint("employee_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "permissions",
        sa.Column("permission_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "name",
            mssql.NVARCHAR(length=100, collation=MSSQL_TEXT_COLLATION),
            nullable=False,
        ),
        sa.Column(
            "description",
            mssql.NVARCHAR(length=500, collation=MSSQL_TEXT_COLLATION),
            nullable=True,
        ),
        sa.CheckConstraint(
            "((name COLLATE Latin1_General_100_BIN2) LIKE '[a-z]%:[a-z]%' "
            "AND PATINDEX('%[^a-z0-9_:]%', "
            "(name COLLATE Latin1_General_100_BIN2)) = 0 "
            "AND LEN(name) - LEN(REPLACE(name, ':', '')) = 1)",
            name="check_permission_name_format",
        ),
        sa.PrimaryKeyConstraint("permission_id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "emp_credentials",
        sa.Column(
            "emp_email",
            mssql.NVARCHAR(length=150, collation=MSSQL_TEXT_COLLATION),
            nullable=False,
        ),
        sa.Column(
            "password_hash",
            mssql.VARCHAR(length=255, collation=MSSQL_TEXT_COLLATION),
            nullable=False,
        ),
        sa.Column("credential_version", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("SYSDATETIMEOFFSET()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("SYSDATETIMEOFFSET()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["emp_email"],
            ["employees.email"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.PrimaryKeyConstraint("emp_email"),
        sa.CheckConstraint(
            "DATALENGTH(emp_email) = DATALENGTH(RTRIM(emp_email))",
            name="check_emp_credentials_email_no_trailing_spaces",
        ),
    )
    op.create_table(
        "employee_skills",
        sa.Column("employee_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("proficiency_level", sa.Integer(), nullable=False),
        sa.Column(
            "years_of_experience",
            sa.Numeric(precision=4, scale=1),
            nullable=False,
        ),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "proficiency_level BETWEEN 1 AND 5",
            name="check_proficiency_level",
        ),
        sa.CheckConstraint(
            "years_of_experience >= 0",
            name="check_skill_experience",
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.skill_id"]),
        sa.PrimaryKeyConstraint("employee_id", "skill_id"),
    )
    op.create_table(
        "employee_project_allocations",
        sa.Column("allocation_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("employee_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "allocation_percentage",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
        ),
        sa.Column("assigned_by", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            mssql.NVARCHAR(length=30, collation=MSSQL_TEXT_COLLATION),
            server_default=sa.text("'planned'"),
            nullable=False,
        ),
        sa.Column("start_date", mssql.DATE(), nullable=False),
        sa.Column("end_date", mssql.DATE(), nullable=False),
        sa.CheckConstraint(
            "allocation_percentage >0  AND allocation_percentage <= 100",
            name="check_allocation_percentage_range",
        ),
        sa.CheckConstraint(
            "end_date >= start_date",
            name="check_allocation_date_range",
        ),
        sa.CheckConstraint(
            "((status COLLATE Latin1_General_100_BIN2) "
            "IN (N'planned', N'active', N'completed', N'cancelled') "
            "AND DATALENGTH(status) = DATALENGTH(RTRIM(status)))",
            name="check_allocation_status",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.employee_id"],
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.project_id"],
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by"],
            ["employees.employee_id"],
        ),
        sa.PrimaryKeyConstraint("allocation_id"),
    )
    op.create_table(
        "project_required_skills",
        sa.Column("project_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("minimum_proficiency", sa.Integer(), nullable=False),
        sa.Column(
            "is_mandatory",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "minimum_proficiency BETWEEN 1 AND 5",
            name="check_project_skill_minimum_proficiency",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.skill_id"]),
        sa.PrimaryKeyConstraint("project_id", "skill_id"),
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
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.role_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.permission_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )
    op.create_table(
        "project_managers",
        sa.Column("project_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("manager_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.project_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["manager_id"],
            ["employees.employee_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("project_id", "manager_id"),
    )

    op.create_index(
        "ix_employee_roles_role_id",
        "employee_roles",
        ["role_id"],
    )
    op.create_index(
        "ix_role_permissions_permission_id",
        "role_permissions",
        ["permission_id"],
    )
    op.create_index(
        "ix_project_managers_manager_id",
        "project_managers",
        ["manager_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_project_managers_manager_id",
        table_name="project_managers",
    )
    op.drop_table("project_managers")
    op.drop_index(
        "ix_role_permissions_permission_id",
        table_name="role_permissions",
    )
    op.drop_table("role_permissions")
    op.drop_index(
        "ix_employee_roles_role_id",
        table_name="employee_roles",
    )
    op.drop_table("employee_roles")
    op.drop_table("project_required_skills")
    op.drop_table("employee_project_allocations")
    op.drop_table("employee_skills")
    op.drop_table("emp_credentials")
    op.drop_table("permissions")
    op.drop_table("employees")
    op.drop_table("projects")
    op.drop_table("skills")
    op.drop_table("roles")
