"""backfill employee roles

Revision ID: b7c2d9e4f6a1
Revises: e2b4d791c6a5
Create Date: 2026-11-26

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b7c2d9e4f6a1"
down_revision: Union[str, Sequence[str], None] = "e2b4d791c6a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE
            invalid_count integer;
        BEGIN
            SELECT COUNT(*)
            INTO invalid_count
            FROM employees e
            LEFT JOIN roles r ON r.role_id = e.role_id
            WHERE e.role_id IS NOT NULL
              AND r.role_id IS NULL;

            IF invalid_count > 0 THEN
                RAISE EXCEPTION
                    'Cannot backfill employee_roles: % employee(s) reference missing role_id values',
                    invalid_count;
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        INSERT INTO employee_roles (employee_id, role_id)
        SELECT employee_id, role_id
        FROM employees
        WHERE role_id IS NOT NULL
        ON CONFLICT (employee_id, role_id) DO NOTHING
        """
    )


def downgrade() -> None:
    # The association table may also contain assignments added after the
    # backfill, so this data migration deliberately has no destructive undo.
    pass
