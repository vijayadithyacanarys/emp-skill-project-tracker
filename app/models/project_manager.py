import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.project import Project


class ProjectManager(Base):
    __tablename__ = "project_managers"

    __table_args__ = (
        Index("ix_project_managers_manager_id", "manager_id"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        primary_key=True,
    )

    manager_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        primary_key=True,
    )

    project: Mapped["Project"] = relationship(
        back_populates="project_manager_assignments",
        foreign_keys=[project_id],
    )

    manager: Mapped["Employee"] = relationship(
        back_populates="project_manager_assignments",
        foreign_keys=[manager_id],
    )
