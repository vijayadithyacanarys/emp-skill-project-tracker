"""add project date range constraint

Revision ID: d1e4c8b7a609
Revises: 9a3f1c7d2e41
Create Date: 2026-11-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d1e4c8b7a609"
down_revision: Union[str, Sequence[str], None] = "9a3f1c7d2e41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "check_project_date_range",
        "projects",
        sa.text(
            "start_date IS NULL OR end_date IS NULL OR end_date >= start_date"
        )
    )


def downgrade() -> None:
    op.drop_constraint(
        "check_project_date_range",
        "projects",
        type_="check"
    )
