import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    Uuid,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_compat import current_timestamp_expression, unicode_string

if TYPE_CHECKING:
    from app.models.assignment_question import AssignmentQuestion
    from app.models.employee_assignment import EmployeeAssignment


class Assignment(Base):
    __tablename__ = "assignments"

    __table_args__ = (
        CheckConstraint(
            "pass_percentage BETWEEN 0 AND 100",
            name="check_assignment_pass_percentage",
        ),
    )

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        unicode_string(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        unicode_string(500),
        nullable=True,
    )

    pass_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=current_timestamp_expression(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=current_timestamp_expression(),
        onupdate=current_timestamp_expression(),
    )

    questions: Mapped[list["AssignmentQuestion"]] = relationship(
        back_populates="assignment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    employee_assignments: Mapped[list["EmployeeAssignment"]] = relationship(
        back_populates="assignment",
    )
