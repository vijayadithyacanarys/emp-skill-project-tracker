import uuid
from decimal import Decimal

from sqlalchemy import (
    String,
    Integer,
    Numeric,
    ForeignKey,
    Uuid,
    CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.employee import Employee
    from app.models.employee_skill import EmployeeSkill
    from app.models.employee_project_allocation import EmployeeProjectAllocation
    from app.models.skill import Skill


class Employee(Base):
    __tablename__ = "employees"

    __table_args__ = (
        CheckConstraint(
            "experience_years >= 0",
            name="check_experience_nonnegative"
        ),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.role_id"),
        nullable=False
    )

    experience_years: Mapped[Decimal] = mapped_column(
        Numeric(4, 1),
        nullable=False,
        default=0
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active"
    )
    

    role: Mapped["Role"] = relationship(
        back_populates="employees"
    )

    skills: Mapped[list["EmployeeSkill"]] = relationship(
    back_populates="employee",
    cascade="all, delete-orphan"
)

    project_allocations: Mapped[list["EmployeeProjectAllocation"]] = relationship(
        back_populates="employee",
        foreign_keys="EmployeeProjectAllocation.employee_id"
    )

    assigned_project_allocations: Mapped[list["EmployeeProjectAllocation"]] = relationship(
        back_populates="assigner",
        foreign_keys="EmployeeProjectAllocation.assigned_by"
    )