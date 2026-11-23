from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProjectRequiredSkillCreate(BaseModel):
    skill_id: int
    minimum_proficiency: int = Field(ge=1, le=5)
    is_mandatory: bool = True


class ProjectRequiredSkillUpdate(BaseModel):
    minimum_proficiency: int | None = Field(default=None, ge=1, le=5)
    is_mandatory: bool | None = None

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set:
            raise ValueError("At least one requirement field must be provided")

        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Requirement fields cannot be null")

        return self


class ProjectRequiredSkillResponse(BaseModel):
    project_id: UUID
    skill_id: int
    minimum_proficiency: int
    is_mandatory: bool

    model_config = ConfigDict(from_attributes=True)
