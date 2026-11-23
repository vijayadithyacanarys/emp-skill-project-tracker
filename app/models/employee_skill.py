import uuid
from decimal import Decimal

from sqlalchemy import (
    Integer,
    Numeric,
    Boolean,
    ForeignKey,
    CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"

    __table_args__ = (
        CheckConstraint(
            "proficiency_level BETWEEN 1 AND 5",
            name="check_proficiency_level"
        ),
        CheckConstraint(
            "years_of_experience >= 0",
            name="check_skill_experience"
        ),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.employee_id"),
        primary_key=True
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.skill_id"),
        primary_key=True
    )

    proficiency_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    years_of_experience: Mapped[Decimal] = mapped_column(
        Numeric(4, 1),
        nullable=False,
        default=0
    )

    verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    employee = relationship(
        "Employee",
        back_populates="skills"
    )

    skill = relationship(
        "Skill",
        back_populates="employees"
    )