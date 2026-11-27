from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AssignmentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    pass_percentage: int = Field(ge=0, le=100)
    is_active: bool = True

    model_config = ConfigDict(extra="forbid")

    @field_validator("title")
    @classmethod
    def reject_blank_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be empty")
        return value


class AssignmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    pass_percentage: int | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("title")
    @classmethod
    def reject_blank_title(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("title must not be empty")
        return value

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set:
            raise ValueError("At least one assignment field must be provided")

        for field in ("title", "pass_percentage", "is_active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")

        return self


class AssignmentResponse(BaseModel):
    assignment_id: UUID
    title: str
    description: str | None
    pass_percentage: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
