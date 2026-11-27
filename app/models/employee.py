import uuid
from decimal import Decimal

from sqlalchemy import (
    Integer,
    Numeric,
    ForeignKey,
    Uuid,
    CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_compat import exact_string_in, unicode_string

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.employee import Employee
    from app.models.employee_credential import EmployeeCredential
    from app.models.employee_role import EmployeeRole
    from app.models.employee_skill import EmployeeSkill
    from app.models.employee_project_allocation import EmployeeProjectAllocation
    from app.models.project_manager import ProjectManager
    from app.models.skill import Skill
    from app.models.employee_assignment import EmployeeAssignment


class Employee(Base):
    __tablename__ = "employees"

    __table_args__ = (
        CheckConstraint(
            "experience_years >= 0",
            name="check_experience_nonnegative"
        ),
        CheckConstraint(
            exact_string_in("status", ("active", "inactive")),
            name="check_employee_status"
        ),
        CheckConstraint(
            "DATALENGTH(email) = DATALENGTH(RTRIM(email))",
            name="check_employee_email_no_trailing_spaces",
        ).ddl_if(dialect="mssql"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        unicode_string(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        unicode_string(150),
        unique=True,
        nullable=False
    )

    experience_years: Mapped[Decimal] = mapped_column(
        Numeric(4, 1),
        nullable=False,
        default=0
    )

    status: Mapped[str] = mapped_column(
        unicode_string(20),
        nullable=False,
        default="active",
        server_default="active"
    )
    


    credential: Mapped["EmployeeCredential | None"] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    employee_role_assignments: Mapped[list["EmployeeRole"]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="EmployeeRole.employee_id",
    )

    project_manager_assignments: Mapped[list["ProjectManager"]] = relationship(
        back_populates="manager",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="ProjectManager.manager_id",
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

    employee_assignments: Mapped[list["EmployeeAssignment"]] = relationship(
        back_populates="employee",
        foreign_keys="EmployeeAssignment.employee_id",
    )

    assigned_employee_assignments: Mapped[list["EmployeeAssignment"]] = relationship(
        back_populates="assigner",
        foreign_keys="EmployeeAssignment.assigned_by",
    )