import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Uuid, column
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import FunctionElement

from app.database import Base
from app.db_compat import unicode_string


class _PermissionNameFormat(FunctionElement[bool]):
    type = Boolean()
    inherit_cache = True


@compiles(_PermissionNameFormat)
def _compile_permission_name_format(element, compiler, **kwargs):
    name = compiler.process(element.clauses.clauses[0], **kwargs)
    return f"{name} ~ '^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$'"


@compiles(_PermissionNameFormat, "mssql")
def _compile_permission_name_format_mssql(element, compiler, **kwargs):
    name = compiler.process(element.clauses.clauses[0], **kwargs)
    binary_name = f"({name} COLLATE Latin1_General_100_BIN2)"
    return (
        f"({binary_name} LIKE '[a-z]%:[a-z]%' "
        f"AND PATINDEX('%[^a-z0-9_:]%', {binary_name}) = 0 "
        f"AND LEN({name}) - LEN(REPLACE({name}, ':', '')) = 1)"
    )


if TYPE_CHECKING:
    from app.models.role_permission import RolePermission


class Permission(Base):
    __tablename__ = "permissions"

    __table_args__ = (
        CheckConstraint(
            _PermissionNameFormat(column("name")),
            name="check_permission_name_format",
        ),
    )

    permission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        unicode_string(100),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        unicode_string(500),
        nullable=True,
    )

    role_permission_assignments: Mapped[list["RolePermission"]] = relationship(
        back_populates="permission",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="RolePermission.permission_id",
    )
