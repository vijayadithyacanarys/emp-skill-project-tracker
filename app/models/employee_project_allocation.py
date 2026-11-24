import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    Uuid
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.project import Project


class EmployeeProjectAllocation(Base):
    __tablename__ = "employee_project_allocations"

    __table_args__ = (
        CheckConstraint(
            "allocation_percentage >0  AND allocation_percentage <= 100",
            name="check_allocation_percentage_range"
        ),
        CheckConstraint(
            "end_date >= start_date",
            name="check_allocation_date_range"
        ),
        CheckConstraint(
            "status IN ('planned', 'active', 'completed', 'cancelled')",
            name="check_allocation_status"
        ),
    )

    allocation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.employee_id"),
        nullable=False
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.project_id"),
        nullable=False
    )

    allocation_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False
    )

    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("employees.employee_id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default = "planned"
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    employee: Mapped["Employee"] = relationship(
        back_populates="project_allocations",
        foreign_keys=[employee_id]
    )

    project: Mapped["Project"] = relationship(
        back_populates="allocations"
    )

    assigner: Mapped["Employee | None"] = relationship(
        back_populates="assigned_project_allocations",
        foreign_keys=[assigned_by]
    )
