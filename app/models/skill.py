from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.employee import Employee
    from app.models.employee_skill import EmployeeSkill
    from app.models.project_required_skill import ProjectRequiredSkill
    from app.models.skill import Skill



class Skill(Base):
    __tablename__ = "skills"

    skill_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    skill_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    employees: Mapped[list["EmployeeSkill"]] = relationship(
        back_populates="skill"
    )

    required_projects: Mapped[list["ProjectRequiredSkill"]] = relationship(
        back_populates="skill"
    )