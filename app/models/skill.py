from sqlalchemy import Computed, UniqueConstraint
from sqlalchemy.dialects import mssql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, engine
from app.db_compat import unicode_string

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.employee import Employee
    from app.models.employee_skill import EmployeeSkill
    from app.models.project_required_skill import ProjectRequiredSkill
    from app.models.skill import Skill



class Skill(Base):
    __tablename__ = "skills"

    if engine.dialect.name == "mssql":
        __table_args__ = (
            UniqueConstraint(
                "skill_name_binary_key",
                "skill_name_data_length",
                name="uq_skills_skill_name_exact",
            ),
        )
    else:
        __table_args__ = (
            UniqueConstraint("skill_name").ddl_if(dialect="postgresql"),
        )

    skill_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    skill_name: Mapped[str] = mapped_column(
        unicode_string(100),
        nullable=False
    )

    if engine.dialect.name == "mssql":
        skill_name_binary_key: Mapped[bytes | None] = mapped_column(
            mssql.VARBINARY(length=200),
            Computed(
                "CONVERT(varbinary(200), skill_name)",
                persisted=True,
            ),
            nullable=True,
        )

        skill_name_data_length: Mapped[int | None] = mapped_column(
            mssql.INTEGER(),
            Computed("DATALENGTH(skill_name)", persisted=True),
            nullable=True,
        )

    description: Mapped[str | None] = mapped_column(
        unicode_string(500),
        nullable=True
    )

    employees: Mapped[list["EmployeeSkill"]] = relationship(
        back_populates="skill"
    )

    required_projects: Mapped[list["ProjectRequiredSkill"]] = relationship(
        back_populates="skill"
    )