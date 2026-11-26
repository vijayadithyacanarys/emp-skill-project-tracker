from datetime import datetime
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_compat import (
    ascii_string,
    current_timestamp_expression,
    unicode_string,
)
from app.models.employee import Employee


class EmployeeCredential(Base):
    __tablename__ = "emp_credentials"

    __table_args__ = (
        CheckConstraint(
            "DATALENGTH(emp_email) = DATALENGTH(RTRIM(emp_email))",
            name="check_emp_credentials_email_no_trailing_spaces",
        ).ddl_if(dialect="mssql"),
    )

    emp_email: Mapped[str] = mapped_column(
        unicode_string(150),
        ForeignKey(
            "employees.email",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        primary_key=True,
    )

    password_hash: Mapped[str] = mapped_column(
        ascii_string(255),
        nullable=False,
    )

    credential_version: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        default=uuid.uuid4,
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

    employee: Mapped[Employee] = relationship(
        back_populates="credential",
    )
