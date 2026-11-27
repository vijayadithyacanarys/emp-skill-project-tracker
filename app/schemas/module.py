from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ModuleCreate(BaseModel):
    skill_id: int
    module_name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    content: str | None = None
    is_active: bool = True

    model_config = ConfigDict(extra="forbid")

    @field_validator("module_name")
    @classmethod
    def reject_blank_module_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("module_name must not be empty")
        return value


class ModuleUpdate(BaseModel):
    skill_id: int | None = None
    module_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    description: str | None = Field(default=None, max_length=500)
    content: str | None = None
    is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("module_name")
    @classmethod
    def reject_blank_module_name(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("module_name must not be empty")
        return value

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set:
            raise ValueError("At least one module field must be provided")

        for field in ("skill_id", "module_name", "is_active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")

        return self


class ModuleResponse(BaseModel):
    module_id: UUID
    skill_id: int
    module_name: str
    description: str | None
    content: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
