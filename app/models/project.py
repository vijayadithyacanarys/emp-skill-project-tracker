import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_compat import date_type, unicode_string, unicode_text

if TYPE_CHECKING:
    from app.models.employee_project_allocation import EmployeeProjectAllocation
    from app.models.project_manager import ProjectManager
    from app.models.project_required_skill import ProjectRequiredSkill


class Project(Base):
    __tablename__ = "projects"

    __table_args__ = (
        CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR end_date >= start_date",
            name="check_project_date_range"
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    project_name: Mapped[str] = mapped_column(
        unicode_string(200),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        unicode_text(),
        nullable=True
    )

    start_date: Mapped[date | None] = mapped_column(
        date_type(),
        nullable=True
    )

    end_date: Mapped[date | None] = mapped_column(
        date_type(),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        unicode_string(30),
        nullable=False
    )

    required_skills: Mapped[list["ProjectRequiredSkill"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )

    allocations: Mapped[list["EmployeeProjectAllocation"]] = relationship(
        back_populates="project"
    )

    project_manager_assignments: Mapped[list["ProjectManager"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="ProjectManager.project_id",
    )
