from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.skill import Skill


class ProjectRequiredSkill(Base):
    __tablename__ = "project_required_skills"

    __table_args__ = (
        CheckConstraint(
            "minimum_proficiency BETWEEN 1 AND 5",
            name="check_project_skill_minimum_proficiency"
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.project_id"),
        primary_key=True
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.skill_id"),
        primary_key=True
    )

    minimum_proficiency: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true()
    )

    project: Mapped["Project"] = relationship(
        back_populates="required_skills"
    )

    skill: Mapped["Skill"] = relationship(
        back_populates="required_projects"
    )
