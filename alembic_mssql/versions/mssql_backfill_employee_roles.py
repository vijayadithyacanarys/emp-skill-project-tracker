"""backfill legacy employee roles for MSSQL

Revision ID: mssql_backfill_0002
Revises: mssql_initial_0001
Create Date: 2026-11-26

"""
from typing import Sequence, Union

from alembic import op


revision: str = "mssql_backfill_0002"
down_revision: Union[str, Sequence[str], None] = "mssql_initial_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DECLARE @invalid_count int;
        SELECT @invalid_count = COUNT(*)
        FROM employees e
        LEFT JOIN roles r ON r.role_id = e.role_id
        WHERE e.role_id IS NOT NULL
          AND r.role_id IS NULL;

        IF @invalid_count > 0
        BEGIN
            DECLARE @invalid_message nvarchar(500) =
                CONCAT(
                    'Cannot backfill employee_roles: ',
                    @invalid_count,
                    ' employee(s) reference missing role_id values'
                );
            THROW 50001, @invalid_message, 1;
        END;
        """
    )

    op.execute(
        """
        INSERT INTO employee_roles (employee_id, role_id)
        SELECT e.employee_id, e.role_id
        FROM employees e
        WHERE e.role_id IS NOT NULL
          AND EXISTS (
              SELECT 1
              FROM roles r
              WHERE r.role_id = e.role_id
          )
          AND NOT EXISTS (
              SELECT 1
              FROM employee_roles er
              WHERE er.employee_id = e.employee_id
                AND er.role_id = e.role_id
          );
        """
    )


def downgrade() -> None:
    # Preserve any associations added after the backfill.
    pass
