import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Uuid, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_compat import current_timestamp_expression, unicode_string, unicode_text

from app.models.skill import Skill

class Module(Base):
    __tablename__ = "modules"

    module_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.skill_id"),
        nullable=False,
        unique=True,
    )

    module_name: Mapped[str] = mapped_column(
        unicode_string(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        unicode_string(500),
        nullable=True,
    )

    content: Mapped[str | None] = mapped_column(
        unicode_text(),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=current_timestamp_expression(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=current_timestamp_expression(),
        onupdate=current_timestamp_expression(),
    )

    skill : Mapped["Skill"] = relationship(
        back_populates="module"
    )