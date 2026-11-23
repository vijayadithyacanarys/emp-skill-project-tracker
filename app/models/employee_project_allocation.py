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
            "allocation_percentage BETWEEN 0 AND 100",
            name="check_allocation_percentage_range"
        ),
        CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR end_date >= start_date",
            name="check_allocation_date_range"
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
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
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
