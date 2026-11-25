import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.role import Role


class EmployeeRole(Base):
    __tablename__ = "employee_roles"

    __table_args__ = (
        Index("ix_employee_roles_role_id", "role_id"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        primary_key=True,
    )

    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.role_id", ondelete="CASCADE"),
        primary_key=True,
    )

    employee: Mapped["Employee"] = relationship(
        back_populates="employee_role_assignments",
        foreign_keys=[employee_id],
    )

    role: Mapped["Role"] = relationship(
        back_populates="employee_role_assignments",
        foreign_keys=[role_id],
    )
