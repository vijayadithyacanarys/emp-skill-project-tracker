"""add credential version

Revision ID: c73a9f1e4b26
Revises: 8d1c5f3a6b27
Create Date: 2026-11-25

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = "c73a9f1e4b26"
down_revision: Union[str, Sequence[str], None] = "8d1c5f3a6b27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "emp_credentials",
        sa.Column("credential_version", sa.Uuid(as_uuid=True), nullable=True),
    )

    credentials = sa.table(
        "emp_credentials",
        sa.column("emp_email", sa.String(length=150)),
        sa.column("credential_version", sa.Uuid(as_uuid=True)),
    )
    connection = op.get_bind()
    employee_emails = connection.execute(
        sa.select(credentials.c.emp_email)
    ).scalars().all()

    for employee_email in employee_emails:
        connection.execute(
            sa.update(credentials)
            .where(credentials.c.emp_email == employee_email)
            .values(credential_version=uuid.uuid4())
        )

    op.alter_column(
        "emp_credentials",
        "credential_version",
        existing_type=sa.Uuid(as_uuid=True),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("emp_credentials", "credential_version")
