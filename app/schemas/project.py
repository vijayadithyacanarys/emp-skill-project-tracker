from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProjectFields(BaseModel):
    project_name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def validate_date_range(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be on or after start_date")
        return self


class ProjectCreate(ProjectFields):
    pass


class ProjectUpdate(ProjectFields):
    project_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200
    )
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(
        default=None,
        min_length=1,
        max_length=30
    )

    @model_validator(mode="after")
    def validate_non_nullable_fields(self):
        if "project_name" in self.model_fields_set and self.project_name is None:
            raise ValueError("project_name cannot be null")
        if "status" in self.model_fields_set and self.status is None:
            raise ValueError("status cannot be null")
        return self


class ProjectResponse(BaseModel):
    project_id: UUID
    project_name: str
    description: str | None
    start_date: date | None
    end_date: date | None
    status: str

    model_config = ConfigDict(from_attributes=True)


class ProjectManagerAssignmentCreate(BaseModel):
    manager_id: UUID


class ProjectManagerResponse(BaseModel):
    employee_id: UUID
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)
