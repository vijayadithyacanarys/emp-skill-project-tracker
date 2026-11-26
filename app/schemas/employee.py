from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from uuid import UUID
from typing import Literal

from app.db_compat import (
    is_mssql_database_configured,
    validate_email_whitespace,
)


EmployeeStatus = Literal["active", "inactive"]


class EmployeeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    role_id: int
    experience_years: float = Field(default=0, ge=0)
    status: EmployeeStatus = "active"

    @field_validator("email", mode="before")
    @classmethod
    def reject_mssql_email_whitespace(cls, value: object) -> object:
        if is_mssql_database_configured():
            validate_email_whitespace(value, "mssql")
        return value


class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    role_id: int | None = None
    experience_years: float | None = Field(default=None, ge=0)
    status: EmployeeStatus | None = None

    @field_validator("email", mode="before")
    @classmethod
    def reject_mssql_email_whitespace(cls, value: object) -> object:
        if is_mssql_database_configured():
            validate_email_whitespace(value, "mssql")
        return value


class EmployeeResponse(BaseModel):
    employee_id: UUID
    name: str
    email: str
    role_id: int
    experience_years: float
    status: EmployeeStatus

    model_config = ConfigDict(from_attributes=True)