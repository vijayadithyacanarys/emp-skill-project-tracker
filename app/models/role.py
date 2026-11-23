from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.employee import Employee

class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    role_name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    employees: Mapped[list["Employee"]] = relationship(
        back_populates="role"
    )