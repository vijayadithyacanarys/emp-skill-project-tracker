from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class EmployeeSkillCreate(BaseModel):
    skill_id: int

    proficiency_level: int = Field(
        ge=1,
        le=5
    )

    years_of_experience: float = Field(
        ge=0
    )

    verified: bool = False


class EmployeeSkillResponse(BaseModel):
    employee_id: UUID
    skill_id: int
    skill_name: str
    proficiency_level: int
    years_of_experience: float
    verified: bool

    model_config = ConfigDict(from_attributes=True)

class EmployeeSkillUpdate(BaseModel):
    proficiency_level: int = Field(ge=1, le=5)

    years_of_experience: float = Field(ge=0)

    verified: bool