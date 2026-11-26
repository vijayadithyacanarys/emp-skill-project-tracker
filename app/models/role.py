from sqlalchemy import Computed, Integer, UniqueConstraint
from sqlalchemy.dialects import mssql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, engine
from app.db_compat import unicode_string
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.employee_role import EmployeeRole
    from app.models.permission import Permission
    from app.models.role_permission import RolePermission

class Role(Base):
    __tablename__ = "roles"

    if engine.dialect.name == "mssql":
        __table_args__ = (
            UniqueConstraint(
                "role_name_binary_key",
                "role_name_data_length",
                name="uq_roles_role_name_exact",
            ),
        )
    else:
        __table_args__ = (
            UniqueConstraint("role_name").ddl_if(dialect="postgresql"),
        )

    role_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    role_name: Mapped[str] = mapped_column(
        unicode_string(50),
        nullable=False
    )

    if engine.dialect.name == "mssql":
        role_name_binary_key: Mapped[bytes | None] = mapped_column(
            mssql.VARBINARY(length=100),
            Computed(
                "CONVERT(varbinary(100), role_name)",
                persisted=True,
            ),
            nullable=True,
        )

        role_name_data_length: Mapped[int | None] = mapped_column(
            mssql.INTEGER(),
            Computed("DATALENGTH(role_name)", persisted=True),
            nullable=True,
        )

    employees: Mapped[list["Employee"]] = relationship(
        back_populates="role"
    )

    employee_role_assignments: Mapped[list["EmployeeRole"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="EmployeeRole.role_id",
    )

    role_permission_assignments: Mapped[list["RolePermission"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="RolePermission.role_id",
    )