from pydantic import BaseModel, ConfigDict, Field, EmailStr
from uuid import UUID


class EmployeeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    role_id: int
    experience_years: float = Field(default=0, ge=0)


class EmployeeUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    role_id: int
    experience_years: float = Field(ge=0)


class EmployeeResponse(BaseModel):
    employee_id: UUID
    name: str
    email: str
    role_id: int
    experience_years: float
    status: str

    model_config = ConfigDict(from_attributes=True)