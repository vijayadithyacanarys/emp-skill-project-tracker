import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.permission import Permission
    from app.models.role import Role


class RolePermission(Base):
    __tablename__ = "role_permissions"

    __table_args__ = (
        Index("ix_role_permissions_permission_id", "permission_id"),
    )

    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.role_id", ondelete="CASCADE"),
        primary_key=True,
    )

    permission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("permissions.permission_id", ondelete="CASCADE"),
        primary_key=True,
    )

    role: Mapped["Role"] = relationship(
        back_populates="role_permission_assignments",
        foreign_keys=[role_id],
    )

    permission: Mapped["Permission"] = relationship(
        back_populates="role_permission_assignments",
        foreign_keys=[permission_id],
    )
