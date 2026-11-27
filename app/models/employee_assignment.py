import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_compat import (
    current_timestamp_expression,
    exact_string_in,
    unicode_string,
)

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.employee import Employee


class EmployeeAssignment(Base):
    __tablename__ = "employee_assignments"

    __table_args__ = (
        CheckConstraint(
            exact_string_in("status", ("assigned", "submitted")),
            name="check_employee_assignment_status",
        ),
        CheckConstraint(
            "score IS NULL OR score BETWEEN 0 AND 100",
            name="check_employee_assignment_score_range",
        ),
        CheckConstraint(
            exact_string_in("result", ("passed", "failed")),
            name="check_employee_assignment_result",
        ),
        Index(
            "uq_employee_assignments_employee_assignment",
            "employee_id",
            "assignment_id",
            unique=True,
        ),
        Index(
            "ix_employee_assignments_assignment_id",
            "assignment_id",
        ),
        Index(
            "ix_employee_assignments_assigned_by",
            "assigned_by",
        ),
    )

    employee_assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.employee_id"),
        nullable=False,
    )

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assignments.assignment_id"),
        nullable=False,
    )

    assigned_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.employee_id"),
        nullable=False,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=current_timestamp_expression(),
    )

    status: Mapped[str] = mapped_column(
        unicode_string(20),
        default="assigned",
        server_default=text("'assigned'"),
        nullable=False,
    )

    score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    result: Mapped[str | None] = mapped_column(
        unicode_string(20),
        nullable=True,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    employee: Mapped["Employee"] = relationship(
        back_populates="employee_assignments",
        foreign_keys=[employee_id],
    )

    assigner: Mapped["Employee"] = relationship(
        back_populates="assigned_employee_assignments",
        foreign_keys=[assigned_by],
    )

    assignment: Mapped["Assignment"] = relationship(
        back_populates="employee_assignments",
    )
