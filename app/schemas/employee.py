from pydantic import BaseModel, ConfigDict, Field, EmailStr
from uuid import UUID
from typing import Literal


EmployeeStatus = Literal["active", "inactive"]


class EmployeeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    role_id: int
    experience_years: float = Field(default=0, ge=0)
    status: EmployeeStatus = "active"


class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    role_id: int | None = None
    experience_years: float | None = Field(default=None, ge=0)
    status: EmployeeStatus | None = None


class EmployeeResponse(BaseModel):
    employee_id: UUID
    name: str
    email: str
    experience_years: float

    model_config = ConfigDict(from_attributes=True)